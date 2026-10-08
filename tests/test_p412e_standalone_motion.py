"""P4.12E — Ethan Vale template preservation and privacy guardrail."""
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/"web"/"prototypes"/"p412e"/"index.html"

class TemplateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if "id" in a:self.ids.append(a["id"])
        if tag in {"link","script"}:self.links.append((tag,a))

class TestP412EStandaloneMotionTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=PAGE.read_text(encoding="utf-8")
        cls.parser=TemplateParser()
        cls.parser.feed(cls.html)

    def test_one_self_contained_document(self):
        self.assertTrue(cls_placeholder := self.html.strip().endswith("</html>"))
        self.assertEqual(self.html.count("<style>"),1)
        self.assertEqual(self.html.count("</style>"),1)
        self.assertEqual(self.html.count("<script>"),1)
        self.assertEqual(self.html.count("</script>"),1)
        self.assertEqual(len(self.parser.ids),len(set(self.parser.ids)))
        self.assertEqual(self.html.count("data:image/webp;base64,"),8)
        self.assertLess(len(self.html.encode("utf-8")),450000)
        self.assertNotIn("snow-leopard.jpg",self.html)
        self.assertNotIn("ethanvale.com",self.html.lower())

    def test_original_visual_contract(self):
        for text in [
            "--bg:#000","--ink:#f4f2ef","--pad:clamp(14px,2.6vw,34px)",
            "--persp:1150px","Playfair+Display","family=Inter",
            'class="splash"','class="top"','class="menu"',
            'class="stage"','class="ring"','id="grid"',
            'class="lb"','id="lbImg"','id="lbFig"',
            "IntersectionObserver","requestAnimationFrame",
            "prefers-reduced-motion","100dvh",
            "safe-area-inset-top","safe-area-inset-bottom",
            'viewport-fit=cover'
        ]:
            self.assertIn(text,self.html)
        external_styles=[
            (tag,attrs) for tag,attrs in self.parser.links
            if tag=="link" and attrs.get("rel")=="stylesheet"
        ]
        self.assertEqual(len(external_styles),1)
        self.assertIn("fonts.googleapis.com",external_styles[0][1]["href"])
        self.assertFalse(any(tag=="script" and "src" in attrs for tag,attrs in self.parser.links))

    def test_animation_and_lightbox_navigation(self):
        for text in [
            "function openLb(index,filtered)",
            "lightboxOrder=filtered?tiles.filter",
            "function stepLb(delta)",
            "if(!lbOpen||reduced){draw();return}",
            "function layout()",
            "function renderRing()",
            "function endDrag",
            "pointerdown","pointermove","touchstart","touchend",
            "ArrowRight","ArrowLeft","Escape",
            "function keepFocus",
            "history.pushState",
            "function routeItemFromHash"
        ]:self.assertIn(text,self.html)

    def test_discovery_handlers_not_attached_to_content_cards(self):
        expected="document.querySelectorAll('.find__filters [data-kind]')"
        self.assertEqual(self.html.count(expected),2)
        self.assertNotIn("document.querySelectorAll('[data-kind]')",self.html)
        self.assertIn('id="searchInput"',self.html)
        self.assertIn('id="searchEmpty"',self.html)
        self.assertIn('id="compareChoices"',self.html)
        self.assertIn("picked.size>=3",self.html)
        self.assertIn("tile.hidden=!show",self.html)

    def test_public_content_is_not_source_inventory(self):
        for secret in [
            "Empire Flippers","empireflippers","listing_number",
            "source_url","source_ref_ids","OFFICIAL_API","OPP_V0.2",
            "EASLO_OWN_SITE_01","LENNOX_AMAZON_02","源更新时间",
            "真实月入","保证收益","预计利润率"
        ]:
            self.assertNotIn(secret,self.html)
        for visible in [
            "见势 JIANSHI","Easlo","Louise Lennox",
            "行业软件订阅","亚马逊数字出版","跨境电商品牌","专业服务",
            "实际销量","商业模式","联系我们"
        ]:self.assertIn(visible,self.html)

    def test_javascript_syntax(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node unavailable")
        code=self.html.split("<script>",1)[1].split("</script>",1)[0]
        run=subprocess.run([node,"--check","-"],input=code,text=True,
                           capture_output=True,timeout=25)
        self.assertEqual(run.returncode,0,run.stderr)

if __name__=="__main__":
    unittest.main()
