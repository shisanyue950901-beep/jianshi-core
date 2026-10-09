"""P4.26: source-faithful public digest and private read-only research leads."""
import json
import re
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
sys.path.insert(0,str(ROOT/"scripts/research"))
from p423_build_project_proofs import parse_cases, build
from p425_public_admission import eligible_cases
from p426_evidence_digest import derive_digest
import p426_daily_leads as scanner

class TestP426Digests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={x["id"]:x for x in eligible_cases(parse_cases())}

    def test_distill_verbatim_and_keep_original_limitations(self):
        self.assertEqual(set(self.cases),{"nerdwallet","carrd","plausible"})
        nerd=derive_digest(self.cases["nerdwallet"])
        self.assertIn("8.366 亿美元",nerd.evidence)
        self.assertIn("4,870 万美元",nerd.evidence)
        self.assertEqual(nerd.period,"2025-12-31")
        self.assertIn("公司合并历史财务",nerd.limitation)
        self.assertIn("sec.gov",nerd.source_url)
        carrd=derive_digest(self.cases["carrd"])
        self.assertIn("10 万美元 MRR",carrd.evidence)
        self.assertIn("未经独立财务审计",carrd.limitation)
        plaus=derive_digest(self.cases["plausible"])
        self.assertIn("7,000 多位",plaus.evidence)
        self.assertIn("2022",plaus.period)

    def test_reject_absent_or_invalid_sources(self):
        with self.assertRaises(ValueError):
            derive_digest({"title":"Imaginary","offer":"A","buyer":"B","revenue":"C"})
        fake=dict(self.cases["carrd"])
        fake["research_evidence"]={**fake["research_evidence"],"tier":"platform_attribution"}
        with self.assertRaises(ValueError):
            derive_digest(fake)

    def test_built_public_pages_show_30_second_summary(self):
        result=build()
        self.assertEqual(result["cases"],3)
        index=(ROOT/"web/dist/projects/index.html").read_text(encoding="utf-8")
        self.assertEqual(index.count('aria-label="自动提炼的证据要点"'),3)
        self.assertIn("实际经营依据：",index)
        self.assertIn("8.366 亿美元",index)
        self.assertIn("未经独立财务审计",index)
        for slug in self.cases:
            page=(ROOT/f"web/dist/projects/{slug}/index.html").read_text(encoding="utf-8")
            self.assertIn("30 秒看懂这门生意",page)
            for required in ("卖什么？","怎么收费？","找到什么经营证据？","还不能证明什么？",
                             "披露时期：","查看原始经营依据"):
                self.assertIn(required,page)
            self.assertIn('rel="noopener noreferrer"',page)
            self.assertNotIn("Empire Flippers",page)
        self.assertFalse((ROOT/"web/dist/projects/easlo/index.html").exists())

    def test_daily_scan_is_bounded_does_not_touch_public_ledger(self):
        before=(ROOT/"config/p424_project_research_evidence.json").read_text(encoding="utf-8")
        report=scanner.run(date(2026,10,9),6,False)
        self.assertEqual(report["candidate_count"],6)
        self.assertFalse(report["publication_allowed"])
        self.assertEqual(report["network_requests_max"],7)
        self.assertTrue(all(x["status"]=="OFFLINE_DRY_RUN" for x in report["candidates"]))
        self.assertTrue(all(x["slug"] not in self.cases for x in report["candidates"]))
        self.assertEqual(before,(ROOT/"config/p424_project_research_evidence.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            scanner.run(date(2026,10,9),7,False)

    def test_algolia_lead_parsing_cannot_become_evidence(self):
        class Response:
            status=200
            def geturl(self): return "https://hn.algolia.com/api/v1/search?query=foo"
            def read(self,n): return json.dumps({"hits":[
                {"objectID":"1234","title":"A founder story about pricing","url":"https://example.org/story","created_at":"2026-01-01"},
                {"objectID":"bad!","title":"Malicious ignored","url":"https://example.org"},
                {"objectID":"555","title":"Internal network ignored","url":"http://127.0.0.1/private"}]}).encode()
            def __enter__(self): return self
            def __exit__(self,*args): return None
        with patch.object(scanner,"urlopen",return_value=Response()) as fake:
            leads=scanner.lookup("Example revenue")
        self.assertEqual(len(leads),2)
        self.assertEqual(leads[0]["status"],"UNVERIFIED_DISCOVERY_LEAD")
        self.assertIs(leads[0]["financial_evidence"],False)
        self.assertIsNone(leads[1]["external_url"])
        self.assertEqual(fake.call_args.kwargs["timeout"],4)
        self.assertIsNone(scanner.safe_link("http://localhost/private"))

    def test_existing_schedule_not_extra_or_paid_and_no_direct_publication(self):
        yaml=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '55 */6 * * *'",yaml)
        self.assertIn("if: github.event_name == 'schedule'",yaml)
        self.assertIn("p426_daily_leads.py --network --max-companies 6",yaml)
        self.assertIn("retention-days: 2",yaml)
        self.assertIn("if-no-files-found: ignore",yaml)
        scanner_code=(ROOT/"scripts/research/p426_daily_leads.py").read_text(encoding="utf-8")
        self.assertNotIn("tools.mcp",scanner_code)
        self.assertNotIn("supabase.co",scanner_code)
        self.assertNotIn("public_admission.json",scanner_code)
        self.assertIn('"publication_allowed": False',scanner_code)

if __name__=="__main__":
    unittest.main()
