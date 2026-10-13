"""B1: every anonymous business study starts with simple business answers.

Strictly preserves the six old public routes, historic sample fields, noindex
status, publication limits, and zero client collection.
"""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from p449_plain_business_models import MODEL_SUMMARIES, simplify
from p412_build_public import RESEARCH_SLUGS

class PlainBusinessModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        for script in ("web/build.py","scripts/release/p412_build_public.py"):
            p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,env=env,
                             text=True,capture_output=True,timeout=60)
            if p.returncode:
                raise AssertionError(p.stderr[-1600:])
        cls.output=ROOT/"web"/"dist"/"research"
        cls.index=(cls.output/"index.html").read_text(encoding="utf8")

    def test_six_readable_cards_before_hidden_old_numbers(self):
        self.assertEqual(set(MODEL_SUMMARIES),set(RESEARCH_SLUGS))
        self.assertEqual(len(MODEL_SUMMARIES),6)
        s=self.index
        self.assertEqual(s.count('class="model-card"'),6)
        self.assertIn("六种生意，先看怎么赚钱",s)
        self.assertIn("不是六个已验证能赚钱的项目",s)
        self.assertLess(s.index('class="model-grid"'),s.index('id="category-comparison"'))
        self.assertLess(s.index('class="model-grid"'),s.index('class="compare-table-v2"'))
        self.assertEqual(s.count('class="model-data-fold"'),1)
        self.assertEqual(s.count('id="category-comparison"'),1)
        self.assertEqual(s.count('class="compare-table-v2"'),1)
        self.assertIn('meta name="robots" content="noindex,follow"',s)
        for slug, summary in MODEL_SUMMARIES.items():
            self.assertIn(f'href="/research/{slug}/"',s)
            self.assertIn(summary["title"],s)
            self.assertIn(summary["charge"],s)

    def test_every_detail_has_business_answer_first_and_every_original_section(self):
        for slug, item in MODEL_SUMMARIES.items():
            with self.subTest(slug=slug):
                s=(self.output/slug/"index.html").read_text(encoding="utf8")
                self.assertIn(item["title"],s)
                self.assertIn(item["what"],s)
                self.assertIn(item["payer"],s)
                self.assertIn(item["charge"],s)
                self.assertIn(item["needs"],s)
                self.assertIn(item["first"],s)
                self.assertEqual(s.count('class="model-facts"'),1)
                self.assertEqual(s.count('class="model-data-fold"'),1)
                self.assertEqual(s.count("<h1>"),1)
                self.assertEqual(s.count('id="historical-stats"'),1)
                self.assertLess(s.index("谁付钱"),s.index('id="historical-stats"'))
                self.assertIn("不代表新项目的收入、利润或实际工作时间",s)
                for required in ('id="sample-scope"','id="sample-metrics"',
                                 'id="sample-examples"','id="sample-boundary"',
                                 "data-freshness-v2","匿名案例",
                                 "noindex,nofollow"):
                    self.assertIn(required,s)
                self.assertIn(f'href="https://jianshi-bua.pages.dev/research/{slug}/"',s)
                self.assertNotIn('href="/opportunity/',s)
                self.assertNotIn("保证收益",s)
                self.assertNotIn("直接复制就能赚钱",s)

    def test_not_form_not_api_not_leaky_or_duplicate(self):
        pages=[self.index]+[(self.output/slug/"index.html").read_text(encoding="utf8")
                            for slug in RESEARCH_SLUGS]
        for s in pages:
            with self.subTest(page=s[:200]):
                self.assertNotIn("<form",s)
                self.assertNotIn("source_ref_ids",s)
                self.assertNotIn("listing_number",s)
                self.assertNotIn("Empire Flippers",s)
                self.assertNotIn("empireflippers",s.lower())
        with self.assertRaises(RuntimeError):
            simplify(self.index,None)
        with self.assertRaises(RuntimeError):
            simplify(self.index,"not-an-approved-business")

    def test_invalid_source_structure_fails_before_publish(self):
        base=(self.output/"agency-business"/"index.html").read_text(encoding="utf8")
        s=base.replace('id="sample-metrics"','id="tampered"')
        with self.assertRaises(RuntimeError):
            simplify(s,"agency-business")
        with self.assertRaises(RuntimeError):
            simplify('<html><head></head><body></body></html>',"agency-business")


if __name__=="__main__":
    unittest.main()
