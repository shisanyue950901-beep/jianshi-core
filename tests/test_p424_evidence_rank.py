"""P4.24 evidence-aware automatic ranking and attributable verification research."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LEDGER=json.loads((ROOT/"config/p424_project_research_evidence.json").read_text(encoding="utf-8"))
SCRIPT=ROOT/"scripts/release/p423_build_project_proofs.py"

class TestP424EvidenceRanking(unittest.TestCase):
    def test_curated_evidence_validates_attributable_company_source(self):
        self.assertEqual(LEDGER["version"],"P4.24_RESEARCH_EVIDENCE_V1")
        self.assertEqual(LEDGER["ranking_contract"],{
            "regulatory_filing":4,"founder_historical":3,
            "platform_attribution":2,"first_party_offer":1
        })
        by_id={x["id"]:x for x in LEDGER["additional_evidence"]}
        self.assertEqual(len(by_id),5)
        self.assertEqual(by_id["nerdwallet"]["tier"],"regulatory_filing")
        self.assertEqual(by_id["carrd"]["tier"],"founder_historical")
        self.assertEqual(by_id["plausible"]["tier"],"founder_historical")
        self.assertEqual(by_id["easlo"]["tier"],"platform_attribution")
        self.assertEqual(by_id["louise"]["tier"],"platform_attribution")
        for item in by_id.values():
            self.assertTrue(item["source_url"].startswith("https://"))
            self.assertIn("next_research",item)
            self.assertNotIn("listing_number",item["source_url"])
        self.assertIn("2025 年",by_id["nerdwallet"]["claim"])
        self.assertIn("未经",by_id["carrd"]["claim"])
        self.assertIn("2022",by_id["plausible"]["claim"])

    def test_evidence_ranking_in_data_but_public_cards_follow_founder_order(self):
        p=subprocess.run([sys.executable,str(SCRIPT)],cwd=ROOT,text=True,capture_output=True,timeout=35)
        self.assertEqual(p.returncode,0,p.stderr)
        d=json.loads(p.stdout)
        self.assertEqual(d["cases"],3)
        directory=(ROOT/"web/dist/projects/index.html").read_text(encoding="utf-8")
        links=re.findall(r'<a href="/projects/([a-z0-9-]+)/" class="case-card"',directory)
        self.assertEqual(links,["carrd","plausible","nerdwallet"])
        # Source evidence tiers remain in the original source and detail
        # pages. No profit-style ranks or unnecessary sort in this 3-card UI.
        self.assertNotIn('data-level=',directory)
        self.assertNotIn('data-sort=',directory)
        self.assertNotIn('id="projectSearch"',directory)
        self.assertIn("不是赚钱排名",directory)
        self.assertIn('data-theme="light"',directory)

    def test_true_filing_self_report_and_ordinary_unknowns(self):
        directory=ROOT/"web/dist/projects"
        cases={
            "nerdwallet":("这家公司有历史财报","8.366 亿美元","sec.gov/Archives/edgar"),
            "carrd":("企业曾公开谈过收入","10 万美元 MRR","saasclub.io/podcast/carrd"),
            "plausible":("企业曾公开谈过收入","7,000 多位","plausible.io/blog/open-source-saas"),

        }
        for slug,fragments in cases.items():
            x=(directory/slug/"index.html").read_text(encoding="utf-8")
            for fragment in fragments:
                self.assertIn(fragment,x,slug)
            self.assertIn("不代表你照着做也能赚钱",x)
            self.assertNotIn("Empire Flippers",x)
            self.assertNotIn("listing_number",x)
        self.assertFalse((directory/"tally/index.html").exists())
        self.assertFalse((directory/"easlo/index.html").exists())
        self.assertNotIn("这家公司有历史财报",(directory/"carrd/index.html").read_text(encoding="utf-8"))
        self.assertNotIn("这家公司有历史财报",(directory/"plausible/index.html").read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
