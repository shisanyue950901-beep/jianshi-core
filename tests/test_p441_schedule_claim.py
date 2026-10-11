"""P4.41: scheduled private daily scan de-duplication and fail-closed claims."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/research"))
import p441_schedule_claim as claim

DAY = date(2026, 10, 11)


def row(run_id, name, created="2026-10-11T06:58:00Z", branch="main"):
    return {"name": name, "created_at": created, "expired": False,
            "workflow_run": {"id": run_id, "head_branch": branch}}


def metadata(*artifacts):
    return {"total_count": len(artifacts), "artifacts": list(artifacts)}


class ScheduledClaimTests(unittest.TestCase):
    def test_first_day_allows_exactly_one_claim(self):
        result = claim.decide(metadata(), 987, DAY)
        self.assertTrue(result["should_scan"])
        self.assertEqual(result["day_key"], "20261011")
        self.assertEqual(result["reason_code"], "NO_PRIOR_CLAIM")
        self.assertFalse(result["publication_allowed"])
        self.assertEqual(result["source_requests_per_day_max"],
                         {"hn": 7, "rss": 1, "github_p437": 2})

    def test_existing_claim_blocks_repeat_even_if_initial_capture_failed(self):
        existing = row(912, "research-scan-claim-20261011-912")
        self.assertFalse(claim.decide(metadata(existing), 913, DAY)["should_scan"])
        # A prior day's claim is not a current-day success.
        prior = row(912, "research-scan-claim-20261010-912",
                    created="2026-10-10T23:59:00Z")
        self.assertTrue(claim.decide(metadata(prior), 913, DAY)["should_scan"])

    def test_legacy_same_day_research_artifact_blocks_upgrade_duplicate(self):
        existing = row(912, "research-leads-912")
        self.assertFalse(claim.decide(metadata(existing), 913, DAY)["should_scan"])
        old = row(912, "research-leads-912", created="2026-10-10T22:00:00Z")
        self.assertTrue(claim.decide(metadata(old), 913, DAY)["should_scan"])

    def test_all_malformed_or_incomplete_inventory_fails_closed(self):
        broken = [
            {}, metadata(row(912, "research-scan-claim-20261011-913")),
            metadata(row(912, "research-scan-claim-20261011-912", branch="feature")),
            metadata(row(912, "research-scan-claim-20261011-912",
                         created="2026-10-10T23:00:00Z")),
            metadata(row(912, "research-scan-claim-20261011-bad")),
            {"total_count": 101, "artifacts": []},
            {"total_count": 1, "artifacts": []},
            {"total_count": False, "artifacts": []},
        ]
        for case in broken:
            with self.subTest(case=str(case)[:100]):
                with self.assertRaises(ValueError):
                    claim.decide(case, 913, DAY)

    def test_only_private_claim_file_and_safe_github_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            inventory, marker, output = [p / name for name in
                ("artifact_metadata.json", "claim.json", "github_output.txt")]
            inventory.write_text(json.dumps(metadata()), encoding="utf-8")
            cmd = [sys.executable, str(ROOT / "scripts/research/p441_schedule_claim.py"),
                   "--metadata", str(inventory), "--run-id", "987",
                   "--claim-output", str(marker), "--github-output", str(output),
                   "--date", "2026-10-11"]
            first = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=10, cwd=ROOT)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(output.read_text(), "should_scan=true\nscan_day=20261011\n")
            marker_info = json.loads(marker.read_text())
            self.assertFalse(marker_info["publication_allowed"])
            self.assertNotIn("title", str(marker_info).lower())
            inventory.write_text(json.dumps(metadata(
                row(987, "research-scan-claim-20261011-987"))), encoding="utf-8")
            output.write_text("", encoding="utf-8")
            marker.unlink()
            second = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=10, cwd=ROOT)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(output.read_text(), "should_scan=false\nscan_day=20261011\n")
            self.assertFalse(marker.exists())

    def test_preflight_cannot_write_repo_or_public_paths(self):
        with self.assertRaises(ValueError):
            claim.private_path(ROOT / "web/dist/claim.json")

    def test_workflow_enforces_four_slots_private_claim_and_no_new_source_calls(self):
        wf = (ROOT / ".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"), 1)
        self.assertIn("queue: max", wf)
        self.assertIn("cancel-in-progress: false", wf)
        self.assertIn("p441_schedule_claim.py", wf)
        self.assertIn("research-scan-claim-", wf)
        self.assertIn("daily_scan_claim_upload.outcome == 'success'", wf)
        self.assertIn("if-no-files-found: error", wf)
        self.assertIn("retention-days: 2", wf)
        self.assertEqual(wf.count('gh api "repos/$GITHUB_REPOSITORY/actions/artifacts?per_page=100"'), 1)
        self.assertEqual(wf.count("p426_daily_leads.py --network --max-companies 6"), 1)
        self.assertEqual(wf.count("p432_publisher_rss_probe.py --online"), 1)
        self.assertEqual(wf.count("p437_official_github_repo_probe.py --online"), 1)
        self.assertNotIn("date -u +%H", wf)
        self.assertIn("p436_unattended_guard.py", wf)
        self.assertIn("p435_scan_health.json", wf)
        self.assertIn("p436_unattended_verdict.json", wf)
        self.assertIn("p437_github_metrics.json", wf)


if __name__ == "__main__":
    unittest.main()
