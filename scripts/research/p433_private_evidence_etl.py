#!/usr/bin/env python3
"""P4.33 deterministic offline private research ETL (HN + publisher RSS).

No network, no article scraping, no sales inference, no public writes.
Only structural normalization, provenance, exact-URL deduplication, quarantine
and optional comparison against a prior *private* report.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import ipaddress
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from p430_company_evidence_review import load_identities
from p432_publisher_rss_probe import safe_post_link

MAX_INPUT_BYTES = 300_000
MAX_RECORDS = 40
BLOCKED = ("acquire.com", "flippa.com", "microns.io", "empireflippers.com")
EXCLUDED = ("localhost", "local", "internal", "onion", "test", "invalid")
DISCUSSION = re.compile(r"https://news\.ycombinator\.com/item\?id=[1-9][0-9]{0,15}\Z")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def read_json(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_INPUT_BYTES:
        raise ValueError("Empty or over-budget private research input")
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("Invalid private report root")
    return document


def safe_external_url(value: object) -> tuple[str | None, str | None]:
    """No requests ever follow this URL. Restricted marketplaces are discarded."""
    if value is None:
        return None, None
    if not isinstance(value, str) or len(value) > 1200 or CONTROL.search(value) or "\\" in value:
        return None, "UNSAFE_EXTERNAL_URL"
    try:
        p = urlsplit(value)
        h = (p.hostname or "").lower()
        if p.scheme != "https" or not h or p.username or p.password or p.port not in (None, 443):
            return None, "UNSAFE_EXTERNAL_URL"
        if any(h == x or h.endswith("." + x) for x in BLOCKED):
            return None, "RESTRICTED_MARKETPLACE_LINK"
        if (h in EXCLUDED or h.endswith(tuple("." + x for x in EXCLUDED))
                or h.isdecimal() or len(h) > 253
                or not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", h)):
            return None, "UNSAFE_EXTERNAL_URL"
        try:
            ipaddress.ip_address(h)
            return None, "UNSAFE_EXTERNAL_URL"
        except ValueError:
            pass
        if any(x in p.path for x in ("/../", "/./")):
            return None, "UNSAFE_EXTERNAL_URL"
        # Strip fragments and query tracking instead of storing user tokens.
        path = p.path or "/"
        return urlunsplit(("https", h, path, "", "")), None
    except ValueError:
        return None, "UNSAFE_EXTERNAL_URL"


def clean_title(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    title = " ".join(html.unescape(value).split())
    if not 5 <= len(title) <= 200 or CONTROL.search(title):
        return None
    return title


def published_day(raw: object, day: date) -> str | None:
    if not isinstance(raw, str) or not 5 <= len(raw) <= 45:
        return None
    try:
        if "T" in raw:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return None
            parsed = dt.astimezone(timezone.utc).date()
        else:
            parsed = date.fromisoformat(raw)
        if date(2000, 1, 1) <= parsed <= day + timedelta(days=1):
            return parsed.isoformat()
    except ValueError:
        pass
    return None


def load_hn(document: dict, identities: dict, day: date) -> tuple[list[dict], list[dict], dict]:
    if (document.get("contract") != "P4.26_PRIVATE_RESEARCH_LEADS_V1"
            or document.get("publication_allowed") is not False
            or document.get("marketplaces_listing_crawled") is not False
            or document.get("network_requests_max") != 7
            or document.get("source_scope") != "PUBLIC_SEARCH_INDEX_ONLY"):
        raise ValueError("Untrusted HN discovery report")
    if document.get("mode") not in ("READ_ONLY_ONLINE", "OFFLINE_DRY_RUN"):
        raise ValueError("Unexpected HN collection mode")
    companies = document.get("candidates")
    fresh = document.get("unmatched_new_project_leads")
    if (not isinstance(companies, list) or len(companies) > 6
            or not isinstance(fresh, list) or len(fresh) > 3
            or document.get("candidate_count") != len(companies)):
        raise ValueError("Unbounded company or fresh discovery input")
    records, rejected = [], []
    errors = 0
    for row in companies + [{"slug": None, "stories": fresh, "name": None}]:
        if not isinstance(row, dict):
            raise ValueError("Invalid candidate format")
        slug = row.get("slug")
        if slug is not None and slug not in identities:
            raise ValueError("Unknown company identity in HN lead")
        expected = identities[slug]["brand"] if slug else None
        if slug and row.get("name") != expected:
            raise ValueError("Changed company brand in lead report")
        if slug and row.get("error"):
            errors += 1
        stories = row.get("stories")
        if not isinstance(stories, list) or len(stories) > 3:
            raise ValueError("Excess search records")
        for hit in stories:
            if (not isinstance(hit, dict) or hit.get("status") != "UNVERIFIED_DISCOVERY_LEAD"
                    or hit.get("financial_evidence") is not False
                    or hit.get("source_kind") != "HN_SEARCH_INDEX_METADATA_ONLY"):
                raise ValueError("Untrusted or elevated HN hit")
            discussion = hit.get("discussion_url")
            if not isinstance(discussion, str) or not DISCUSSION.fullmatch(discussion):
                rejected.append({"channel": "HN", "reason": "INVALID_DISCUSSION_ID"})
                continue
            title = clean_title(hit.get("headline"))
            external, issue = safe_external_url(hit.get("external_url"))
            if issue == "RESTRICTED_MARKETPLACE_LINK":
                rejected.append({"channel": "HN", "reason": issue})
                continue
            if not title:
                rejected.append({"channel": "HN", "reason": "INVALID_TITLE"})
                continue
            if issue:
                rejected.append({"channel": "HN", "reason": issue})
            # A search match is NOT an attributed company claim, even if title mentions brand.
            hint = "UNASSIGNED_DISCOVERY_TOPIC"
            if expected:
                pattern = r"(?<![a-z0-9])" + re.escape(expected) + r"(?![a-z0-9])"
                hint = ("AMBIGUOUS_SHORT_BRAND" if len(expected) < 5
                        else "TITLE_BRAND_TOKEN_PRESENT_NOT_VERIFIED" if re.search(pattern, title, re.I)
                        else "SEARCH_ONLY_NO_TITLE_IDENTITY")
            records.append({
                "channel": "HN_PUBLIC_INDEX", "case_id": slug,
                "title": title, "canonical_url": external or discussion,
                "reference_url": discussion, "published_on": published_day(hit.get("published_at"), day),
                "identity_hint": hint,
            })
    return records, rejected, {
        "mode": document["mode"],
        "reported_candidate_errors": errors,
        "successful_requests_confirmed": False,  # P4.26 reports no per-request HTTP receipts.
    }


def load_rss(document: dict, identities: dict, day: date) -> tuple[list[dict], list[dict], dict]:
    if (document.get("contract") != "P432_PRIVATE_RSS_LEADS_V1"
            or document.get("eligible_for_publication") is not False
            or document.get("financial_claims_verified") != 0
            or document.get("source_fulltext_stored") is not False
            or document.get("source_url") != "https://usefathom.com/blog/feed.xml"
            or document.get("mode") not in ("LIVE_RSS_HTTP", "OFFLINE_FIXTURE_NOT_LIVE")):
        raise ValueError("Untrusted RSS report")
    rows = document.get("records")
    if not isinstance(rows, list) or len(rows) > 10 or document.get("records_count") != len(rows):
        raise ValueError("Unbounded RSS input")
    if document.get("network_requests") != (1 if document["mode"] == "LIVE_RSS_HTTP" else 0):
        raise ValueError("Inconsistent RSS request count")
    if identities["fathom"]["brand"] != "Fathom Analytics":
        raise ValueError("Fathom identity drift")
    accepted, rejected = [], []
    for item in rows:
        if (not isinstance(item, dict) or item.get("company_id") != "fathom"
                or item.get("candidate_company") != "Fathom Analytics"
                or item.get("source_kind") != "FIRST_PARTY_RSS_METADATA_ONLY"
                or item.get("eligible_for_publication") is not False
                or item.get("financial_evidence_verified") is not False
                or item.get("review_status") != "UNVERIFIED_DISCOVERY_LEAD"):
            raise ValueError("RSS entry claims unverified identity or financial proof")
        title = clean_title(item.get("title"))
        link = safe_post_link(item.get("source_url"))
        if not title or not link:
            rejected.append({"channel": "FATHOM_RSS", "reason": "INVALID_PUBLISHER_ITEM"})
            continue
        accepted.append({
            "channel": "OFFICIAL_PUBLISHER_RSS", "case_id": "fathom",
            "title": title, "canonical_url": link, "reference_url": link,
            "published_on": published_day(item.get("published_on"), day),
            "identity_hint": "PUBLISHER_RSS_BRAND_MATCH_NOT_FINANCIAL_PROOF",
        })
    return accepted, rejected, {"mode": document["mode"], "rss_item_count": len(rows)}


def clean_pipeline(hn: dict | None, rss: dict | None, previous: dict | None = None,
                   today: date | None = None) -> dict:
    day = today or datetime.now(timezone.utc).date()
    if hn is None and rss is None:
        raise ValueError("Provide a private source report")
    identities = load_identities()
    raw, rejected, source_health = [], [], {}
    for source_id, loader, obj in (("HN", load_hn, hn), ("RSS", load_rss, rss)):
        if obj is not None:
            rows, drops, health = loader(obj, identities, day)
            raw.extend(rows)
            rejected.extend(drops)
            source_health[source_id] = health
    if len(raw) > MAX_RECORDS:
        raise ValueError("Unbounded ETL intake")
    dedup: dict[str, dict] = {}
    for row in raw:
        key = hashlib.sha256(row["canonical_url"].encode("utf-8")).hexdigest()
        if key not in dedup:
            dedup[key] = {
                "fingerprint": key, "title": row["title"],
                "canonical_url": row["canonical_url"],
                "published_on": row["published_on"],
                "channels": [], "reference_urls": [],
                "searched_case_ids": [], "identity_hints": [],
                "status": "NEEDS_ORIGINAL_SOURCE_REVIEW",
                "company_identity_verified": False,
                "financial_evidence_verified": False,
                "eligible_for_publication": False,
            }
        group = dedup[key]
        if row["channel"] not in group["channels"]:
            group["channels"].append(row["channel"])
        if row["reference_url"] not in group["reference_urls"]:
            group["reference_urls"].append(row["reference_url"])
        if row["case_id"] and row["case_id"] not in group["searched_case_ids"]:
            group["searched_case_ids"].append(row["case_id"])
        if row["identity_hint"] not in group["identity_hints"]:
            group["identity_hints"].append(row["identity_hint"])
        if not group["published_on"] and row["published_on"]:
            group["published_on"] = row["published_on"]
    prior_hashes = set()
    if previous is not None:
        if (previous.get("contract") != "P433_PRIVATE_CLEAN_REVIEW_V1"
                or previous.get("publication_allowed") is not False):
            raise ValueError("Prior report is not a private P4.33 review")
        old_rows = previous.get("records")
        if not isinstance(old_rows, list) or len(old_rows) > 100:
            raise ValueError("Unbounded prior report")
        for row in old_rows:
            key = row.get("fingerprint") if isinstance(row, dict) else None
            if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key):
                raise ValueError("Corrupt prior fingerprint")
            prior_hashes.add(key)
    records = sorted(dedup.values(), key=lambda r: r["fingerprint"])
    for row in records:
        row["novelty"] = "ALREADY_IN_PRIOR_PRIVATE_REPORT" if row["fingerprint"] in prior_hashes else "NEW_TO_PRIVATE_REVIEW"
        if len(row["searched_case_ids"]) > 1:
            row["identity_hints"].append("MULTIPLE_SEARCH_QUERIES_NOT_INDEPENDENT_CONFIRMATION")
    return {
        "contract": "P433_PRIVATE_CLEAN_REVIEW_V1",
        "run_date_utc": day.isoformat(),
        "mode": "OFFLINE_DETERMINISTIC_CLEANING",
        "source_health": source_health,
        "network_requests_added": 0,
        "raw_candidate_count": len(raw),
        "accepted_unique_count": len(records),
        "duplicate_reference_count": len(raw) - len(records),
        "new_to_private_review_count": sum(x["novelty"] == "NEW_TO_PRIVATE_REVIEW" for x in records),
        "rejection_count": len(rejected),
        "quarantine": rejected,
        "records": records,
        "financial_claims_verified": 0,
        "legal_entities_verified": 0,
        "publication_allowed": False,
        "notices": [
            "机器清洗 ≠ 公司经营审计；官网、检索标题、RSS 均不证明付费或盈利。",
            "搜索公司与标题出现品牌只代表候选匹配，不能自动升级 L3/L4。",
            "跨来源同一 URL 去重只是出处合并，不能构成两家独立来源。",
            "没有 prior 输入时，仅本批次去重，不能声称跨天增量检查完成。",
        ],
    }


def private_path(path: Path) -> Path:
    result = path.resolve()
    if result.is_relative_to(ROOT.resolve()):
        raise ValueError("Private outputs must be outside repository")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline clean private discovery leads; zero network")
    parser.add_argument("--hn", type=Path, help="Existing P4.26 private HN scan artifact")
    parser.add_argument("--rss", type=Path, help="Existing P4.32 private RSS artifact")
    parser.add_argument("--previous", type=Path, help="Optional previous P4.33 private clean report")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.hn and not args.rss:
        parser.error("Require --hn and/or --rss")
    output = private_path(args.output)
    report = clean_pipeline(
        read_json(args.hn) if args.hn else None,
        read_json(args.rss) if args.rss else None,
        read_json(args.previous) if args.previous else None,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PRIVATE_REVIEW_ONLY", "raw": report["raw_candidate_count"],
        "unique": report["accepted_unique_count"], "duplicates": report["duplicate_reference_count"],
        "rejections": report["rejection_count"], "published": 0, "additional_requests": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
