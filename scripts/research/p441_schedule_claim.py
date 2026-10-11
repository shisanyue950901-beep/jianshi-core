#!/usr/bin/env python3
"""P4.41: fail-closed, offline daily schedule claim from private Actions metadata.

A claim is uploaded BEFORE any research source request. This file never fetches
network data, reads private research leads, or writes into the repository.
Runs must also be serialized by the workflow's schedule-only concurrency group.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAIM_NAME = re.compile(r"research-scan-claim-(\d{8})-([1-9]\d{0,18})\Z")
LEGACY_NAME = re.compile(r"research-leads-([1-9]\d{0,18})\Z")
MAX_METADATA_BYTES = 524288
MAX_ARTIFACTS = 100


def private_path(raw: Path) -> Path:
    path = raw.resolve()
    if path.is_relative_to(ROOT.resolve()):
        raise ValueError("Private claim cannot be stored in repository/public site")
    return path


def read_metadata(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_METADATA_BYTES:
        raise ValueError("Missing or oversized GitHub artifact metadata")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("GitHub artifact metadata must be an object")
    return data


def _timestamp(raw: object) -> date:
    if not isinstance(raw, str) or not raw.endswith("Z"):
        raise ValueError("Invalid artifact creation time")
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Artifact creation time lacks timezone")
    return dt.astimezone(timezone.utc).date()


def _valid_identity(row: dict, expected_run: int) -> None:
    job = row.get("workflow_run")
    if (not isinstance(job, dict)
            or job.get("id") != expected_run
            or job.get("head_branch") != "main"):
        raise ValueError("Unexpected private artifact workflow identity")


def decide(metadata: dict, current_run_id: int, today: date) -> dict:
    """Refuse a second *attempt*, including when the first HTTP scan failed."""
    if not isinstance(current_run_id, int) or current_run_id <= 0:
        raise ValueError("Invalid current run ID")
    rows = metadata.get("artifacts")
    count = metadata.get("total_count")
    if (type(count) is not int or count < 0 or count > MAX_ARTIFACTS
            or not isinstance(rows, list) or len(rows) != count):
        # Missing pages can conceal a claim: do not authorize any network work.
        raise ValueError("Incomplete GitHub artifact inventory; fail closed")
    day_key = today.strftime("%Y%m%d")
    previous_claim = False
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Malformed GitHub artifact row")
        name = row.get("name")
        if not isinstance(name, str):
            raise ValueError("Malformed GitHub artifact name")
        if name.startswith("research-scan-claim-"):
            m = CLAIM_NAME.fullmatch(name)
            if not m:
                raise ValueError("Malformed daily scan claim name")
            if m.group(1) == day_key:
                _valid_identity(row, int(m.group(2)))
                if _timestamp(row.get("created_at")) != today:
                    raise ValueError("Claim date disagrees with GitHub timestamp")
                previous_claim = True
        elif name.startswith("research-leads-"):
            # Upgrade-safety: legacy scan evidence created earlier today
            # also blocks a duplicate on the day this feature is deployed.
            m = LEGACY_NAME.fullmatch(name)
            if not m:
                raise ValueError("Malformed legacy research artifact name")
            created = _timestamp(row.get("created_at"))
            if created == today:
                _valid_identity(row, int(m.group(1)))
                previous_claim = True
    return {
        "contract": "P441_DAILY_SCAN_DECISION_V1",
        "run_date_utc": today.isoformat(),
        "day_key": day_key,
        "run_id": current_run_id,
        "should_scan": not previous_claim,
        "reason_code": "ALREADY_CLAIMED" if previous_claim else "NO_PRIOR_CLAIM",
        "publication_allowed": False,
        "source_requests_per_day_max": {"hn": 7, "rss": 1, "github_p437": 2},
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Offline private daily scan deduplication")
    p.add_argument("--metadata", type=Path, required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--claim-output", type=Path, required=True)
    p.add_argument("--github-output", type=Path, required=True)
    p.add_argument("--date", type=date.fromisoformat, help="Only for deterministic tests")
    args = p.parse_args()
    day = args.date or datetime.now(timezone.utc).date()
    outcome = decide(read_metadata(args.metadata), args.run_id, day)
    claim_path = private_path(args.claim_output)
    gh_output = private_path(args.github_output)
    if claim_path == gh_output:
        raise ValueError("Claim and output paths must differ")
    gh_output.parent.mkdir(parents=True, exist_ok=True)
    with gh_output.open("a", encoding="utf-8") as f:
        f.write("should_scan=" + str(outcome["should_scan"]).lower() + "\n")
        f.write("scan_day=" + outcome["day_key"] + "\n")
    if outcome["should_scan"]:
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("P441_DAILY_SCAN_CLAIM_READY")
    else:
        print("P441_DAILY_SCAN_ALREADY_CLAIMED")


if __name__ == "__main__":
    main()
