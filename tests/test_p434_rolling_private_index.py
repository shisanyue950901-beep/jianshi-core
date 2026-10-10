"""P4.34: artifact selection and rolling SHA-only private history tests."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/research"))
import p434_rolling_private_index as idx
DAY=date(2026,10,9)
NOW=datetime(2026,10,9,13,0,tzinfo=timezone.utc)


def clean(urls=(),hn_success=1,rss=False):
    records=[{"fingerprint":hashlib.sha256(u.encode()).hexdigest(),
              "canonical_url":u,"eligible_for_publication":False,
              "financial_evidence_verified":False,"company_identity_verified":False} for u in urls]
    return {"contract":"P433_PRIVATE_CLEAN_REVIEW_V1","publication_allowed":False,
            "financial_claims_verified":0,"legal_entities_verified":0,
            "network_requests_added":0,"run_date_utc":DAY.isoformat(),
            "accepted_unique_count":len(records),"records":records,
            "source_health":{"HN":{"http_requests_successful":hn_success},
                **({"RSS":{"mode":"LIVE_RSS_HTTP"}} if rss else {})}}


def artifact(run,name=None,branch="main",expires="2026-10-10T00:00:00Z",
             created="2026-10-09T09:00:00Z",expired=False):
    return {"id":run+100,"name":name or f"research-leads-{run}",
            "workflow_run":{"id":run,"head_branch":branch},"expires_at":expires,
            "created_at":created,"expired":expired}


class RollingStateTest(unittest.TestCase):
    def test_baseline_not_misrepresented_as_new(self):
        report,index=idx.make_delta(clean(["https://usefathom.com/blog/first"]),None,today=DAY)
        self.assertEqual(report["status"],"FIRST_INDEX_BASELINE_NO_TREND")
        self.assertIsNone(report["new_since_available_index"])
        self.assertEqual(report["source_http_status"],"AT_LEAST_ONE_LIVE_HTTP_SUCCESS")
        self.assertFalse(report["eligible_for_publication"])
        self.assertFalse(index["contains_urls_or_titles"])
        self.assertEqual(len(index["fingerprints"]),1)
        self.assertNotIn("usefathom",json.dumps(index))

    def test_cross_day_increment_and_duplicate(self):
        a="https://usefathom.com/blog/first"
        b="https://usefathom.com/blog/second"
        _,old=idx.make_delta(clean([a]),None,today=DAY)
        delta,new=idx.make_delta(clean([a,b]),old,today=DAY)
        self.assertEqual(delta["status"],"COMPARED_WITH_PRIOR_INDEX")
        self.assertEqual(delta["new_since_available_index"],1)
        self.assertEqual(delta["seen_in_available_index"],1)
        self.assertEqual(len(new["fingerprints"]),2)

    def test_live_health_fails_closed_without_http(self):
        a,_=idx.make_delta(clean([],hn_success=0),None,today=DAY)
        self.assertEqual(a["source_http_status"],"NO_LIVE_HTTP_CONFIRMED")
        b,_=idx.make_delta(clean([],hn_success=0,rss=True),None,today=DAY)
        self.assertEqual(b["source_http_status"],"AT_LEAST_ONE_LIVE_HTTP_SUCCESS")

    def test_malformed_and_promoted_clean_records_denied(self):
        current=clean(["https://example.org/post"])
        bad=json.loads(json.dumps(current))
        bad["records"][0]["financial_evidence_verified"]=True
        with self.assertRaises(ValueError):
            idx.make_delta(bad,None,today=DAY)
        bad=json.loads(json.dumps(current))
        bad["records"][0]["fingerprint"]="0"*64
        with self.assertRaises(ValueError):
            idx.make_delta(bad,None,today=DAY)
        bad=json.loads(json.dumps(current))
        bad["publication_allowed"]=True
        with self.assertRaises(ValueError):
            idx.make_delta(bad,None,today=DAY)
        bad=json.loads(json.dumps(current))
        bad["run_date_utc"]="2024-01-01"
        with self.assertRaises(ValueError):
            idx.make_delta(bad,None,today=DAY)

    def test_prior_hash_index_rejects_raw_url_and_bad_hash(self):
        _,old=idx.make_delta(clean(["https://example.org/first"]),None,today=DAY)
        old["fingerprints"][0]["url"]="https://example.org/first"
        with self.assertRaisesRegex(ValueError,"raw URLs"):
            idx.make_delta(clean([]),old,today=DAY)
        _,old=idx.make_delta(clean(["https://example.org/first"]),None,today=DAY)
        old["fingerprints"][0]["hash"]="wrong"
        with self.assertRaises(ValueError):
            idx.make_delta(clean([]),old,today=DAY)

    def test_expired_history_pruned(self):
        _,old=idx.make_delta(clean([]),None,today=DAY)
        old["fingerprints"]=[
            {"hash":"1"*64,"first_seen":"2026-07-01","last_seen":"2026-07-02"},
            {"hash":"2"*64,"first_seen":"2026-09-30","last_seen":"2026-10-01"},
        ]
        _,new=idx.make_delta(clean([]),old,today=DAY)
        self.assertEqual([x["hash"] for x in new["fingerprints"]],["2"*64])

    def test_prior_run_only_and_branch_scope(self):
        meta={"artifacts":[
            artifact(10,created="2026-10-09T08:00:00Z"),
            artifact(11,created="2026-10-09T10:00:00Z",branch="feature"),
            artifact(12,created="2026-10-09T11:00:00Z",expired=True),
            artifact(13,created="2026-10-09T12:00:00Z"),
            artifact(14,created="2026-10-09T12:30:00Z"),
            artifact(999,created="2026-10-09T12:59:00Z"),
        ]}
        out=idx.choose_artifact(meta,999,NOW)
        self.assertEqual(out,{"status":"PRIOR_ARTIFACT_FOUND","previous_run_id":14})
        out=idx.choose_artifact({"artifacts":[artifact(999)]},999,NOW)
        self.assertEqual(out["status"],"NO_ELIGIBLE_PREVIOUS_ARTIFACT")

    def test_reject_foreign_artifact_name_and_expired(self):
        meta={"artifacts":[artifact(123,name="research-leads-456"),
                           artifact(987,name="../research-leads-987"),
                           artifact(201,expires="2026-10-09T00:00:00Z")]}
        self.assertIsNone(idx.choose_artifact(meta,999,NOW)["previous_run_id"])
        with self.assertRaises(ValueError):
            idx.choose_artifact({"artifacts":[0]*101},999,NOW)

    def test_private_destination_and_build_cli(self):
        for name in ("web/dist/private.json","config/ledger.json","docs/research.json"):
            with self.assertRaises(ValueError):
                idx.safe_output(ROOT/name)
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory)
            current=d/"clean.json"
            report=d/"delta.json"
            state=d/"state.json"
            # Subprocess uses actual date; ensure fixture date matches runner day.
            case=clean(["https://usefathom.com/blog/first"])
            case["run_date_utc"]=date.today().isoformat()
            current.write_text(json.dumps(case),encoding="utf-8")
            p=subprocess.run([sys.executable,str(ROOT/"scripts/research/p434_rolling_private_index.py"),
                              "build","--clean",str(current),"--report-output",str(report),
                              "--index-output",str(state)],cwd=ROOT,capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertTrue(state.is_file())
            self.assertIsNone(json.loads(report.read_text())["new_since_available_index"])

    def test_same_daily_slot_and_existing_artifact_storage(self):
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"),1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"),1)
        self.assertNotIn("cron: '55 */6 * * *'",wf)
        self.assertIn("github.event.schedule == '55 0 * * *'",wf)
        self.assertNotIn("date -u +%H",wf)
        self.assertEqual(wf.count("p432_publisher_rss_probe.py --online"),1)
        self.assertIn("p434_rolling_private_index.py select-artifact",wf)
        self.assertIn("p434_rolling_private_index.py build",wf)
        self.assertIn("gh run download",wf)
        self.assertIn("actions: read",wf)
        self.assertIn("p434_hash_index.json",wf)
        self.assertIn("retention-days: 2",wf)
        self.assertNotIn("actions/cache",wf)
        self.assertNotIn("TinyFish",wf)


if __name__ == "__main__":
    unittest.main()
