#!/usr/bin/env python3
"""P4.36: automated fail-closed health verdict for scheduled private research.

Never performs network calls, publishes candidates or grants financial status.
A zero-success daily scan returns a nonzero exit status AFTER the caller has
built auditable private reports. Workflow retains those reports with always().
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 524288
EXPECTED_HN_DAILY_REQUESTS = 7
EXPECTED_RSS_DAILY_REQUESTS = 1
SOURCE_COUNT = 2
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


def read_private(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Missing or over-budget research health input")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Unexpected JSON root")
    return obj


def private_path(raw: Path) -> Path:
    path = raw.resolve()
    if path.is_relative_to(ROOT.resolve()):
        raise ValueError("Cannot write monitoring verdict inside repository or public site")
    return path


def require_int(obj: dict, key: str, lo: int, hi: int) -> int:
    val = obj.get(key)
    if type(val) is not int or not lo <= val <= hi:
        raise ValueError("Invalid monitoring counter: " + key)
    return val


def evaluate(health: dict, clean: dict, index: dict, day: date) -> dict:
    if (health.get("contract") != "P435_PRIVATE_AGGREGATE_HEALTH_V1"
            or health.get("publication_allowed") is not False
            or health.get("contains_source_titles_or_urls") is not False
            or health.get("run_date_utc") != day.isoformat()
            or health.get("financial_claims_verified") != 0
            or health.get("publications") != 0
            or health.get("marketplaces_crawled") != 0):
        raise ValueError("Private scan health contract or UTC date drift")
    hn_attempts = require_int(health,"hn_http_attempts",EXPECTED_HN_DAILY_REQUESTS,EXPECTED_HN_DAILY_REQUESTS)
    hn_success = require_int(health,"hn_http_successes",0,EXPECTED_HN_DAILY_REQUESTS)
    hn_fail = require_int(health,"hn_http_failures",0,EXPECTED_HN_DAILY_REQUESTS)
    rss_success = require_int(health,"rss_http_successes",0,1)
    rss_fail = require_int(health,"rss_http_failures",0,1)
    if (hn_success + hn_fail != hn_attempts
            or rss_success + rss_fail != EXPECTED_RSS_DAILY_REQUESTS
            or require_int(health,"http_attempts_total",8,8) != 8
            or require_int(health,"http_success_total",0,8) != hn_success + rss_success):
        raise ValueError("HTTP request accounting inconsistent")
    if (clean.get("contract") != "P433_PRIVATE_CLEAN_REVIEW_V1"
            or clean.get("publication_allowed") is not False
            or clean.get("financial_claims_verified") != 0
            or clean.get("legal_entities_verified") != 0
            or clean.get("network_requests_added") != 0
            or clean.get("run_date_utc") != day.isoformat()):
        raise ValueError("Unexpected or elevated cleaned data contract")
    rows = clean.get("records")
    if (not isinstance(rows,list) or len(rows) > 40
            or require_int(clean,"accepted_unique_count",0,40) != len(rows)
            or require_int(health,"cleaned_unique_records",0,40) != len(rows)):
        raise ValueError("Inconsistent cleaned record inventory")
    for row in rows:
        if (not isinstance(row,dict)
                or row.get("financial_evidence_verified") is not False
                or row.get("eligible_for_publication") is not False
                or row.get("company_identity_verified") is not False):
            raise ValueError("Research item appears financially promoted")
    if (index.get("contract") != "P434_PRIVATE_ROLLING_HASH_INDEX_V1"
            or index.get("publication_allowed") is not False
            or index.get("contains_urls_or_titles") is not False
            or index.get("as_of_utc") != day.isoformat()):
        raise ValueError("Unexpected private rolling index")
    fingerprints = index.get("fingerprints")
    if (not isinstance(fingerprints,list) or len(fingerprints) > 1200
            or require_int(health,"rolling_history_fingerprints",0,1200) != len(fingerprints)):
        raise ValueError("Rolling index size drift")
    observed = set()
    for row in fingerprints:
        if (not isinstance(row, dict) or set(row) != {"hash","first_seen","last_seen"}
                or not isinstance(row.get("hash"),str)
                or not SHA256.fullmatch(row["hash"]) or row["hash"] in observed):
            raise ValueError("Rolling history contains unsafe or duplicate data")
        observed.add(row["hash"])
        try:
            first = date.fromisoformat(row["first_seen"])
            last = date.fromisoformat(row["last_seen"])
        except (TypeError,ValueError):
            raise ValueError("Malformed private history date") from None
        if not date(2020,1,1) <= first <= last <= day:
            raise ValueError("Future or inverted rolling history date")
    # A current cleaned URL must survive into the rolling index; older
    # fingerprints may also be present, but today's links cannot disappear.
    for row in rows:
        fingerprint=row.get("fingerprint")
        canonical_url=row.get("canonical_url")
        if (not isinstance(fingerprint,str) or not SHA256.fullmatch(fingerprint)
                or not isinstance(canonical_url,str)
                or hashlib.sha256(canonical_url.encode("utf-8")).hexdigest() != fingerprint
                or fingerprint not in observed):
            raise ValueError("Cleaned URL is missing from rolling history or fingerprint drift")
    prior = health.get("prior_index_restored")
    if type(prior) is not bool:
        raise ValueError("Invalid previous-index restoration flag")
    prev_delta = health.get("new_urls_since_previous_index")
    if (prev_delta is not None and (type(prev_delta) is not int or not 0 <= prev_delta <= 40)):
        raise ValueError("Invalid cross-day delta")
    if (prior and prev_delta is None) or (not prior and prev_delta is not None):
        raise ValueError("Unverified cross-day novelty claim")
    successes = hn_success + rss_success
    expected_status = ("NO_HTTP_SUCCESSES" if successes == 0
                       else "BOTH_SOURCES_RESPONDED" if hn_success == 7 and rss_success == 1
                       else "PARTIAL_SOURCE_SUCCESS")
    if health.get("status") != expected_status:
        raise ValueError("Health status does not match HTTP receipts")
    reasons = []
    if successes == 0:
        reasons.append("ALL_SOURCES_UNREACHABLE")
    elif successes < 8:
        reasons.append("SOME_HTTP_REQUESTS_FAILED")
    if not prior:
        reasons.append("PREVIOUS_HASH_INDEX_UNAVAILABLE")
    if len(rows) == 0:
        reasons.append("NO_NORMALIZED_LEADS")
    outcome = ("FAIL" if successes == 0 else "DEGRADED" if reasons else "PASS")
    return {
        "contract": "P436_PRIVATE_UNATTENDED_VERDICT_V1",
        "run_date_utc": day.isoformat(),
        "verdict": outcome,
        "reason_codes": reasons,
        "http_attempts": 8,
        "http_successes": successes,
        "automated_source_types": SOURCE_COUNT,
        "cleaned_unique_records": len(rows),
        "private_rolling_fingerprints": len(fingerprints),
        "previous_index_restored": prior,
        "permitted_publications": 0,
        "financial_claims_verified": 0,
        "publication_allowed": False,
        "raw_source_content_stored": False,
        "notice": "FAIL means GitHub scheduled workflow marks failure; DEGRADED emits Actions warning only.",
    }


def main() -> None:
    p=argparse.ArgumentParser(description="Evaluate private scheduled capture health")
    p.add_argument("--health",type=Path,required=True)
    p.add_argument("--clean",type=Path,required=True)
    p.add_argument("--index",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--date",type=date.fromisoformat,default=None,help="UTC test date only")
    args=p.parse_args()
    result=evaluate(read_private(args.health),read_private(args.clean),read_private(args.index),
                    args.date or datetime.now(timezone.utc).date())
    path=private_path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Use GitHub Actions annotations; no titles/URLs/artifact content in logs.
    if result["verdict"] == "FAIL":
        print("::error title=JianShi Private Capture Failed::HN and RSS had zero successful HTTP requests; private evidence was retained.")
    elif result["verdict"] == "DEGRADED":
        print("::warning title=JianShi Private Capture Degraded::" + ",".join(result["reason_codes"]))
    print(json.dumps({"verdict":result["verdict"],"successes":result["http_successes"],
                      "requests":result["http_attempts"],"cleaned":result["cleaned_unique_records"],
                      "publications":0},ensure_ascii=False))
    if result["verdict"] == "FAIL":
        sys.exit(1)


if __name__=="__main__":
    main()
