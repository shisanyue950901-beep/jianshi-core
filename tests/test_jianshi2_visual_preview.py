"""JIANSHI 2.0 F1 visual preview contracts; production pipeline stays isolated."""
import base64
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "web/prototypes/jianshi2-v1/index.html"
WORKFLOW = ROOT / ".github/workflows/publish-static.yml"


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.anchors = []
        self.images = []
        self.forms = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            self.anchors.append(a.get("href", ""))
        if tag == "img":
            self.images.append(a)
        if tag == "form":
            self.forms.append(a)


class VisualPreviewContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PREVIEW.read_text(encoding="utf-8")
        cls.nodes = Elements()
        cls.nodes.feed(cls.html)

    def test_preview_isolated_from_live_build(self):
        self.assertIn("非生产环境", self.html)
        self.assertIn("暂未开放真实提交", self.html)
        self.assertIn("web/prototypes/jianshi2-v1", str(PREVIEW))
        self.assertIn("scripts/release/p412_build_public.py", 
            (ROOT / "docs/JIANSHI2_F1_PRODUCT_UI_FREEZE_20261011.md").read_text())
        self.assertIn("cron: '55 0 * * *'", WORKFLOW.read_text())

    def test_original_generated_artwork_is_self_contained(self):
        self.assertEqual(len(self.nodes.images), 1)
        image = self.nodes.images[0]
        self.assertTrue(image["src"].startswith("data:image/webp;base64,"))
        data = base64.b64decode(image["src"].split(",", 1)[1], validate=True)
        self.assertEqual(data[:4], b"RIFF")
        self.assertEqual(data[8:12], b"WEBP")
        self.assertLess(len(data), 100_000)
        self.assertIn("概念主视觉", image["alt"])
        self.assertIn("非真实项目案例", image["alt"])

    def test_five_module_anchors_and_usable_mobile_menu(self):
        expected = {"opportunities", "solutions", "marketplace", "talent", "academy"}
        self.assertTrue(expected.issubset(self.nodes.ids))
        self.assertTrue(expected.issubset({
            link[1:] for link in self.nodes.anchors if link.startswith("#")}))
        self.assertIn('aria-controls="menu"', self.html)
        self.assertIn("aria-expanded=", self.html)
        self.assertIn("e.key==='Escape'", self.html)
        self.assertIn("@media(max-width:760px)", self.html)

    def test_reduced_motion_and_search_are_accessible(self):
        self.assertIn("prefers-reduced-motion:reduce", self.html)
        self.assertIn("[hidden]{display:none!important}", self.html)
        self.assertIn("IntersectionObserver", self.html)
        self.assertIn('role="status"', self.html)
        self.assertIn('type="search"', self.html)
        self.assertEqual(len(self.nodes.forms), 1)
        self.assertEqual(self.nodes.forms[0].get("id"), "searchForm")
        self.assertNotIn("action=", self.html)
        self.assertNotIn("method=\"post\"", self.html)

    def test_unreleased_services_have_empty_states_and_no_unsafe_fake_data(self):
        for phrase in ("真实商单正在筹备中", "课程体系先预留",
                       "不展示虚构", "没有开放真实入驻", "方向示意"):
            self.assertIn(phrase, self.html)
        for unsafe in ("10,000+", "2,500+", "已有客户", "成交金额",
                       "月收入保证", "真实客户案例已验证"):
            self.assertNotIn(unsafe, self.html)
        self.assertNotIn("https://super-i.cn", self.html)

    def test_public_examples_are_existing_audited_references_only(self):
        for name in ("Carrd", "Plausible", "NerdWallet"):
            self.assertIn(name, self.html)
        self.assertEqual(self.html.count('class="project"'), 3)
        self.assertIn("https://jianshi-bua.pages.dev/research/", self.html)
        self.assertNotIn('src="/docs/', self.html)
        self.assertNotIn('src="/config/', self.html)
        self.assertNotIn("GITHUB_TOKEN", self.html)


if __name__ == "__main__":
    unittest.main()
