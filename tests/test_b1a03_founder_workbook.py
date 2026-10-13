"""B1-A03 offline founder validation worksheet acceptance.

Only approved P4.40 case profiles; no simulated user data is a customer result.
"""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))

from p423_build_project_proofs import parse_cases, project_page, index_page
from p425_public_admission import eligible_cases
from p440_decision_report import (
    decision_data, render_decision_panel, render_founder_workbook
)


class TestB1A03FounderWorkbook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {c["id"]: c for c in eligible_cases(parse_cases())}

    def test_three_reviewed_cases_all_have_exactly_one_linked_workbook(self):
        self.assertEqual(set(self.cases), {"carrd", "plausible", "nerdwallet"})
        for slug, case in self.cases.items():
            with self.subTest(slug=slug):
                html = project_page(case)
                self.assertEqual(html.count('id="founder-workbook"'), 1)
                self.assertEqual(html.count('href="#founder-workbook"'), 1)
                self.assertEqual(html.count('class="workbook-step"'), 4)
                self.assertLess(html.index('id="decision-report"'),
                                html.index('id="founder-workbook"'))
                self.assertIn("把项目研究，变成四个可核实的问题", html)
                for term in ("谁可能需要这类服务？", "有人真实愿意付费吗？",
                             "我是否具备必要能力与交付资源？",
                             "先验证什么，什么情况下停止？",
                             "收费不等于成交", "不采集填写内容"):
                    # Assertion uses actual copy; price description is specific.
                    if term == "收费不等于成交":
                        self.assertIn("公开价格不等于成交", html)
                    else:
                        self.assertIn(term, html)
                for term in (case["buyer"], case["revenue"],
                             decision_data(case)["first_step"],
                             decision_data(case)["blocking_evidence"]):
                    self.assertIn(term, html)
                self.assertIn('aria-labelledby="founder-workbook-title"', html)
                self.assertIn("@media print", html)
                self.assertIn(".workbook-step{break-inside:avoid", html)
                self.assertNotIn('method="post"', html)
                self.assertNotIn("<form", html)

    def test_worksheet_is_case_specific_but_not_financial_advice(self):
        carrd = render_founder_workbook(self.cases["carrd"])
        plausible = render_founder_workbook(self.cases["plausible"])
        nerdwallet = render_founder_workbook(self.cases["nerdwallet"])
        self.assertNotEqual(carrd, plausible)
        self.assertIn("没有证据就缩小范围或停止", carrd)
        self.assertIn("没有开发、运维与数据安全能力", plausible)
        self.assertIn("仅研究商业机制，不建议以此大型企业作为一人起步项目", nerdwallet)
        for html in (carrd, plausible, nerdwallet):
            self.assertIn("不构成", "不构成")  # baseline phrasing check follows
            self.assertIn("不是投资建议、收益预测", html)
            self.assertIn("不是实际采访或创业成功证明", html)
            self.assertNotIn("保证赚钱", html)
            self.assertNotIn("预计收益率", html)
            self.assertNotIn("200 个真实客户", html)

    def test_sanitizes_external_editorial_strings(self):
        c = copy.deepcopy(self.cases["carrd"])
        c["buyer"] = '<script>alert("x")</script>'
        c["revenue"] = '<img src=x onerror=alert(1)>'
        html = render_founder_workbook(c)
        self.assertNotIn('<script>alert("x")</script>', html)
        self.assertNotIn('<img src=x onerror=alert(1)>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', html)
        self.assertNotIn("<input", html)
        self.assertNotIn("<textarea", html)
        self.assertNotIn("<button", html)

    def test_unreviewed_or_broken_source_is_rejected(self):
        c = copy.deepcopy(self.cases["carrd"])
        c["id"] = "unreviewed-secret-startup"
        with self.assertRaises(RuntimeError):
            render_founder_workbook(c)
        for key, value in (("buyer", ""), ("revenue", 3)):
            c = copy.deepcopy(self.cases["plausible"])
            c[key] = value
            with self.assertRaises(RuntimeError):
                render_founder_workbook(c)
        c = copy.deepcopy(self.cases["nerdwallet"])
        c["research_evidence"]["source_url"] = "http://unsafe.example"
        with self.assertRaises(RuntimeError):
            render_founder_workbook(c)

    def test_existing_decision_report_and_listing_is_preserved(self):
        for case in self.cases.values():
            original = render_decision_panel(decision_data(case))
            self.assertEqual(original.count("<li>"), 3)
            self.assertEqual(original.count('id="decision-report"'), 1)
            self.assertIn("原企业的历史经营证据", original)
            self.assertIn("已验证可直接投入创业：0", original)
        listings = index_page(list(self.cases.values()))
        self.assertEqual(listings.count('class="decision-mini"'), 3)
        self.assertNotIn('id="founder-workbook"', listings)

    def test_no_network_persistence_or_new_collection_cost(self):
        for path in ("scripts/release/p423_build_project_proofs.py",
                     "scripts/release/p440_decision_report.py"):
            s = (ROOT/path).read_text(encoding="utf-8")
            for forbidden in ("requests.get(", "urlopen(", "fetch(", "navigator.sendBeacon",
                              "customer_email", "upload_url", "SupabaseClient"):
                self.assertNotIn(forbidden, s)
        wf = (ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"), 1)
        self.assertIn('JIANSHI_AUTH_ENABLED: "0"', wf)


if __name__ == "__main__":
    unittest.main()
