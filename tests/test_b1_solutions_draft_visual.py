"""B1 visual: editorial solutions and zero-upload drafts retain all contracts."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"release"))
from p446_content_hubs import SOLUTIONS, CARD_PREVIEWS, B1_SOLUTIONS_VISUAL_CSS, render_pages
from p448_v2_local_drafts import B1_DRAFT_VISUAL_CSS, SCRIPT, SPEC, PAGES, render_one


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1=0
        self.forms=0
        self.fields=[]
        self.links=[]
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="h1":self.h1+=1
        if tag=="form":self.forms+=1
        if tag=="textarea":self.fields.append(a)
        if tag=="a":self.links.append(a.get("href"))
        if a.get("id"):self.ids.append(a["id"])


class B1VisualContinuity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solutions=render_pages()

    def test_all_four_static_solution_cards_inherit_new_design_without_claims(self):
        page=self.solutions["solutions/"]
        self.assertEqual(page.count('class="solution-icon"'),4)
        self.assertEqual(page.count('class="card link"'),4)
        self.assertIn('class="solution-journey"',page)
        self.assertIn("选业务问题",page)
        self.assertIn("先小范围测试",page)
        self.assertIn(".solution-hero:after",page)
        self.assertIn(".f21-catalog-grid .card.link:focus-visible",page)
        self.assertIn("@media(max-width:650px)",B1_SOLUTIONS_VISUAL_CSS)
        for row in SOLUTIONS:
            self.assertIn('/solutions/'+row["slug"]+'/',page)
            self.assertIn(CARD_PREVIEWS[row["slug"]]["risk"],page)
        self.assertIn('id="f21-search"',page)
        self.assertIn('id="f21-reset" hidden',page)
        self.assertIn("暂时不能在网站上购买服务",page)
        for misleading in ("立即下单","成功客户案例","成交订单","保证效果"):
            self.assertNotIn(misleading,page)

    def test_detail_safety_and_real_actions_unchanged(self):
        for row in SOLUTIONS:
            page=self.solutions["solutions/"+row["slug"]+"/"]
            with self.subTest(row=row["slug"]):
                self.assertIn('class="solution-journey"',page)
                self.assertIn('class="wrap content solution-detail-guide"',page)
                self.assertIn('id="delivery"',page)
                self.assertIn('class="solution-technical"',page)
                self.assertIn(row["boundary"],page)
                self.assertIn('href="/marketplace/brief/"',page)
                self.assertIn('href="/solutions/"',page)
                self.assertNotIn("<form",page)
                scan=Scan()
                scan.feed(page)
                self.assertEqual(scan.h1,1)

    def test_local_editors_seven_scoped_inputs_dynamic_progress(self):
        self.assertEqual(len(PAGES),2)
        for route in PAGES:
            page=render_one(route)
            scan=Scan()
            scan.feed(page)
            with self.subTest(route=route):
                self.assertEqual(scan.h1,1)
                self.assertEqual(len(scan.fields),7)
                self.assertEqual(scan.forms,0)
                self.assertEqual(len(scan.ids),len(set(scan.ids)))
                self.assertIn('class="hero tool-hero"',page)
                self.assertIn('class="draft-hero-badges"',page)
                self.assertIn("不上传数据",page)
                self.assertIn('class="tool-fields"',page)
                self.assertIn('id="draft-progress-bar"',page)
                self.assertIn('data-placeholder=',page)
                self.assertIn(".tool-preview:empty::before",page)
                self.assertIn(".tool-layout>.tool-panel:last-child",page)
                self.assertIn("关闭或刷新页面后内容会消失",page)
                self.assertIn(SPEC[route]["back"],scan.links)
                self.assertIn("progressBar.style.width",SCRIPT)
                for forbidden in ("<form","fetch(","XMLHttpRequest","sendBeacon",
                                  "WebSocket","localStorage","sessionStorage","indexedDB",
                                  "action=","type=\"email\""):
                    self.assertNotIn(forbidden,page)

    def test_reduced_motion_and_no_external_design_dependencies(self):
        self.assertIn("prefers-reduced-motion:reduce",B1_SOLUTIONS_VISUAL_CSS)
        self.assertIn("prefers-reduced-motion:reduce",B1_DRAFT_VISUAL_CSS)
        for bad in ("@import","url(http","<iframe","<video","motionsites.ai"):
            self.assertNotIn(bad,B1_DRAFT_VISUAL_CSS+B1_SOLUTIONS_VISUAL_CSS)


if __name__=="__main__":
    unittest.main()
