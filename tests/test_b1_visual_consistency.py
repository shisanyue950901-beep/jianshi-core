"""B1: branded finder/company views without rewriting financial provenance."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from f21_g2_discovery import render as discovery_render, ENTRIES
from p423_build_project_proofs import index_page, project_page, parse_cases
from p425_public_admission import eligible_cases


class ElementAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "a":
            self.links.append(attrs.get("href"))


class VisualParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = eligible_cases(parse_cases())
        cls.directory = index_page(cls.cases)
        cls.discover = discovery_render()

    def test_finder_has_compact_branded_hero_and_retains_all_cards(self):
        page = self.discover
        self.assertIn('class="discover-steps"', page)
        self.assertIn("找到方向", page)
        self.assertIn("看懂收费", page)
        self.assertIn("核查风险", page)
        self.assertIn('aria-label="项目研究的三个步骤"', page)
        self.assertIn("#discover .hero:after",page)
        self.assertIn(".discover-card:focus-visible",page)
        self.assertIn("@media(max-width:650px)",page)
        self.assertEqual(page.count('data-discover-card data-category='),len(ENTRIES))
        self.assertIn('id="discover-query"',page)
        self.assertIn('id="discover-empty"',page)
        self.assertIn('id="discover-reset" hidden',page)
        self.assertNotIn('href="/account/preview/"',page)
        parsed = ElementAudit()
        parsed.feed(page)
        self.assertEqual(parsed.h1_count,1)
        for route,*_ in ENTRIES:
            self.assertIn(route,parsed.links)

    def test_company_directory_stays_exactly_three_source_admitted_cases(self):
        page = self.directory
        self.assertEqual(page.count('class="case-card"'),3)
        self.assertIn('class="case-directory-hero"',page)
        self.assertIn('class="case-directory-proof"',page)
        self.assertIn("0 个已确认可以直接复制盈利的项目",page)
        self.assertIn('class="case-browse"',page)
        self.assertIn('href="/discover/"',page)
        self.assertIn(".case-directory-hero:before",page)
        self.assertIn(".directory a.case-card:focus-visible",page)
        self.assertIn("@media(max-width:650px)",page)
        self.assertIn("不是赚钱排名",page)
        parsed = ElementAudit()
        parsed.feed(page)
        self.assertEqual(parsed.h1_count,1)
        for slug in ("carrd","plausible","nerdwallet"):
            self.assertEqual(parsed.links.count("/projects/"+slug+"/"),1)

    def test_every_detail_preserves_its_evidence_and_research_actions(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                page=project_page(case)
                self.assertIn('class="case-detail-hero"',page)
                self.assertIn("不等于创业收益预测",page)
                self.assertIn("建议核查来源和成本",page)
                self.assertIn('aria-label="历史公司案例概览"',page)
                self.assertIn('id="decision-report"',page)
                self.assertIn('id="case-details"',page)
                self.assertIn('id="founder-workbook-toggle"',page)
                self.assertIn(case["research_evidence"]["source_url"],page)
                self.assertIn('id="themeToggle"',page)
                self.assertIn("prefers-reduced-motion",page)
                self.assertNotIn("<form",page)
                self.assertNotIn('data-auth-email-form',page)
                parsed = ElementAudit()
                parsed.feed(page)
                self.assertEqual(parsed.h1_count,1)

    def test_exact_admitted_case_gate_still_applies(self):
        with self.assertRaises(RuntimeError):
            index_page(self.cases[:2])


if __name__ == "__main__":
    unittest.main()
