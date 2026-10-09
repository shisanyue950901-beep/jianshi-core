"""P4.36 nightly unattended quality gate: fail, degrade, audit and isolation."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/research"))
import p436_unattended_guard as guard

DAY=date(2026,10,9)


def bundles(hn_good=7, rss_good=1, prior=True, records=1):
    urls=[f"https://usefathom.com/blog/example-{n}" for n in range(records)]
    clean_rows=[{"fingerprint":hashlib.sha256(u.encode()).hexdigest(),
        "canonical_url":u,"eligible_for_publication":False,
        "financial_evidence_verified":False,"company_identity_verified":False} for u in urls]
    index_rows=[{"hash":row["fingerprint"],"first_seen":"2026-10-09",
                 "last_seen":"2026-10-09"} for row in clean_rows]
    successes=hn_good+rss_good
    status=("NO_HTTP_SUCCESSES" if successes==0 else
            "BOTH_SOURCES_RESPONDED" if successes==8 else "PARTIAL_SOURCE_SUCCESS")
    health={
        "contract":"P435_PRIVATE_AGGREGATE_HEALTH_V1",
        "publication_allowed":False,"contains_source_titles_or_urls":False,
        "run_date_utc":DAY.isoformat(),"financial_claims_verified":0,
        "publications":0,"marketplaces_crawled":0,"status":status,
        "hn_http_attempts":7,"hn_http_successes":hn_good,"hn_http_failures":7-hn_good,
        "rss_http_successes":rss_good,"rss_http_failures":1-rss_good,
        "http_attempts_total":8,"http_success_total":successes,
        "cleaned_unique_records":records,"rolling_history_fingerprints":records,
        "prior_index_restored":prior,
        "new_urls_since_previous_index":0 if prior else None,
    }
    clean={"contract":"P433_PRIVATE_CLEAN_REVIEW_V1","publication_allowed":False,
        "financial_claims_verified":0,"legal_entities_verified":0,
        "network_requests_added":0,"run_date_utc":DAY.isoformat(),
        "accepted_unique_count":records,"records":clean_rows}
    index={"contract":"P434_PRIVATE_ROLLING_HASH_INDEX_V1","publication_allowed":False,
        "contains_urls_or_titles":False,"as_of_utc":DAY.isoformat(),
        "fingerprints":index_rows}
    return health,clean,index


class UnattendedGuardTest(unittest.TestCase):
    def test_full_success_is_pass(self):
        verdict=guard.evaluate(*bundles(),DAY)
        self.assertEqual(verdict["verdict"],"PASS")
        self.assertEqual(verdict["http_successes"],8)
        self.assertEqual(verdict["automated_source_types"],2)
        self.assertEqual(verdict["private_rolling_fingerprints"],1)
        self.assertFalse(verdict["publication_allowed"])
        self.assertEqual(verdict["permitted_publications"],0)
        self.assertNotIn("https://",json.dumps(verdict))

    def test_zero_http_successes_is_fail(self):
        verdict=guard.evaluate(*bundles(0,0),DAY)
        self.assertEqual(verdict["verdict"],"FAIL")
        self.assertIn("ALL_SOURCES_UNREACHABLE",verdict["reason_codes"])
        self.assertEqual(verdict["http_successes"],0)

    def test_partial_success_degraded_but_not_a_blocking_failure(self):
        verdict=guard.evaluate(*bundles(4,0),DAY)
        self.assertEqual(verdict["verdict"],"DEGRADED")
        self.assertIn("SOME_HTTP_REQUESTS_FAILED",verdict["reason_codes"])
        self.assertEqual(verdict["http_attempts"],8)

    def test_first_historical_baseline_degraded_not_claiming_crossday(self):
        verdict=guard.evaluate(*bundles(7,1,prior=False),DAY)
        self.assertEqual(verdict["verdict"],"DEGRADED")
        self.assertIn("PREVIOUS_HASH_INDEX_UNAVAILABLE",verdict["reason_codes"])

    def test_zero_leads_with_success_is_warning_not_false_financial_claim(self):
        verdict=guard.evaluate(*bundles(7,1,records=0),DAY)
        self.assertEqual(verdict["verdict"],"DEGRADED")
        self.assertIn("NO_NORMALIZED_LEADS",verdict["reason_codes"])
        self.assertEqual(verdict["financial_claims_verified"],0)

    def test_unsafe_sources_wrong_counts_or_date_are_rejected(self):
        a,b,c=bundles()
        a["http_success_total"]=9
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)
        a,b,c=bundles()
        a["publication_allowed"]=True
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)
        a,b,c=bundles()
        a["run_date_utc"]="2024-10-09"
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)
        a,b,c=bundles()
        a["hn_http_attempts"]=6
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)

    def test_cleaned_financial_claim_promotion_fails(self):
        a,b,c=bundles()
        b["records"][0]["financial_evidence_verified"]=True
        with self.assertRaisesRegex(ValueError,"financially promoted"):
            guard.evaluate(a,b,c,DAY)
        a,b,c=bundles()
        b["accepted_unique_count"]=0
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)

    def test_index_unsafe_attributes_corruption_and_history_flag_fail(self):
        a,b,c=bundles()
        c["fingerprints"][0]["url"]="https://private.example"
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)
        a,b,c=bundles()
        c["fingerprints"][0]["hash"]="0"*64
        # Hash is valid syntax but different from clean; deliberately check inventory only here.
        c["fingerprints"][0]["hash"]="not-a-sha"
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)
        a,b,c=bundles(prior=False)
        a["new_urls_since_previous_index"]=1
        with self.assertRaises(ValueError):
            guard.evaluate(a,b,c,DAY)

    def test_cli_verdict_is_persisted_even_when_all_sources_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            for status, expected in ((0,"FAIL"),(7,"PASS")):
                a,b,c=bundles(hn_good=status,rss_good=0 if status==0 else 1)
                for name,data in (("health",a),("clean",b),("index",c)):
                    (base/(name+".json")).write_text(json.dumps(data),encoding="utf-8")
                dest=base/"verdict.json"
                proc=subprocess.run([sys.executable,str(ROOT/"scripts/research/p436_unattended_guard.py"),
                    "--health",str(base/"health.json"),"--clean",str(base/"clean.json"),
                    "--index",str(base/"index.json"),"--output",str(dest),"--date","2026-10-09"],
                    cwd=ROOT,capture_output=True,text=True,timeout=10)
                self.assertEqual(proc.returncode,1 if status==0 else 0,proc.stderr)
                saved=json.loads(dest.read_text(encoding="utf-8"))
                self.assertEqual(saved["verdict"],expected)
                self.assertNotIn("usefathom",dest.read_text(encoding="utf-8"))
                if status==0:self.assertIn("::error",proc.stdout)

    def test_no_private_data_can_be_written_inside_repo(self):
        for path in ("config/research.json","web/dist/research.json","scripts/keys.json"):
            with self.assertRaises(ValueError):
                guard.private_path(ROOT/path)

    def test_workflow_retains_failed_runs_without_more_jobs_or_requests(self):
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 */6 * * *'"),1)
        self.assertIn("if: github.event_name == 'schedule'",wf)
        self.assertIn("always() && github.event_name == 'schedule'",wf)
        self.assertIn("p436_unattended_guard.py",wf)
        self.assertIn("p436_unattended_verdict.json",wf)
        self.assertIn("p426_daily_leads.py --network --max-companies 6",wf)
        self.assertNotIn("P435_SMOKE_ONCE",wf)
        self.assertNotIn("p431_sec_primary_probe.py --online",wf)
        self.assertNotIn("actions/cache",wf)
        self.assertIn("retention-days: 2",wf)
        self.assertNotIn("TinyFish",wf)


if __name__=="__main__":
    unittest.main()
