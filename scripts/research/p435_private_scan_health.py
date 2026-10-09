#!/usr/bin/env python3
"""P4.35 machine-readable *aggregate* source health and one-time smoke results.

No HTTP calls; refuses unverifiable successes; never publishes data or prints
source titles, external URLs, financial claims, secrets or raw source content.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 524288
RSS_GOOD = "P434_RSS_HTTP_OK"
RSS_BAD = "P434_RSS_ACCESS_FAILED_NO_RETRY"
RESTORE_STATUSES = {
    "P434_PRIOR_ARTIFACT_NOT_AVAILABLE",
    "P434_PRIOR_HASH_INDEX_RESTORED",
    "P434_PRIOR_ARTIFACT_HAS_NO_HASH_INDEX",
    "P434_PRIOR_ARTIFACT_DOWNLOAD_FAILED",
    "P434_ARTIFACT_INDEX_API_FAILED",
}


def small_json(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Missing or overbudget private scan report")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Expected JSON object")
    return obj


def status_file(path: Path, choices: set[str]) -> str:
    if not path.is_file() or not 0 < path.stat().st_size <= 120:
        raise ValueError("Missing or overbudget source status")
    status = path.read_text(encoding="utf-8").strip()
    if status not in choices:
        raise ValueError("Unknown source status; fail closed")
    return status


def summarize(hn: dict, delta: dict, rss_state: str, prior_state: str) -> dict:
    if (hn.get("contract") != "P4.26_PRIVATE_RESEARCH_LEADS_V1"
            or hn.get("mode") != "READ_ONLY_ONLINE"
            or hn.get("publication_allowed") is not False
            or hn.get("marketplaces_listing_crawled") is not False
            or hn.get("source_scope") != "PUBLIC_SEARCH_INDEX_ONLY"
            or hn.get("network_requests_max") != 7):
        raise ValueError("Invalid HN scan provenance")
    attempted = hn.get("network_requests_attempted")
    successful = hn.get("network_requests_successful")
    failed = hn.get("network_requests_failed")
    if any(type(x) is not int for x in (attempted, successful, failed)):
        raise ValueError("Missing real request counters")
    if not 0 <= successful <= attempted <= 7 or failed != attempted - successful:
        raise ValueError("Inconsistent HN HTTP receipts")
    if attempted != hn.get("candidate_count", -1) + 1:
        raise ValueError("HN company count mismatches attempts")
    if not isinstance(hn.get("candidates"), list) or len(hn["candidates"]) != hn["candidate_count"]:
        raise ValueError("Unbounded HN candidate health")
    if sum(bool(row.get("error")) for row in hn["candidates"]) > failed:
        raise ValueError("Company errors exceed failures")
    if rss_state not in (RSS_GOOD, RSS_BAD) or prior_state not in RESTORE_STATUSES:
        raise ValueError("Unrecognized RSS or prior state")
    if (delta.get("contract") != "P434_PRIVATE_DAILY_DELTA_V1"
            or delta.get("eligible_for_publication") is not False
            or delta.get("financial_claims_verified") != 0
            or delta.get("network_requests_added") != 0):
        raise ValueError("Untrusted/financially promoted delta")
    if hn.get("run_date_utc") != delta.get("run_date_utc"):
        raise ValueError("Cross-date scan reports")
    date.fromisoformat(hn["run_date_utc"])
    if delta.get("source_http_status") != (
        "AT_LEAST_ONE_LIVE_HTTP_SUCCESS" if successful > 0 or rss_state == RSS_GOOD
        else "NO_LIVE_HTTP_CONFIRMED"
    ):
        raise ValueError("Mismatch in claimed live HTTP status")
    prior = delta.get("previous_index_available")
    if type(prior) is not bool or prior != (prior_state == "P434_PRIOR_HASH_INDEX_RESTORED"):
        raise ValueError("Rolling index state disagrees with prior artifact restore")
    observed = delta.get("observed_in_this_batch")
    if type(observed) is not int or not 0 <= observed <= 40:
        raise ValueError("Invalid cleaned item count")
    if delta.get("new_since_available_index") is not None and not prior:
        raise ValueError("First baseline falsely claims cross-day novelty")
    if type(delta.get("fingerprint_history_size")) is not int or not 0 <= delta["fingerprint_history_size"] <= 1200:
        raise ValueError("Invalid rolling-state size")
    live_providers = int(successful > 0) + int(rss_state == RSS_GOOD)
    overall = ("NO_HTTP_SUCCESSES" if live_providers == 0 else
               "PARTIAL_SOURCE_SUCCESS" if live_providers == 1 or failed > 0 else
               "BOTH_SOURCES_RESPONDED")
    return {
        "contract": "P435_PRIVATE_AGGREGATE_HEALTH_V1",
        "run_date_utc": hn["run_date_utc"],
        "status": overall,
        "hn_http_attempts": attempted, "hn_http_successes": successful,
        "hn_http_failures": failed,
        "rss_http_successes": int(rss_state == RSS_GOOD),
        "rss_http_failures": int(rss_state == RSS_BAD),
        "http_success_total": successful + int(rss_state == RSS_GOOD),
        "http_attempts_total": attempted + 1,
        "cleaned_unique_records": observed,
        "prior_index_restored": prior,
        "restoration_status": prior_state,
        "rolling_history_fingerprints": delta["fingerprint_history_size"],
        "new_urls_since_previous_index": delta["new_since_available_index"],
        "publications": 0,
        "financial_claims_verified": 0,
        "marketplaces_crawled": 0,
        "publication_allowed": False,
        "contains_source_titles_or_urls": False,
    }


def safe_output(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT.resolve()):
        raise ValueError("Cannot write private health to repository")
    return resolved


def write_summary(report: dict, path: Path) -> None:
    if report.get("contract") != "P435_PRIVATE_AGGREGATE_HEALTH_V1":
        raise ValueError("Invalid aggregate health summary")
    lines = [
        "### 见势 P4.35 私有采集健康（不代表财务真实性）",
        f"- 真实 HTTP：尝试 {report['http_attempts_total']}，成功 {report['http_success_total']}；状态 {report['status']}",
        f"- HN：{report['hn_http_successes']}/{report['hn_http_attempts']} 成功；RSS：{report['rss_http_successes']}/1 成功",
        f"- 清洗后链接：{report['cleaned_unique_records']}；历史指纹：{report['rolling_history_fingerprints']}",
        f"- 历史状态：{'恢复' if report['prior_index_restored'] else '冷启动'}；公开收录：0",
    ]
    if report.get("prior_index_restored"):
        lines.append(f"- 相对上次有效指纹索引的新链接：{report['new_urls_since_previous_index']}")
    text = "\n".join(lines) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(text)
    print(text)


def main() -> None:
    p = argparse.ArgumentParser(description="Local aggregate-only private HTTP scan health")
    sub = p.add_subparsers(dest="command", required=False)
    printing = sub.add_parser("print-summary")
    printing.add_argument("--input", type=Path, required=True)
    printing.add_argument("--output", type=Path, required=True)
    p.add_argument("--hn", type=Path)
    p.add_argument("--rss-health", type=Path)
    p.add_argument("--restore-health", type=Path)
    p.add_argument("--delta", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.command == "print-summary":
        write_summary(small_json(args.input), args.output)
        return
    for item in (args.hn, args.rss_health, args.restore_health, args.delta, args.output):
        if item is None:
            p.error("Aggregate mode requires --hn, --rss-health, --restore-health, --delta, --output")
    report = summarize(
        small_json(args.hn), small_json(args.delta),
        status_file(args.rss_health, {RSS_GOOD, RSS_BAD}),
        status_file(args.restore_health, RESTORE_STATUSES),
    )
    output = safe_output(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "http_attempts": report["http_attempts_total"],
        "http_successes": report["http_success_total"],
        "status": report["status"],
        "cleaned": report["cleaned_unique_records"],
        "published": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
