import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestP42FrontendProductization(unittest.TestCase):
    def test_product_positioning_and_catalog_contract(self):
        build = (ROOT / "web" / "build.py").read_text(encoding="utf-8")
        self.assertIn("公开商业数据研究工具", build)
        self.assertIn("项目研究库", build)
        self.assertIn("样本纳入规则", build)
        self.assertIn("证据边界", build)
        self.assertIn("def build_opportunities_page", build)
        self.assertIn('"/opportunities/"', build)


    def test_public_detail_is_evidence_first(self):
        build = (ROOT / "web" / "build.py").read_text(encoding="utf-8")
        for token in [
            "MARKET EVIDENCE BRIEF",
            "样本纳入规则",
            "挂牌样本摘要",
            "OBSERVED LISTINGS",
            "证据边界",
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
        self.assertIn('grep -q "先看证据" index.html', workflow)
        self.assertIn('grep -q "项目研究库" opportunities/index.html', workflow)
        self.assertIn('grep -q "SYSTEM SIGNAL PROFILE" opportunity/solo-saas/index.html', workflow)
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
        self.assertIn("项目研究库", html)
        self.assertIn("公开商业挂牌样本", html)
        self.assertIn("当前证据边界", html)


if __name__ == "__main__":
    unittest.main()
