"""Founder case detail page: 5-second answers, deep research only on request.

Static HTML checks do not claim that actual phone or desktop interaction passed.
"""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/release"))
from p423_build_project_proofs import parse_cases, project_page, PAYING_PARTIES
from p425_public_admission import eligible_cases
from p440_decision_report import decision_data
from p426_evidence_digest import derive_digest


class TagStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.detail_attrs=[]
        self.summary_count=0
        self.link_targets=[]
        self.ids=[]
        self.stack=[]
        self.all_details_valid=True

    def handle_starttag(self,tag,attrs):
        kv=dict(attrs)
        if tag=="details":
            self.detail_attrs.append(kv)
            self.stack.append({"summary":False})
        if tag=="summary":
            self.summary_count+=1
            if self.stack:
                self.stack[-1]["summary"]=True
        if kv.get("id"):
            self.ids.append(kv["id"])
        if tag=="a" and kv.get("href","").startswith("#"):
            self.link_targets.append(kv["href"][1:])

    def handle_endtag(self,tag):
        if tag=="details":
            if not self.stack:
                self.all_details_valid=False
            elif not self.stack.pop()["summary"]:
                self.all_details_valid=False


class FounderCaseDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {c["id"]:c for c in eligible_cases(parse_cases())}

    def test_all_three_have_short_payer_and_honest_risk_before_deep_research(self):
        self.assertEqual(set(self.cases),{"carrd","plausible","nerdwallet"})
        for slug, case in self.cases.items():
            with self.subTest(slug=slug):
                html=project_page(case)
                digest=derive_digest(case)
                decision=decision_data(case)
                self.assertIn("30 秒看懂这门生意",html)
                self.assertIn(PAYING_PARTIES[slug],html)
                self.assertIn(digest.revenue,html)
                self.assertIn(digest.limitation,html)
                self.assertIn(decision["fit_label"],html)
                self.assertIn(decision["first_step"],html)
                self.assertLess(html.index("谁付钱？"), html.index('id="decision-report"'))
                self.assertLess(html.index('id="decision-report"'),html.index('id="case-details"'))
                self.assertLess(html.index('id="case-details"'),html.index('id="founder-workbook-toggle"'))
                self.assertIn('href="/projects/"',html)
                self.assertIn("不意味着成功",decision["fit_label"]+" 不意味着成功")

    def test_native_disclosure_is_closed_has_workbook_and_preserves_sources(self):
        for slug,case in self.cases.items():
            with self.subTest(slug=slug):
                html=project_page(case)
                parsed=TagStructure()
                parsed.feed(html)
                self.assertTrue(parsed.all_details_valid)
                self.assertFalse(parsed.stack)
                self.assertEqual(len(parsed.detail_attrs),3)
                self.assertEqual(parsed.summary_count,3)
                self.assertTrue(all("open" not in kv for kv in parsed.detail_attrs))
                self.assertEqual(len(parsed.ids),len(set(parsed.ids)))
                self.assertIn("founder-workbook-toggle",parsed.ids)
                self.assertIn("founder-workbook",parsed.ids)
                self.assertIn("founder-workbook-toggle",parsed.link_targets)
                for important in ("查看资料来源、成本和更多风险说明",
                                  "查看能力门槛、成本和其他需要核实的问题",
                                  "想自己验证？打开四步工作单",
                                  'id="validation-plan"',
                                  'id="founder-workbook"',
                                  'href="'+case["research_evidence"]["source_url"]+'"',
                                  'href="'+case["officialHomeUrl"]+'"'):
                    self.assertIn(important,html)
                self.assertEqual(html.count('class="workbook-step"'),4)
                self.assertEqual(html.count('class="digest"'),1)
                self.assertIn("找到什么经营证据？",html)
                self.assertIn("还不能证明什么？",html)

    def test_blue_purple_mother_style_and_small_screen_accessibility(self):
        html=project_page(self.cases["carrd"])
        self.assertIn("--accent:#6254b9",html)
        self.assertIn("--bg:#f7f8fc",html)
        self.assertIn("@media(max-width:590px)",html)
        self.assertIn('.decision-more summary:focus-visible',html)
        self.assertIn('.dossier-more summary:focus-visible',html)
        self.assertIn('.workbook-fold summary:focus-visible',html)
        self.assertIn('color-scheme:dark',html)
        self.assertIn("@media print",html)
        for danger in ("<form","type=\"email\"","navigator.sendBeacon",
                       "XMLHttpRequest(","localStorage.setItem"):
            self.assertNotIn(danger,html)

    def test_source_integrity_and_no_marketing_rewrite(self):
        for slug,case in self.cases.items():
            html=project_page(case)
            self.assertIn(case["research_evidence"]["claim"],html)
            self.assertIn(case["research_evidence"]["period"],html)
            self.assertIn(case["research_evidence"]["next_research"],html)
            self.assertIn("已验证可直接投入创业：0",html)
            self.assertIn("不是投资建议、收益预测",html)
            for bad in ("保证盈利","保证赚钱","200 个真实客户"):
                self.assertNotIn(bad,html)


if __name__=="__main__":
    unittest.main()
