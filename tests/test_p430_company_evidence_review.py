"""P4.30: offline private R2 identity and source triage never publishes L3/L4."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/research"))
import p430_company_evidence_review as r2


class PrivateR2TriageTest(unittest.TestCase):
    def setUp(self):
        self.identities = r2.load_identities()

    def snapshot(self, **updates):
        item = {
            "case_id": "plausible",
            "asserted_brand": "Plausible",
            "asserted_home": "https://plausible.io/",
            "source_url": "https://plausible.io/blog/open-source-saas",
            "published_on": "2022-06-22",
            "source_text": "Plausible reached $1M ARR in 2022; these figures are self-reported, not audited.",
        }
        item.update(updates)
        return {"contract": "P430_PRIVATE_SOURCE_SNAPSHOTS_V1", "items": [item]}

    def test_identity_register_is_explicit_and_does_not_verify_legal_entities(self):
        self.assertEqual(len(self.identities), 20)
        self.assertEqual(self.identities["nerdwallet"]["sec_cik"], "0001625278")
        self.assertEqual(self.identities["carrd"]["official_domain"], "carrd.com")
        self.assertEqual(self.identities["kit"]["legal_entity_status"], "UNVERIFIED")
        self.assertTrue(all(x["legal_entity"] is None for x in self.identities.values()))
        self.assertNotIn("helploom", self.identities)

    def test_source_is_original_first_party_or_single_curated_interview(self):
        p = self.identities["plausible"]
        self.assertEqual(r2.classify_source("plausible","https://plausible.io/blog/open-source-saas",p),
                         "FIRST_PARTY_REVIEW_ONLY")
        self.assertEqual(r2.classify_source("carrd","https://saasclub.io/podcast/carrd-aj-306/",self.identities["carrd"]),
                         "CURATED_INTERVIEW_REVIEW_ONLY")
        self.assertEqual(r2.classify_source("carrd","https://saasclub.io/podcast/other/",self.identities["carrd"]),
                         "REJECT_UNAPPROVED_SOURCE")
        self.assertEqual(r2.classify_source("nerdwallet",
                         "https://www.sec.gov/Archives/edgar/data/1625278/000162527826000014/nrds-20251231.htm",
                         self.identities["nerdwallet"]), "REGULATORY_FILING_REVIEW_ONLY")
        self.assertEqual(r2.classify_source("carrd","https://sec.gov/Archives/edgar/data/1625278/123/x.htm",
                         self.identities["carrd"]), "REJECT_UNAPPROVED_SOURCE")

    def test_block_listing_scrapes_fake_hosts_and_ssrf(self):
        entity=self.identities["carrd"]
        for url in ("https://app.acquire.com/public/123",
                    "https://flippa.com/buy/456",
                    "https://www.microns.io/startup/a",
                    "https://empireflippers.com/listing/abc"):
            self.assertEqual(r2.classify_source("carrd",url,entity),"REJECT_UNLICENSED_MARKETPLACE")
        for url in ("http://carrd.com/", "https://carrd.com.evil.org",
                    "https://u:p@carrd.com", "https://127.0.0.1/admin",
                    "https://localhost.local/", "https://carrd.com:4443/x"):
            self.assertTrue(r2.classify_source("carrd",url,entity).startswith("REJECT"))

    def test_literal_extraction_preserves_mrr_arr_and_currency_uncertainty(self):
        doc=self.snapshot(source_text="Plausible has $100K MRR, $1M ARR and 7,000 paid subscribers in 2022.")
        row=r2.process_snapshots(doc,self.identities)[0]
        self.assertEqual(row["status"],"NEEDS_REVIEW")
        self.assertEqual({x["metric"] for x in row["indicators"]},
                         {"MRR","ARR","PAID_CUSTOMERS_OR_SUBSCRIBERS"})
        self.assertTrue(all(x["currency"]=="DOLLAR_SYMBOL_UNRESOLVED"
                            for x in row["indicators"] if x["metric"] in {"MRR","ARR"}))
        self.assertFalse(row["legal_entity_verified"])
        self.assertFalse(row["source_rights_independently_verified"])
        self.assertFalse(row["eligible_for_publication"])
        self.assertNotIn(doc["items"][0]["source_text"],json.dumps(row))
        self.assertEqual(len(row["source_text_sha256"]),64)

    def test_no_cross_entity_revenue_inference_and_no_verified_profits(self):
        doc=self.snapshot(source_text="Plausible is a tool. Totally Different Inc has $1M ARR today.")
        row=r2.process_snapshots(doc,self.identities)[0]
        self.assertEqual(row["indicators"],[])
        self.assertEqual(row["status"],"REJECT_OR_RESEARCH")
        self.assertIn("NO_ATTRIBUTABLE_LITERAL_METRIC",row["issues"])
        report=r2.build_report(snapshots=self.snapshot())
        self.assertEqual(report["financial_claims_verified"],0)
        self.assertFalse(report["publication_allowed"])

    def test_mismatch_unapproved_source_and_missing_period_cannot_advance(self):
        bad=self.snapshot(asserted_brand="Plausible Fake",
                          asserted_home="https://plausible.io.evil.org/",
                          source_url="https://search.example.com/plausible-revenue",
                          published_on=None)
        r=r2.process_snapshots(bad,self.identities)[0]
        self.assertEqual(r["status"],"REJECT_OR_RESEARCH")
        self.assertEqual(r["indicators"],[])
        self.assertIn("BRAND_OR_DOMAIN_MISMATCH",r["issues"])
        self.assertIn("REJECT_UNAPPROVED_SOURCE",r["issues"])
        self.assertIn("PUBLICATION_DATE_UNVERIFIED",r["issues"])

    def test_ambiguous_short_brand_and_unknown_company_fail_closed(self):
        kit=self.snapshot(case_id="kit", asserted_brand="Kit",
                          asserted_home="https://kit.com/",
                          source_url="https://kit.com/blog/revenue",
                          source_text="Kit reported $12K MRR, perhaps.")
        item=r2.process_snapshots(kit,self.identities)[0]
        self.assertIn("AMBIGUOUS_SHORT_BRAND",item["issues"])
        self.assertEqual(item["indicators"],[])
        unknown=self.snapshot(case_id="not-in-registry")
        self.assertEqual(r2.process_snapshots(unknown,self.identities)[0]["status"],
                         "REJECT_UNKNOWN_IDENTITY")

    def test_hn_metadata_only_is_queued_not_approved(self):
        leads={
            "contract":"P4.26_PRIVATE_RESEARCH_LEADS_V1",
            "publication_allowed":False,
            "marketplaces_listing_crawled":False,
            "candidates":[
                {"slug":"gumroad","status":"UNVERIFIED_DISCOVERY_LEAD",
                 "stories":[{"status":"UNVERIFIED_DISCOVERY_LEAD",
                             "discussion_url":"https://news.ycombinator.com/item?id=1234",
                             "external_url":"https://gumroad.com/pricing"}]},
            ],
        }
        report=r2.build_report(leads=leads)
        self.assertEqual(report["network_requests"],0)
        self.assertEqual(report["sources_fetched"],0)
        self.assertEqual(report["lead_queue"][0]["status"],"RESEARCH_ORIGINAL_SOURCE")
        self.assertFalse(report["lead_queue"][0]["eligible_for_publication"])
        self.assertNotIn("external_url",str(report))
        leads["candidates"][0]["stories"][0]["status"]="FINANCIALLY_VERIFIED"
        with self.assertRaises(ValueError):
            r2.build_report(leads=leads)

    def test_intake_limits_and_public_gate_integrity(self):
        base=json.loads((ROOT/"config/p424_project_research_evidence.json").read_text(encoding="utf-8"))
        self.assertEqual({x["id"] for x in base["additional_evidence"]
                          if x["tier"] in ("regulatory_filing","founder_historical")},
                         {"carrd","nerdwallet","plausible"})
        document=self.snapshot()
        document["items"] *= 7
        with self.assertRaises(ValueError):
            r2.process_snapshots(document,self.identities)
        report=r2.build_report(snapshots=self.snapshot())
        self.assertFalse(report["publication_allowed"])
        self.assertEqual(report["marketplace_scrapes"],0)

    def test_cli_private_artifact_and_forbidden_public_output(self):
        with tempfile.TemporaryDirectory() as temp:
            input_path=Path(temp)/"snapshot.json"
            output_path=Path(temp)/"review.json"
            input_path.write_text(json.dumps(self.snapshot()),encoding="utf-8")
            result=subprocess.run([sys.executable,str(ROOT/"scripts/research/p430_company_evidence_review.py"),
                                   "--snapshots",str(input_path),"--output",str(output_path)],
                                  cwd=ROOT,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(report["publication_allowed"])
            self.assertEqual(report["source_candidates"][0]["status"],"NEEDS_REVIEW")
            result=subprocess.run([sys.executable,str(ROOT/"scripts/research/p430_company_evidence_review.py"),
                                   "--snapshots",str(input_path),
                                   "--output",str(ROOT/"web/dist/unsafe.json")],
                                  cwd=ROOT,capture_output=True,text=True,timeout=15)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((ROOT/"web/dist/unsafe.json").exists())

    def test_does_not_add_paid_services_or_schedules(self):
        script=(ROOT/"scripts/research/p430_company_evidence_review.py").read_text(encoding="utf-8")
        self.assertNotIn("urlopen",script)
        self.assertNotIn("requests.get",script)
        self.assertNotIn("mcp__TinyFish",script)
        self.assertNotIn("supabase",script.lower())
        workflow=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(workflow.count("cron: '55 0 * * *'"),1)
        self.assertEqual(workflow.count("cron: '55 6,12,18 * * *'"),1)
        self.assertEqual(workflow.count("- cron:"),2)
        self.assertIn("github.event_name == 'schedule' && github.event.schedule == '55 0 * * *'",workflow)


if __name__=="__main__":
    unittest.main()
