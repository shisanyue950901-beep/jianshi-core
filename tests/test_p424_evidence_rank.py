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

    def test_dynamic_rank_and_two_different_views(self):
        p=subprocess.run([sys.executable,str(SCRIPT)],cwd=ROOT,text=True,capture_output=True,timeout=35)
        self.assertEqual(p.returncode,0,p.stderr)
        d=json.loads(p.stdout)
        self.assertEqual(d["cases"],20)
        directory=(ROOT/"web/dist/projects/index.html").read_text(encoding="utf-8")
        links=re.findall(r'<a href="/projects/([a-z0-9-]+)/" data-level="([1-4])"',directory)
        self.assertEqual(len(links),20)
        self.assertEqual(links[0],("nerdwallet","4"))
        self.assertEqual({x[0] for x in links[:3]},{"nerdwallet","carrd","plausible"})
        self.assertEqual(sum(1 for _,level in links if level=="4"),1)
        self.assertEqual(sum(1 for _,level in links if level=="3"),2)
        self.assertEqual(sum(1 for _,level in links if level=="2"),2)
        self.assertEqual(sum(1 for _,level in links if level=="1"),15)
        self.assertIn('data-sort="depth"',directory)
        self.assertIn('data-sort="gaps"',directory)
        self.assertIn("Number(a.dataset.level)-Number(b.dataset.level)",directory)
        self.assertIn("Number(b.dataset.level)-Number(a.dataset.level)",directory)
        self.assertIn("不是盈利或成功率排名",directory)
        self.assertIn('aria-pressed="true"',directory)
        self.assertIn("data-theme=\"light\"",directory)

    def test_true_filing_self_report_and_ordinary_unknowns(self):
        directory=ROOT/"web/dist/projects"
        cases={
            "nerdwallet":("历史公司级财务：有监管披露","8.366 亿美元","sec.gov/Archives/edgar"),
            "carrd":("历史收入：创始人／企业公开自述","10 万美元 MRR","saasclub.io/podcast/carrd"),
            "plausible":("历史收入：创始人／企业公开自述","7,000 多位","plausible.io/blog/open-source-saas"),
            "tally":("利润／经营成果：待独立核实","当前补证进度","tally.so"),
        }
        for slug,fragments in cases.items():
            x=(directory/slug/"index.html").read_text(encoding="utf-8")
            for fragment in fragments:
                self.assertIn(fragment,x,slug)
            self.assertIn("不能算作某家企业的经营证明",x)
            self.assertNotIn("Empire Flippers",x)
            self.assertNotIn("listing_number",x)
        self.assertNotIn("历史公司级财务：有监管披露",(directory/"carrd/index.html").read_text(encoding="utf-8"))
        self.assertNotIn("历史公司级财务：有监管披露",(directory/"plausible/index.html").read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
