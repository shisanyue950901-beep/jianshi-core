import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestP42FrontendProductization(unittest.TestCase):
    def test_product_positioning_and_catalog_contract(self):
        build = (ROOT / "web" / "build.py").read_text(encoding="utf-8")
        self.assertIn("商业机会发现与决策平台", build)
        self.assertIn("海外已验证项目 · 中文筛选", build)
        self.assertIn("低成本验证", build)
        self.assertIn("def build_opportunities_page", build)
        self.assertIn('"/opportunities/"', build)
        self.assertIn("值得深入研究", build)
        self.assertIn("值得验证", build)
        self.assertIn("尚未完成编辑审查", build)

    def test_detail_has_six_layers(self):
        build = (ROOT / "web" / "build.py").read_text(encoding="utf-8")
        for token in [
            "01 · 决策摘要",
            "02 · 机会说明",
            "03 · 商业验证",
            "04 · 执行判断",
            "05 · 内容机会",
            "06 · 证据与来源",
        ]:
            self.assertIn(token, build)

    def test_catalog_filter_client(self):
        js = (ROOT / "web" / "static" / "search.js").read_text(encoding="utf-8")
        self.assertIn("data-catalog-search", js)
        self.assertIn("data-catalog-filter", js)
        self.assertIn("card.dataset.state", js)

    def test_static_snapshot_workflow_tracks_p42_artifacts(self):
        workflow = (ROOT / ".github" / "workflows" / "publish-static.yml").read_text(encoding="utf-8")
        self.assertIn("opportunities/**", workflow)
        self.assertIn("test -f opportunities/index.html", workflow)
        self.assertIn('grep -q "海外已验证项目 · 中文筛选" index.html', workflow)
        self.assertIn('grep -q "首批项目研究" opportunities/index.html', workflow)
        self.assertIn('grep -q "01 · 决策摘要" opportunity/solo-saas/index.html', workflow)
        self.assertIn("opportunity opportunities today", workflow)

    def test_fixture_build_emits_opportunities_page(self):
        env = os.environ.copy()
        env.pop("JIANSHI_API_URL", None)
        subprocess.run(
            ["python", "web/build.py"],
            cwd=ROOT,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out = ROOT / "web" / "dist" / "opportunities" / "index.html"
        self.assertTrue(out.exists())
        html = out.read_text(encoding="utf-8")
        self.assertIn("先看海外已经真实存在的项目", html)
        self.assertIn("首批项目研究", html)
        self.assertIn("趋势方向 · 辅助观察", html)


if __name__ == "__main__":
    unittest.main()
