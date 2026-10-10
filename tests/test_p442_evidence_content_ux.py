import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "web" / "build.py"

class EvidenceContentNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = dict(os.environ)
        env.pop("JIANSHI_API_URL", None)
        subprocess.run(
            [sys.executable, str(BUILD)],
            cwd=ROOT, env=env, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        cls.home = (ROOT / "web/dist/index.html").read_text(encoding="utf-8")
        cls.catalog = (ROOT / "web/dist/opportunities/index.html").read_text(encoding="utf-8")
        cls.detail = (ROOT / "web/dist/opportunity/vertical-industry-saas/index.html").read_text(encoding="utf-8")

    def test_home_reading_journey_and_catalog_glossary(self):
        self.assertIn("三步读懂一份项目研究档案", self.home)
        self.assertIn('href="/opportunities/#reading-metrics"', self.home)
        self.assertIn('id="research-categories"', self.home)
        self.assertIn('id="reading-metrics"', self.catalog)
        for term in ("项目案例数量", "营收与利润中位数", "细分领域分布", "匿名项目摘要"):
            self.assertIn(term, self.catalog)
        self.assertIn('id="catalog-categories"', self.catalog)

    def test_detail_anchors_and_guardrails(self):
        for anchor in ("sample-scope", "sample-metrics", "sample-examples", "sample-boundary"):
            self.assertIn(f'id="{anchor}"', self.detail)
            self.assertIn(f'href="#{anchor}"', self.detail)
        self.assertIn("当前分类包含 4 个去重项目案例", self.detail)
        self.assertIn("报价样本数量尚未提供", self.detail)
        self.assertIn("逐条金额为区间展示", self.detail)
        self.assertIn("noindex,nofollow", self.detail)

    def test_niche_preview_accepts_only_public_distribution(self):
        spec = importlib.util.spec_from_file_location("jianshi_web_build_p442", BUILD)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        research = {
            "niche_distribution": [
                {"name": "  商业  ", "count": 3},
                {"name": "商业", "count": 1},
                {"name": "科技", "count": 2},
                {"name": "", "count": 4},
                {"name": "教育", "count": 1},
                {"name": "音乐", "count": 1},
            ],
            "china_screening": {"suitable_for": ["不应公开"]},
        }
        self.assertEqual(module._published_niches(research), ["商业", "科技", "教育"])
        self.assertNotIn("不应公开", module.prototype_card({
            "slug": "fixture", "title": "测试类别",
            "overseas_validation": {"direct_samples": 0},
        }))

    def test_public_content_keeps_evidence_only_contract(self):
        for page in (self.home, self.catalog, self.detail):
            for forbidden in (
                "优先研究", "值得研究", "一人公司适配", "为什么推荐",
                "适合谁", "不太适合谁", "第一轮怎么验证",
                "Empire Flippers", "empireflippers.com", "listing_number",
            ):
                self.assertNotIn(forbidden, page)

if __name__ == "__main__":
    unittest.main()
