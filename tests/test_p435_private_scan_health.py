"""P4.35: single-merge live smoke report, hard validation and zero-publication."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/research"))
import p435_private_scan_health as health
import p426_daily_leads as hn
from p430_company_evidence_review import load_identities


def reports(hn_good=2, rss_good=True, restored=False):
    scan={
        "contract":"P4.26_PRIVATE_RESEARCH_LEADS_V1","mode":"READ_ONLY_ONLINE",
        "publication_allowed":False,"marketplaces_listing_crawled":False,
        "source_scope":"PUBLIC_SEARCH_INDEX_ONLY","network_requests_max":7,
        "network_requests_attempted":2,"network_requests_successful":hn_good,
        "network_requests_failed":2-hn_good,"candidate_count":1,
        "candidates":[{"error":None if hn_good>0 else "TimeoutError"}],
        "run_date_utc":"2026-10-09",
    }
    delta={
        "contract":"P434_PRIVATE_DAILY_DELTA_V1","eligible_for_publication":False,
        "financial_claims_verified":0,"network_requests_added":0,"run_date_utc":"2026-10-09",
        "source_http_status":"AT_LEAST_ONE_LIVE_HTTP_SUCCESS" if hn_good or rss_good else "NO_LIVE_HTTP_CONFIRMED",
        "previous_index_available":restored,"observed_in_this_batch":3,
        "fingerprint_history_size":12,
        "new_since_available_index":1 if restored else None,
    }
    rss=health.RSS_GOOD if rss_good else health.RSS_BAD
    prior="P434_PRIOR_HASH_INDEX_RESTORED" if restored else "P434_PRIOR_ARTIFACT_NOT_AVAILABLE"
    return scan,delta,rss,prior


class PrivateHealthTests(unittest.TestCase):
    def test_both_sources_success_and_aggregate_only(self):
        report=health.summarize(*reports())
        self.assertEqual(report["status"],"BOTH_SOURCES_RESPONDED")
        self.assertEqual(report["http_success_total"],3)
        self.assertEqual(report["http_attempts_total"],3)
        self.assertEqual(report["cleaned_unique_records"],3)
        self.assertFalse(report["prior_index_restored"])
        self.assertFalse(report["publication_allowed"])
        self.assertNotIn("example",json.dumps(report))

    def test_both_sources_failed_never_claim_success(self):
        result=health.summarize(*reports(0,False))
        self.assertEqual(result["status"],"NO_HTTP_SUCCESSES")
        self.assertEqual(result["http_success_total"],0)
        self.assertEqual(result["http_attempts_total"],3)
        self.assertEqual(result["publications"],0)

    def test_partial_success_and_restoration(self):
        result=health.summarize(*reports(1,False,restored=True))
        self.assertEqual(result["status"],"PARTIAL_SOURCE_SUCCESS")
        self.assertTrue(result["prior_index_restored"])
        self.assertEqual(result["new_urls_since_previous_index"],1)

    def test_refuse_forged_counts_financial_claims_restoration(self):
        s,d,r,p=reports(0,False)
        s["network_requests_failed"]=1
        with self.assertRaises(ValueError):
            health.summarize(s,d,r,p)
        s,d,r,p=reports(0,False)
        d["source_http_status"]="AT_LEAST_ONE_LIVE_HTTP_SUCCESS"
        with self.assertRaisesRegex(ValueError,"claimed live"):
            health.summarize(s,d,r,p)
        s,d,r,p=reports()
        d["financial_claims_verified"]=1
        with self.assertRaises(ValueError):
            health.summarize(s,d,r,p)
        s,d,r,p=reports(restored=True)
        with self.assertRaisesRegex(ValueError,"Rolling index"):
            health.summarize(s,d,r,"P434_PRIOR_ARTIFACT_NOT_AVAILABLE")

    def test_invalid_health_files_and_private_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            txt=Path(temp)/"state.txt"
            txt.write_text("P434_RSS_HTTP_OK\n",encoding="utf-8")
            self.assertEqual(health.status_file(txt,{health.RSS_GOOD,health.RSS_BAD}),health.RSS_GOOD)
            txt.write_text("P434_RSS_OK_INJECTED",encoding="utf-8")
            with self.assertRaises(ValueError):
                health.status_file(txt,{health.RSS_GOOD,health.RSS_BAD})
        with self.assertRaises(ValueError):
            health.safe_output(ROOT/"web/dist/public_health.json")

    def test_summary_excludes_source_titles_and_secrets(self):
        summary=health.summarize(*reports(1,True))
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"GITHUB_STEP_SUMMARY"
            health.write_summary(summary,path)
            body=path.read_text(encoding="utf-8")
            self.assertIn("真实 HTTP",body)
            self.assertNotIn("https://",body)
            self.assertNotIn("Fathom Analytics",body)
            self.assertNotIn("token",body.lower())

    def test_end_to_end_cli_and_step_summary(self):
        scan, delta, rss, prior = reports(1, True, restored=False)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            files={name:folder/name for name in ("hn.json","delta.json","rss.txt","prior.txt","health.json","summary.txt")}
            files["hn.json"].write_text(json.dumps(scan),encoding="utf-8")
            files["delta.json"].write_text(json.dumps(delta),encoding="utf-8")
            files["rss.txt"].write_text(rss+"\\n",encoding="utf-8")
            files["prior.txt"].write_text(prior+"\\n",encoding="utf-8")
            script=str(ROOT/"scripts/research/p435_private_scan_health.py")
            cmd=[sys.executable,script,
                 "--hn",str(files["hn.json"]),"--rss-health",str(files["rss.txt"]),
                 "--restore-health",str(files["prior.txt"]),"--delta",str(files["delta.json"]),
                 "--output",str(files["health.json"])]
            run=subprocess.run(cmd,capture_output=True,text=True,cwd=ROOT,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr)
            result=json.loads(files["health.json"].read_text(encoding="utf-8"))
            self.assertEqual(result["http_success_total"],2)
            summary=subprocess.run([sys.executable,script,"print-summary",
                "--input",str(files["health.json"]),"--output",str(files["summary.txt"])],
                capture_output=True,text=True,cwd=ROOT,timeout=10)
            self.assertEqual(summary.returncode,0,summary.stderr)
            self.assertIn("真实 HTTP",files["summary.txt"].read_text(encoding="utf-8"))

    def test_real_smoke_candidate_matches_identity_registry(self):
        targets=hn.research_targets(date(2026,10,9),1)
        self.assertEqual(len(targets),1)
        identities=load_identities()
        self.assertEqual(targets[0]["name"],identities[targets[0]["slug"]]["brand"])

    def test_exact_one_time_merge_message_and_original_daily_rate(self):
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 */6 * * *'"),1)
        self.assertIn("startsWith(github.event.head_commit.message, 'P435_PRIVATE_SMOKE_ONCE_20261009')",wf)
        self.assertIn('if [ "$P435_SMOKE_ONCE" = "1" ]; then max_companies=1; fi',wf)
        self.assertIn('max_companies=6',wf)
        self.assertIn('p435_private_scan_health.py print-summary',wf)
        self.assertIn('p435_scan_health.json',wf)
        self.assertIn("workflow_dispatch:",wf)  # Existing manual static build remains unchanged.
        self.assertNotIn("p431_sec_primary_probe.py --online",wf)


if __name__=="__main__":
    unittest.main()
