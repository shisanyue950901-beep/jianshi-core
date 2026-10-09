#!/usr/bin/env python3
"""P4.34: private offline rolling fingerprint index + previous artifact selection.

Consumes P4.33 private clean JSON. Never runs a network call, grants evidence
status, modifies a public directory, or stores titles/URLs in the index.
Previous artifact is selected from GITHUB-owned metadata only; download is
performed separately in the existing scheduled job using GH_TOKEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_CONTRACT = "P434_PRIVATE_ROLLING_HASH_INDEX_V1"
REPORT_CONTRACT = "P434_PRIVATE_DAILY_DELTA_V1"
SHA = re.compile(r"[0-9a-f]{64}\Z")
ARTIFACT = re.compile(r"research-leads-([1-9][0-9]{0,18})\Z")
MAX_BYTES = 512_000
MAX_ROWS = 1200
WINDOW_DAYS = 45


def load(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Missing or oversized private input")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Private JSON root must be an object")
    return obj


def safe_output(path: Path) -> Path:
    full = path.resolve()
    if full.is_relative_to(ROOT.resolve()):
        raise ValueError("Rolling private reports cannot write to repository")
    return full


def _iso(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Invalid GitHub artifact timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Naive artifact timestamp")
    return parsed.astimezone(timezone.utc)


def choose_artifact(api_response: dict, run_id: int, now: datetime) -> dict:
    """Only prior scheduled main-branch artifacts matching the strict name."""
    rows = api_response.get("artifacts")
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError("Untrusted/unbounded GitHub artifact metadata")
    if now.tzinfo is None:
        raise ValueError("Need timezone-aware UTC now")
    matches = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        match = ARTIFACT.fullmatch(name) if isinstance(name, str) else None
        if not match or item.get("expired") is not False:
            continue
        previous = int(match.group(1))
        job = item.get("workflow_run")
        if (previous == run_id or not isinstance(job, dict)
                or job.get("id") != previous
                or job.get("head_branch") != "main"):
            continue
        try:
            created = _iso(item["created_at"])
            expiration = _iso(item["expires_at"])
        except (ValueError, TypeError, KeyError):
            continue
        if created > now or expiration <= now:
            continue
        matches.append((created, previous))
    if not matches:
        return {"status": "NO_ELIGIBLE_PREVIOUS_ARTIFACT", "previous_run_id": None}
    matches.sort(reverse=True)
    return {"status": "PRIOR_ARTIFACT_FOUND", "previous_run_id": matches[0][1]}


def validate_previous(previous: dict, today: date) -> dict[str, tuple[date, date]]:
    if previous.get("contract") != STATE_CONTRACT or previous.get("publication_allowed") is not False:
        raise ValueError("Untrusted private rolling index")
    rows = previous.get("fingerprints")
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError("Over-budget rolling index")
    data: dict[str, tuple[date, date]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"hash", "first_seen", "last_seen"}:
            raise ValueError("Index contains raw URLs or unknown attributes")
        key = row["hash"]
        if not isinstance(key, str) or not SHA.fullmatch(key) or key in data:
            raise ValueError("Bad or duplicate URL fingerprint")
        try:
            first, last = date.fromisoformat(row["first_seen"]), date.fromisoformat(row["last_seen"])
        except (ValueError, TypeError):
            raise ValueError("Malformed index date") from None
        if not date(2020, 1, 1) <= first <= last <= today:
            raise ValueError("Impossible rolling-index dates")
        if (today - last).days < WINDOW_DAYS:
            data[key] = (first, last)
    return data


def make_delta(clean: dict, previous: dict | None, today: date | None = None) -> tuple[dict, dict]:
    day = today or datetime.now(timezone.utc).date()
    if (clean.get("contract") != "P433_PRIVATE_CLEAN_REVIEW_V1"
            or clean.get("publication_allowed") is not False
            or clean.get("financial_claims_verified") != 0
            or clean.get("legal_entities_verified") != 0
            or clean.get("network_requests_added") != 0):
        raise ValueError("Unknown or elevated ETL report")
    if clean.get("run_date_utc") != day.isoformat():
        raise ValueError("Rolling report day mismatch")
    rows = clean.get("records")
    if not isinstance(rows, list) or len(rows) > 40 or clean.get("accepted_unique_count") != len(rows):
        raise ValueError("Invalid P4.33 report size")
    state = validate_previous(previous, day) if previous is not None else {}
    seen = set()
    added, repeats = [], []
    for row in rows:
        if (not isinstance(row, dict) or row.get("eligible_for_publication") is not False
                or row.get("financial_evidence_verified") is not False
                or row.get("company_identity_verified") is not False):
            raise ValueError("Financial promotion in raw clean record")
        fp = row.get("fingerprint")
        url = row.get("canonical_url")
        if (not isinstance(fp, str) or not SHA.fullmatch(fp) or fp in seen
                or not isinstance(url, str) or hashlib.sha256(url.encode("utf-8")).hexdigest() != fp):
            raise ValueError("Corrupt/duplicated URL fingerprint in current report")
        seen.add(fp)
        if fp in state:
            first_seen, _ = state[fp]
            repeats.append(fp)
        else:
            first_seen = day
            added.append(fp)
        state[fp] = (first_seen, day)
    # Trim oldest hashes, never save original titles, URLs or article content.
    chosen = sorted(state.items(), key=lambda item: (item[1][1], item[0]), reverse=True)[:MAX_ROWS]
    index = {
        "contract": STATE_CONTRACT, "as_of_utc": day.isoformat(),
        "window_days": WINDOW_DAYS, "fingerprints": [
            {"hash": fp, "first_seen": first.isoformat(), "last_seen": last.isoformat()}
            for fp, (first, last) in sorted(chosen)
        ], "publication_allowed": False, "contains_urls_or_titles": False,
    }
    sources = clean.get("source_health") or {}
    hn = sources.get("HN") or {}
    rss = sources.get("RSS") or {}
    succeeded = hn.get("http_requests_successful")
    if succeeded is not None and (type(succeeded) is not int or not 0 <= succeeded <= 7):
        raise ValueError("Invalid HN HTTP receipt")
    live = bool((type(succeeded) is int and succeeded > 0) or rss.get("mode") == "LIVE_RSS_HTTP")
    baseline = previous is None
    delta = {
        "contract": REPORT_CONTRACT,
        "run_date_utc": day.isoformat(),
        "status": "FIRST_INDEX_BASELINE_NO_TREND" if baseline else "COMPARED_WITH_PRIOR_INDEX",
        "source_http_status": "AT_LEAST_ONE_LIVE_HTTP_SUCCESS" if live else "NO_LIVE_HTTP_CONFIRMED",
        "previous_index_available": not baseline,
        "observed_in_this_batch": len(rows),
        "new_since_available_index": None if baseline else len(added),
        "seen_in_available_index": None if baseline else len(repeats),
        "fingerprint_history_size": len(index["fingerprints"]),
        "raw_text_stored_in_index": False,
        "network_requests_added": 0,
        "financial_claims_verified": 0,
        "eligible_for_publication": False,
        "notices": [
            "首次运行仅建立基线，不能把同批记录全部称为跨日新增。",
            "历史状态来自48小时私有产物，产物失效或调度中断则回退冷启动，不保证无限期历史。",
            "URL摘要去重不等于对公司法律主体、营收金额或盈利能力的核实。",
        ],
    }
    return delta, index


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline private rolling fingerprint delta")
    sub = parser.add_subparsers(dest="command", required=True)
    select = sub.add_parser("select-artifact")
    select.add_argument("--metadata", type=Path, required=True)
    select.add_argument("--current-run-id", type=int, required=True)
    select.add_argument("--output", type=Path, required=True)
    ingest = sub.add_parser("build")
    ingest.add_argument("--clean", type=Path, required=True)
    ingest.add_argument("--previous", type=Path)
    ingest.add_argument("--report-output", type=Path, required=True)
    ingest.add_argument("--index-output", type=Path, required=True)
    opts = parser.parse_args()
    if opts.command == "select-artifact":
        result = choose_artifact(load(opts.metadata), opts.current_run_id, datetime.now(timezone.utc))
        path = safe_output(opts.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(result))
        return
    report_path = safe_output(opts.report_output)
    index_path = safe_output(opts.index_output)
    if report_path == index_path:
        raise ValueError("Index and report must use different paths")
    delta, index = make_delta(load(opts.clean), load(opts.previous) if opts.previous else None)
    for path, data in ((report_path, delta), (index_path, index)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": delta["status"], "source": delta["source_http_status"],
        "observed": delta["observed_in_this_batch"],
        "novelty": delta["new_since_available_index"],
        "published": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
