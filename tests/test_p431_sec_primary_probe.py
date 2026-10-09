"""P4.31 private SEC original-source collection: never automatically publish XBRL."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/research"))
import p431_sec_primary_probe as sec


def fixtures():
    accession = "0001625278-26-000014"
    filed = "2026-02-25"
    period = "2025-12-31"
    common = {"accn":accession,"form":"10-K","filed":filed,"fy":2025,
              "fp":"FY","start":"2025-01-01","end":period}
    submissions = {
        "cik": 1625278, "name": "NerdWallet, Inc.",
        "filings": {"recent": {
            "accessionNumber": [accession],
            "form": ["10-K"],
            "filingDate": [filed],
            "reportDate": [period],
            "primaryDocument": ["nrds-20251231.htm"],
        }}
    }
    facts = {
        "cik": 1625278, "entityName": "NerdWallet, Inc.",
        "facts": {"us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {"USD": [{**common, "val": 836600000},
                                  {**common, "val": 10, "form": "10-Q"},
                                  {**common, "val": 777, "accn": "0000000000-00-000000"}]}},
            "NetIncomeLoss": {"units": {"USD": [{**common, "val": 48700000}]}},
            "Revenues": {"units": {"EUR": [{**common, "val": 999999}]}},
        }}
    }
    return submissions, facts


class SecPrimaryProbeTest(unittest.TestCase):
    def test_policy_fixes_two_official_subresources(self):
        registry=json.loads((ROOT/"config/p431_public_api_source_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["contract"],"P431_PRIVATE_SOURCE_EXPANSION_V1")
        self.assertEqual(len(registry["sources"]),3)
        self.assertFalse(registry["publish_to_website"])
        self.assertFalse(registry["restricted_listing_collection"])
        self.assertEqual({x["id"] for x in registry["sources"]},
                         {"sec-submissions","sec-companyfacts","fathom-firstparty-blog"})
        self.assertTrue(all(x["automatic_collection"] is False for x in registry["sources"]))
        self.assertFalse(next(x for x in registry["sources"]
                              if x["id"]=="fathom-firstparty-blog")["on_demand_fetch_allowed"])

    def test_only_reviewed_nerdwallet_cik_is_allowed(self):
        company=sec.load_identity("nerdwallet")
        self.assertEqual(company["legal_entity_status"],"UNVERIFIED")
        self.assertEqual(company["sec_cik"],"0001625278")
        for other in ("fathom","carrd","gumroad"):
            with self.assertRaises(ValueError):
                sec.load_identity(other)
        with self.assertRaises(ValueError):
            sec.sec_url("companyfacts","0000000001")
        with self.assertRaises(ValueError):
            sec.sec_url("frames","0001625278")

    def test_two_fixed_urls_and_operator_contact(self):
        self.assertEqual(sec.sec_url("submissions","0001625278"),
                         "https://data.sec.gov/submissions/CIK0001625278.json")
        self.assertEqual(sec.sec_url("companyfacts","0001625278"),
                         "https://data.sec.gov/api/xbrl/companyfacts/CIK0001625278.json")
        self.assertEqual(sec.validated_contact("team@example.com"),"team@example.com")
        for fake in ("", "foo", "x@y", "bad@mail.com\r\nHost:evil.org"):
            with self.assertRaises(ValueError):
                sec.validated_contact(fake)

    def test_structural_evidence_not_approval(self):
        sub, facts=fixtures()
        report=sec.triage("nerdwallet",sub,facts,{"submissions":"a"*64,"companyfacts":"b"*64})
        self.assertEqual(report["cik"],"0001625278")
        self.assertEqual(len(report["annual_filings"]),1)
        self.assertIn("/1625278/000162527826000014/nrds-20251231.htm",
                      report["annual_filings"][0]["filing_url"])
        self.assertEqual(len(report["latest_annual_metric_observations"]),2)
        self.assertEqual({r["tag"] for r in report["latest_annual_metric_observations"]},
                         {"NetIncomeLoss","RevenueFromContractWithCustomerExcludingAssessedTax"})
        self.assertEqual({r["unit"] for r in report["latest_annual_metric_observations"]}, {"USD"})
        self.assertEqual(report["status"],"NEEDS_REVIEW")
        self.assertFalse(report["eligible_for_publication"])
        self.assertFalse(report["legal_identity_verified"])
        self.assertFalse(report["startup_reproducibility_proven"])
        self.assertEqual(report["financial_claims_verified"],0)

    def test_wrong_entity_and_wrong_cik_never_cross_attribute(self):
        sub, facts=fixtures()
        sub["name"]="Totally Different Business"
        with self.assertRaisesRegex(ValueError,"issuer name"):
            sec.triage("nerdwallet",sub,facts,{})
        sub, facts=fixtures()
        facts["cik"]=1
        with self.assertRaisesRegex(ValueError,"CIK mismatch"):
            sec.triage("nerdwallet",sub,facts,{})
        sub, facts=fixtures()
        facts["entityName"]="Another Company Ltd"
        with self.assertRaisesRegex(ValueError,"identity mismatch"):
            sec.triage("nerdwallet",sub,facts,{})

    def test_bad_primary_document_and_mismatched_columns_fail_closed(self):
        sub, facts=fixtures()
        sub["filings"]["recent"]["primaryDocument"][0]="../../secrets.txt"
        report=sec.triage("nerdwallet",sub,facts,{})
        self.assertEqual(report["status"],"RESEARCH_MORE")
        self.assertEqual(report["annual_filings"],[])
        sub, facts=fixtures()
        sub["filings"]["recent"]["form"].append("10-Q")
        with self.assertRaisesRegex(ValueError,"columns"):
            sec.triage("nerdwallet",sub,facts,{})

    def test_reject_10q_currency_mismatch_and_incorrect_periods(self):
        sub, facts=fixtures()
        table=facts["facts"]["us-gaap"]["NetIncomeLoss"]["units"]["USD"]
        table.extend([
            {**table[0],"val":3,"start":"2025-10-01"},
            {**table[0],"val":4,"filed":"2026-03-01"},
            {**table[0],"val":5,"end":"2024-12-31"},
            {**table[0],"val":6,"fp":"Q4"},
            {**table[0],"val":7,"form":"10-Q"},
            {**table[0],"val":8,"accn":"0001111111-26-000001"},
        ])
        report=sec.triage("nerdwallet",sub,facts,{})
        self.assertEqual(len(report["latest_annual_metric_observations"]),2)

    def test_protect_private_output_and_no_credentials_or_source_text(self):
        with self.assertRaises(ValueError):
            sec.output_path(ROOT/"web/dist/sec.json")
        with self.assertRaises(ValueError):
            sec.output_path(ROOT/"config/p424_project_research_evidence.json")
        for keyword in ("TinyFish","supabase.co","flippa.com/buy","app.acquire.com/public"):
            self.assertNotIn(keyword,(ROOT/"scripts/research/p431_sec_primary_probe.py").read_text(encoding="utf-8"))

    def test_fixture_cli_makes_zero_network_requests(self):
        sub,facts=fixtures()
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            (folder/"submissions.json").write_text(json.dumps(sub),encoding="utf-8")
            (folder/"companyfacts.json").write_text(json.dumps(facts),encoding="utf-8")
            target=folder/"private_result.json"
            p=subprocess.run([sys.executable,str(ROOT/"scripts/research/p431_sec_primary_probe.py"),
                              "--fixtures",str(folder),"--output",str(target)],
                             cwd=ROOT,capture_output=True,text=True,timeout=20)
            self.assertEqual(p.returncode,0,p.stderr)
            report=json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(report["mode"],"OFFLINE_FIXTURE_NOT_LIVE")
            self.assertEqual(report["requests_made"],0)
            self.assertEqual(len(report["latest_annual_metric_observations"]),2)
            self.assertFalse(report["eligible_for_publication"])
            self.assertNotIn("team@example.com",target.read_text(encoding="utf-8"))

    def test_live_requires_declared_real_contact(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,str(ROOT/"scripts/research/p431_sec_primary_probe.py"),
                              "--online","--output",str(Path(d)/"result.json")],
                             cwd=ROOT,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(p.returncode,0)
            self.assertIn("--contact",p.stderr)

    def test_private_firstparty_founder_leads_are_not_admitted(self):
        file=ROOT/"config/p431_private_primary_source_leads.json"
        review=json.loads(file.read_text(encoding="utf-8"))
        self.assertEqual(review["contract"],"P431_PRIVATE_FIRST_PARTY_REVIEW_CANDIDATES_V1")
        self.assertFalse(review["publication_allowed"])
        self.assertEqual(len(review["candidates"]),1)
        fathom=review["candidates"][0]
        self.assertEqual(fathom["case_id"],"fathom")
        self.assertEqual(fathom["status"],"NEEDS_REVIEW")
        self.assertFalse(fathom["legal_entity_verified"])
        self.assertEqual(len(fathom["observations"]),3)
        self.assertTrue(all(o["source_url"].startswith("https://usefathom.com/blog/") for o in fathom["observations"]))
        self.assertTrue(all(o["published_on"] for o in fathom["observations"]))
        self.assertIsNone(fathom["observations"][-1]["reported_numeric"])
        public=json.loads((ROOT/"config/p424_project_research_evidence.json").read_text(encoding="utf-8"))
        self.assertNotIn("fathom",{x["id"] for x in public["additional_evidence"]})

    def test_existing_frequency_and_no_new_scheduling_or_paid_proxies(self):
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '55 */6 * * *'",wf)
        script=(ROOT/"scripts/research/p431_sec_primary_probe.py").read_text(encoding="utf-8")
        self.assertNotIn("cron",script)
        self.assertNotIn("urlopen(",script)
        self.assertNotIn("selenium",script)


if __name__=="__main__":
    unittest.main()
