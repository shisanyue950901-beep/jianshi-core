#!/usr/bin/env python3
"""P4.26 bounded, read-only discovery LEADS, never verified financial evidence.

Daily scan reuses one existing GitHub static workflow's scheduled execution.
Only queries the documented public HN Algolia search API. Does not crawl results,
publish new companies, change the ledger, or access the Supabase production DB.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "release"))

API_HOST = "hn.algolia.com"
MAX_COMPANIES = 6
# Only public HN Algolia search metadata. Never search or extract protected
# Acquire/Flippa listing databases via third-party search as a workaround.
DISCOVERY_TOPICS = ("Show HN revenue", "bootstrapped founder revenue",
                    "micro SaaS paying customers", "solo founder business")
MAX_STORIES = 3
MAX_RESPONSE = 131_072
TIMEOUT_SECONDS = 4


def safe_link(value: object) -> str | None:
    if not isinstance(value, str) or len(value) > 1200:
        return None
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return None
    if parts.hostname.endswith((".local", ".internal")) or parts.hostname in ("localhost", "127.0.0.1"):
        return None
    return value


def research_targets(day: date, maximum: int) -> list[dict]:
    from p423_build_project_proofs import parse_cases
    from p425_public_admission import admitted_ids

    if not 1 <= maximum <= MAX_COMPANIES:
        raise ValueError("Too many candidates requested")
    unapproved = sorted((c for c in parse_cases() if c["id"] not in admitted_ids()), key=lambda x: x["id"])
    if not unapproved:
        raise RuntimeError("No private candidates remain for bounded research")
    offset = day.toordinal() % len(unapproved)
    order = unapproved[offset:] + unapproved[:offset]
    return [{"slug":c["id"], "name":c["title"].split("｜", 1)[0]} for c in order[:maximum]]


def lookup(query: str) -> list[dict]:
    if not query or len(query) > 110:
        raise ValueError("Unbounded research query")
    url = "https://" + API_HOST + "/api/v1/search?" + urlencode({
        "query": query, "tags": "story", "hitsPerPage": MAX_STORIES, "page": 0,
    })
    req = Request(url, headers={"User-Agent": "JianShiResearch/0.1 (+https://jianshi-bua.pages.dev/)",
                                "Accept": "application/json"})
    with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
        final = urlsplit(response.geturl())
        if response.status != 200 or final.scheme != "https" or final.hostname != API_HOST:
            raise ValueError("Untrusted public search response")
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Public search response too large")
    result = json.loads(raw)
    if not isinstance(result.get("hits"), list):
        raise ValueError("Unexpected search response")
    stories = []
    for hit in result["hits"][:MAX_STORIES]:
        if not isinstance(hit, dict):
            continue
        story_id = hit.get("objectID")
        if not isinstance(story_id, str) or not story_id.isdigit():
            continue
        title = hit.get("title")
        if not isinstance(title, str) or not 5 <= len(title) <= 240:
            continue
        external = safe_link(hit.get("url"))
        stories.append({
            "headline": re.sub(r"[\x00-\x1f]", "", title),
            "discussion_url": "https://news.ycombinator.com/item?id=" + story_id,
            "external_url": external,
            "published_at": hit.get("created_at") if isinstance(hit.get("created_at"), str) else None,
            "status": "UNVERIFIED_DISCOVERY_LEAD",
            "financial_evidence": False,
            "source_kind": "HN_SEARCH_INDEX_METADATA_ONLY",
        })
    return stories


def run(day: date, maximum: int, online: bool) -> dict:
    if not 1 <= maximum <= MAX_COMPANIES:
        raise ValueError("Bounded to at most 6 existing backlog companies")
    targets = research_targets(day, maximum)
    rows = []
    for candidate in targets:
        # This is a lead query, NOT a verified company claim.
        query = candidate["name"] + " revenue"
        record = {**candidate, "query": query, "status": "UNVERIFIED_DISCOVERY_LEAD",
                  "eligible_for_publication": False, "stories": [], "error": None}
        if online:
            try:
                record["stories"] = lookup(query)
            except Exception as exc:
                record["error"] = type(exc).__name__
        else:
            record["status"] = "OFFLINE_DRY_RUN"
        rows.append(record)
    # Rotate solo-founder stories through the *same* one-query budget.
    # No direct or indirect automated extraction of restricted marketplaces.
    discovery_query = DISCOVERY_TOPICS[day.toordinal() % len(DISCOVERY_TOPICS)]
    fresh = []
    if online:
        try:
            fresh = lookup(discovery_query)
        except Exception:
            pass
    return {
        "contract": "P4.26_PRIVATE_RESEARCH_LEADS_V1",
        "run_date_utc": day.isoformat(),
        "mode": "READ_ONLY_ONLINE" if online else "OFFLINE_DRY_RUN",
        "source": "https://hn.algolia.com/api",
        "source_scope": "PUBLIC_SEARCH_INDEX_ONLY",
        "candidate_count": len(targets),
        "network_requests_max": MAX_COMPANIES + 1,
        "response_bytes_max": MAX_RESPONSE,
        "timeout_seconds_each": TIMEOUT_SECONDS,
        "candidates": rows,
        "discovery_query": discovery_query,
        "discovery_provider": "PUBLIC_HN_ALGOLIA_SEARCH_ONLY",
        "marketplaces_listing_crawled": False,
        "unmatched_new_project_leads": fresh,
        "publication_allowed": False,
        "notices": [
            "检索命中不是原始经营证据，更不是 L3/L4 审核结果",
            "原网页未被抓取或核实，公司身份和收入声明未经验证",
            "不得把研究线索直接写入公开证据台账或网站",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true", help="Use only public HN search API with hard caps")
    parser.add_argument("--max-companies", type=int, default=6)
    parser.add_argument("--date", help="UTC YYYY-MM-DD, for deterministic local tests")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    day = date.fromisoformat(args.date) if args.date else datetime.now(timezone.utc).date()
    report = run(day, args.max_companies, args.network)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mode": report["mode"], "candidate_count": report["candidate_count"],
                      "status": "PRIVATE_RESEARCH_ONLY", "published": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
