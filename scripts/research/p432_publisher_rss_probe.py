#!/usr/bin/env python3
"""P4.32: bounded read-only on-demand publisher RSS metadata collector.

No full article content, no marketplace listings, no scheduling, no public
admission. Only the one feed that the publisher explicitly offers to readers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "config/p432_source_access_matrix.json"
URL = "https://usefathom.com/blog/feed.xml"
MAX_BYTES = 262144
MAX_RESULTS = 10
TIMEOUT = 6


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Publisher RSS redirect denied; review new feed URL first")


def load_policy() -> dict:
    registry = json.loads(POLICY.read_text(encoding="utf-8"))
    if registry.get("contract") != "P437_PRIVATE_SOURCE_ACCESS_V2":
        raise ValueError("Unknown source-rights contract")
    providers = registry.get("sources")
    if not isinstance(providers, list) or len(providers) != 10:
        raise ValueError("Unexpected provider matrix")
    by_id = {p["id"]: p for p in providers}
    if len(by_id) != 10:
        raise ValueError("Duplicate source provider")
    if (by_id["fathom-rss"].get("source_url") != URL
            or by_id["fathom-rss"].get("automated_fetch") != "DAILY_EXISTING_SCAN_SLOT_ONCE"
            or by_id["fathom-rss"].get("access") != "OFFICIAL_PUBLISHER_OFFERED_RSS"
            or by_id["fathom-rss"].get("max_requests_per_run") != 1
            or by_id["fathom-rss"].get("max_response_bytes") != MAX_BYTES
            or by_id["fathom-rss"].get("max_items_per_run") != MAX_RESULTS):
        raise ValueError("RSS collection permission changed")
    for name in ("acquire-listings", "flippa-listings", "microns-listings",
                 "indiehackers-pages"):
        if by_id[name].get("automated_fetch") != "FORBIDDEN":
            raise ValueError("Restricted provider was improperly enabled")
    if registry.get("publication_allowed") is not False:
        raise ValueError("RSS discovery cannot publish")
    return by_id


def safe_post_link(value: str) -> str | None:
    if not isinstance(value, str) or len(value) > 512:
        return None
    p = urlsplit(value)
    if (p.scheme != "https" or p.hostname not in ("usefathom.com", "www.usefathom.com")
            or p.username or p.password or p.port is not None
            or p.query or p.fragment or not re.fullmatch(r"/blog/[a-z0-9-]{2,150}/?", p.path)):
        return None
    return "https://usefathom.com" + p.path.rstrip("/")


def safe_date(value: str | None) -> str | None:
    if not isinstance(value, str) or len(value) > 100:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError):
        return None


def parse_feed(raw: bytes) -> list[dict]:
    if len(raw) > MAX_BYTES or len(raw) < 30:
        raise ValueError("Feed over budget or empty")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("XML entities/DTDs are not allowed")
    root = ElementTree.fromstring(raw)
    if root.tag != "rss":
        raise ValueError("Expected publisher RSS, not arbitrary XML/Atom")
    channel = root.find("channel")
    if channel is None or "Fathom" not in (channel.findtext("title") or ""):
        raise ValueError("Feed identity did not match Fathom publisher")
    seen: set[str] = set()
    result = []
    for item in channel.findall("item")[:60]:
        title = item.findtext("title")
        link = safe_post_link((item.findtext("link") or "").strip())
        if (not link or link in seen or not isinstance(title, str)
                or not 5 <= len(title.strip()) <= 180
                or any(ord(ch) < 32 and ch not in "\t\n" for ch in title)):
            continue
        seen.add(link)
        result.append({
            "title": re.sub(r"\s+", " ", title).strip(),
            "source_url": link,
            "published_on": safe_date(item.findtext("pubDate")),
            "source_kind": "FIRST_PARTY_RSS_METADATA_ONLY",
            "candidate_company": "Fathom Analytics",
            "company_id": "fathom",
            "financial_evidence_verified": False,
            "eligible_for_publication": False,
            "review_status": "UNVERIFIED_DISCOVERY_LEAD",
        })
        if len(result) >= MAX_RESULTS:
            break
    return result


def read_feed_online() -> bytes:
    req = Request(URL, headers={
        "User-Agent": "JianShiResearch/0.2 (+https://jianshi-bua.pages.dev/)",
        "Accept": "application/rss+xml, application/xml, text/xml",
        "Accept-Encoding": "identity",
    })
    opener = build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            media = response.headers.get("Content-Type", "").lower()
            if (response.status != 200 or response.geturl() != URL
                    or not any(t in media for t in ("xml", "rss"))):
                raise ValueError("RSS media type, status, or origin mismatch")
            raw = response.read(MAX_BYTES + 1)
    except HTTPError as exc:
        raise RuntimeError(f"RSS_ACCESS_STOP_{exc.code}") from None
    if len(raw) > MAX_BYTES:
        raise ValueError("RSS response exceeds max bytes")
    return raw


def private_destination(value: Path) -> Path:
    dst = value.resolve()
    if dst.is_relative_to(ROOT.resolve()):
        raise ValueError("Private RSS output must remain outside repository")
    return dst


def collect(raw: bytes, online: bool) -> dict:
    load_policy()
    records = parse_feed(raw)
    return {
        "contract": "P432_PRIVATE_RSS_LEADS_V1",
        "source_url": URL,
        "source_policy": "OFFICIAL_PUBLISHER_OFFERED_RSS",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "LIVE_RSS_HTTP" if online else "OFFLINE_FIXTURE_NOT_LIVE",
        "network_requests": 1 if online else 0,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_fulltext_stored": False,
        "marketplace_scrapes": 0,
        "records": records,
        "records_count": len(records),
        "financial_claims_verified": 0,
        "eligible_for_publication": False,
        "next_action": "人工/受控合法核对原始经营披露、品牌主体和报告期；不可直接晋级L3/L4。",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Collect publisher-offered RSS metadata for private research")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--online", action="store_true")
    mode.add_argument("--fixture", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    destination = private_destination(args.output)
    load_policy()
    if args.online:
        raw = read_feed_online()
    else:
        if not args.fixture.is_file() or args.fixture.stat().st_size > MAX_BYTES:
            raise ValueError("Invalid oversized/offline RSS input")
        raw = args.fixture.read_bytes()
    data = collect(raw, online=args.online)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "mode": data["mode"], "records": data["records_count"],
        "network_requests": data["network_requests"], "published": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
