#!/usr/bin/env python3
"""P4.30 private, offline R2 evidence triage. NO network or public admission.

Consumes the already bounded HN lead artifact and/or separately supplied
permission-reviewed text snapshots. Structural hits remain NEEDS_REVIEW, never
L3/L4 and never written into public evidence config or web/dist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
IDENTITIES = ROOT / "config/p430_company_identity_registry.json"
MAX_ITEMS = 6
MAX_INPUT_BYTES = 131_072
MAX_TEXT_CHARS = 48_000
CURATED_INTERVIEW = {"carrd": "https://saasclub.io/podcast/carrd-aj-306/"}
SEC_CIK = {"nerdwallet": "1625278"}
BLOCKED_MARKETPLACES = (
    "acquire.com", "flippa.com", "microns.io", "empireflippers.com"
)
FINANCIAL_RE = re.compile(
    r"(?i)(?<![\w])"
    r"(?:"
    r"(?P<value1>\$\s*\d[\d,]*(?:\.\d+)?\s*[KMB]?)\s*(?P<metric1>MRR|ARR)"
    r"|(?P<metric2>MRR|ARR)\s*(?:of|at|is|:|=|approximately|about)?\s*(?P<value2>\$\s*\d[\d,]*(?:\.\d+)?\s*[KMB]?)"
    r")\b"
)
PAID_RE = re.compile(
    r"(?i)(?<!\d)(?P<count>\d[\d,]{1,12})\s*(?:\+|more than|over)?\s+"
    r"(?P<metric>paying (?:customers|subscribers)|paid (?:customers|subscribers|users))\b"
)


def host(value: str) -> str:
    if not isinstance(value, str) or len(value) > 1500 or any(ord(c) < 33 for c in value):
        raise ValueError("Unsafe URL")
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or parts.port not in (None, 443) or "\\" in value
            or "/../" in parts.path or "/./" in parts.path):
        raise ValueError("Only safe HTTPS source URLs")
    h = parts.hostname.lower().removeprefix("www.")
    if not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", h):
        raise ValueError("Non-public or ambiguous host")
    if h in ("localhost.local", "127.0.0.1") or h.endswith((".local", ".internal")):
        raise ValueError("Private-network host")
    return h


def load_identities(path: Path = IDENTITIES) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("version") != "P430_PRIVATE_IDENTITY_REVIEW_V1":
        raise ValueError("Unknown identity registry")
    rows = document.get("companies")
    if not isinstance(rows, list) or len(rows) != 20:
        raise ValueError("Expected 20 explicit private candidate identities")
    out = {}
    domains = set()
    for record in rows:
        slug = record.get("id")
        domain = record.get("official_domain")
        brand = record.get("brand")
        if (not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]{2,60}", slug)
                or not isinstance(brand, str) or not 2 <= len(brand) <= 80
                or not isinstance(domain, str) or host("https://" + domain + "/") != domain
                or slug in out or domain in domains
                or record.get("legal_entity_status") != "UNVERIFIED"
                or record.get("legal_entity") is not None):
            raise ValueError("Unsafe/duplicate or misleading entity mapping")
        domains.add(domain)
        out[slug] = record
    # Independently compare mapped source domains with existing editorial cases;
    # company brand/host is still NOT proof of a legal entity.
    editorial = {}
    for name in ("p413_public_project_library.json", "p415_public_case_growth.json"):
        data = json.loads((ROOT / "config" / name).read_text(encoding="utf-8"))
        for item in data["cases"]:
            editorial[item["id"]] = host(item["officialHomeUrl"])
    editorial.update({"easlo": "easlo.co", "louise": "authorlouiselennox.com"})
    if set(out) != set(editorial) or any(out[k]["official_domain"] != v for k, v in editorial.items()):
        raise ValueError("Editorial identity drift: fail closed")
    return out


def load_private_json(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Missing or oversized private input")
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("Invalid private input")
    return content


def classify_source(case_id: str, url: str, identity: dict) -> str:
    try:
        h = host(url)
    except (ValueError, TypeError):
        return "REJECT_UNSAFE_URL"
    if any(h == m or h.endswith("." + m) for m in BLOCKED_MARKETPLACES):
        return "REJECT_UNLICENSED_MARKETPLACE"
    if h == identity["official_domain"]:
        return "FIRST_PARTY_REVIEW_ONLY"
    if CURATED_INTERVIEW.get(case_id) == url:
        return "CURATED_INTERVIEW_REVIEW_ONLY"
    if h == "sec.gov" and case_id in SEC_CIK:
        path = urlsplit(url).path
        if re.fullmatch(r"/Archives/edgar/data/" + SEC_CIK[case_id] + r"/[0-9]+/[a-zA-Z0-9._-]+", path):
            return "REGULATORY_FILING_REVIEW_ONLY"
    return "REJECT_UNAPPROVED_SOURCE"


def extract_indicators(text: str, brand: str) -> list[dict]:
    """Literal metric spans only, without ARR extrapolation or currency inference."""
    signals = []
    for rx in (FINANCIAL_RE, PAID_RE):
        for match in rx.finditer(text):
            # An earlier paragraph mentioning the brand does not attribute a
            # later company's revenue to this brand. Match only one sentence.
            boundaries = ".!?;。！？；\n"
            left = max([text.rfind(ch, 0, match.start()) for ch in boundaries] + [-1]) + 1
            right_edges = [text.find(ch, match.end()) for ch in boundaries]
            right = min([i for i in right_edges if i >= 0] + [len(text)])
            vicinity = text[max(left, match.start()-220):min(right, match.end()+100)]
            if not re.search(r"(?i)(?<![a-z0-9])" + re.escape(brand) + r"(?![a-z0-9])", vicinity):
                continue
            if rx is FINANCIAL_RE:
                signals.append({
                    "metric": (match.group("metric1") or match.group("metric2")).upper(),
                    "literal": re.sub(r"\s+", " ", match.group(0)).strip(),
                    "currency": "DOLLAR_SYMBOL_UNRESOLVED",
                    "offset": match.start(),
                })
            else:
                signals.append({
                    "metric": "PAID_CUSTOMERS_OR_SUBSCRIBERS",
                    "literal": re.sub(r"\s+", " ", match.group(0)).strip(),
                    "currency": "NOT_APPLICABLE",
                    "offset": match.start(),
                })
            if len(signals) >= 8:
                return signals
    return signals


def process_snapshots(document: dict, identities: dict) -> list[dict]:
    if document.get("contract") != "P430_PRIVATE_SOURCE_SNAPSHOTS_V1":
        raise ValueError("Snapshots require the explicit private contract")
    items = document.get("items")
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ValueError("At most six private text snapshots per batch")
    reports = []
    for obj in items:
        if not isinstance(obj, dict):
            raise ValueError("Malformed source snapshot")
        slug = obj.get("case_id")
        if not isinstance(slug, str) or slug not in identities:
            reports.append({"case_id": str(slug)[:60], "status": "REJECT_UNKNOWN_IDENTITY", "indicators": []})
            continue
        expected = identities[slug]
        url = obj.get("source_url")
        policy = classify_source(slug, url, expected)
        brand = obj.get("asserted_brand")
        home = obj.get("asserted_home")
        try:
            actual_home_host = host(home)
        except (TypeError, ValueError):
            actual_home_host = ""
        issues = []
        if brand != expected["brand"] or actual_home_host != expected["official_domain"]:
            issues.append("BRAND_OR_DOMAIN_MISMATCH")
        if policy.startswith("REJECT"):
            issues.append(policy)
        day = obj.get("published_on")
        try:
            date.fromisoformat(day)
        except (TypeError, ValueError):
            issues.append("PUBLICATION_DATE_UNVERIFIED")
        text = obj.get("source_text")
        if not isinstance(text, str) or not 20 <= len(text) <= MAX_TEXT_CHARS:
            issues.append("MISSING_OR_OVERSIZED_TEXT")
            text = ""
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None
        # Short generic names like "Kit" are not reliable textual identity
        # signals. Legal entity remains unverified for every candidate.
        if len(expected["brand"]) < 5:
            issues.append("AMBIGUOUS_SHORT_BRAND")
        found = [] if issues else extract_indicators(text, expected["brand"])
        if not found and not issues:
            issues.append("NO_ATTRIBUTABLE_LITERAL_METRIC")
        reports.append({
            "case_id": slug,
            "source_url": url if not policy.startswith("REJECT") else None,
            "source_class": policy,
            "source_text_sha256": sha,
            "published_on": day if "PUBLICATION_DATE_UNVERIFIED" not in issues else None,
            "indicators": found,
            "issues": issues,
            "legal_entity_verified": False,
            "source_rights_independently_verified": False,
            "status": "NEEDS_REVIEW" if found else "REJECT_OR_RESEARCH",
            "eligible_for_publication": False,
        })
    return reports


def process_leads(document: dict, identities: dict) -> list[dict]:
    """Index the existing seven-request HN lead output; never follow links."""
    if (document.get("contract") != "P4.26_PRIVATE_RESEARCH_LEADS_V1"
            or document.get("publication_allowed") is not False
            or document.get("marketplaces_listing_crawled") is not False):
        raise ValueError("Unexpected or unsafe lead scan input")
    items = document.get("candidates")
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ValueError("Unbounded discovery intake")
    out = []
    for row in items:
        slug = row.get("slug") if isinstance(row, dict) else None
        if slug not in identities:
            raise ValueError("Unknown research identity")
        stories = row.get("stories")
        if not isinstance(stories, list) or len(stories) > 3:
            raise ValueError("Unbounded external leads")
        links = []
        for story in stories:
            if not isinstance(story, dict) or story.get("status") != "UNVERIFIED_DISCOVERY_LEAD":
                raise ValueError("Unexpected elevated discovery evidence")
            u = story.get("discussion_url")
            if (not isinstance(u, str) or not re.fullmatch(
                    r"https://news\.ycombinator\.com/item\?id=\d+", u)):
                raise ValueError("Untrusted community reference")
            links.append(u)
        out.append({
            "case_id": slug,
            "brand": identities[slug]["brand"],
            "official_domain": identities[slug]["official_domain"],
            "legal_entity_status": "UNVERIFIED",
            "community_references": links,
            "status": "RESEARCH_ORIGINAL_SOURCE",
            "eligible_for_publication": False,
        })
    return out


def build_report(leads: dict | None = None, snapshots: dict | None = None) -> dict:
    identities = load_identities()
    return {
        "contract": "P430_PRIVATE_EVIDENCE_TRIAGE_V1",
        "network_requests": 0,
        "sources_fetched": 0,
        "marketplace_scrapes": 0,
        "financial_claims_verified": 0,
        "publication_allowed": False,
        "source_rights_independently_verified": False,
        "lead_queue": process_leads(leads, identities) if leads else [],
        "source_candidates": process_snapshots(snapshots, identities) if snapshots else [],
        "notices": [
            "HN 搜索命中不是经营证据；本程序从不访问原文或采集挂牌。",
            "原文快照可生成待审查字面指标，但不能证明法律主体、许可或指标真实性。",
            "严禁自动改写正式证据台账；R3 与创业可复制性审核尚未完成。",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Private offline R2 evidence triage; no network")
    parser.add_argument("--leads", type=Path)
    parser.add_argument("--snapshots", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.leads and not args.snapshots:
        parser.error("Supply a private lead report and/or approved snapshot")
    target = args.output.resolve()
    if target.is_relative_to(ROOT.resolve()):
        raise ValueError("Private evidence must never be written into public artifacts")
    report = build_report(
        leads=load_private_json(args.leads) if args.leads else None,
        snapshots=load_private_json(args.snapshots) if args.snapshots else None,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PRIVATE_REVIEW_ONLY",
        "lead_count": len(report["lead_queue"]),
        "snapshot_count": len(report["source_candidates"]),
        "admitted": 0,
        "network_requests": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
