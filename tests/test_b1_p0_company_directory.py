"""B1-P0: three concise company cards are a user journey, not evidence dashboard."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from p423_build_project_proofs import index_page, project_page, parse_cases
from p425_public_admission import eligible_cases


class TestB1P0CompanyDirectory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = eligible_cases(parse_cases())
        cls.html = index_page(cls.cases)

    def test_order_matches_home_and_discovery_not_profit_rank(self):
        page = self.html
        paths = [f'href="/projects/{slug}/"' for slug in ("carrd", "plausible", "nerdwallet")]
        self.assertEqual(page.count('class="case-card"'), 3)
        self.assertTrue(all(page.count(path) == 1 for path in paths))
        self.assertLess(page.index(paths[0]), page.index(paths[1]))
        self.assertLess(page.index(paths[1]), page.index(paths[2]))
        self.assertIn("不是赚钱排名", page)

    def test_first_view_uses_plain_business_facts_not_old_controls(self):
        page = self.html
        self.assertEqual(page.count('aria-label="案例生意概况"'), 3)
        for field in ("做什么：", "谁在用：", "谁付钱：", "怎么赚钱：", "上手门槛："):
            self.assertEqual(page.count(field), 3)
        self.assertIn("想看更多生意方向？去找项目", page)
        self.assertIn('href="/discover/"', page)
        self.assertNotIn('data-sort=', page)
        self.assertNotIn('id="projectSearch"', page)
        self.assertNotIn('class="decision-mini"', page)
        self.assertNotIn('aria-label="自动提炼的证据要点"', page)
        self.assertIn("@media(max-width:650px)", page)
        self.assertIn("--accent:#6254b9", page)

    def test_real_payer_and_risk_not_deleted(self):
        page = self.html
        self.assertIn("网站广告合作伙伴；读者不等于广告付款方", page)
        self.assertIn("公开定价不等于真实成交", page)
        self.assertIn("不是已经验证可以照做赚钱的项目", page)
        for case in self.cases:
            detail = project_page(case)
            self.assertIn('id="case-details"', detail)
            self.assertIn('id="founder-workbook-toggle"', detail)
            self.assertIn(case["research_evidence"]["source_url"], detail)

    def test_missing_admitted_case_stays_fail_closed(self):
        with self.assertRaises(RuntimeError):
            index_page(self.cases[:-1])


if __name__ == "__main__":
    unittest.main()
