"""B1 P2: unopened public channels must offer usable local actions, not roadmaps."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from p446_content_hubs import PAGES, render_pages
from f21_g2b_guided_actions import CHECKLISTS, ACADEMY_PLANS
from f21_g2c_related_quality import RELATED


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
        self.related_sections = 0
        self.buttons = []
        self.detail_open = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            self.links.append(a.get("href"))
        if tag == "button":
            self.buttons.append(a)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "section" and "g2c-related" in a.get("class", "").split():
            self.related_sections += 1
        if tag == "details" and "open" in a:
            self.detail_open += 1


class B1P2PublicEmptyStates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = render_pages()

    def test_core_local_actions_are_immediate_and_nontransactional(self):
        cases = {
            "marketplace/": ("/marketplace/brief/", "现在可以做什么？",
                             "商机列表尚未开放", "需求说明应包含的字段", "request-brief"),
            "talent/": ("/talent/portfolio/", "现在可以做什么？",
                        "尚未开放创作者入驻", "作品介绍可以怎么写？", "portfolio"),
            "academy/": ("#learning-paths", "选一个方向，做三项练习",
                         "没有已上线的可播放课程", "g2b-academy-choice", "learning-paths"),
        }
        for route,(action,heading,unavailable,helpful,target) in cases.items():
            with self.subTest(route=route):
                page=self.pages[route]
                scan=Scan()
                scan.feed(page)
                self.assertIn('href="'+action+'"',page)
                self.assertIn(heading,page)
                self.assertIn(unavailable,page)
                self.assertIn(helpful,page)
                self.assertIn(target,scan.ids)
                self.assertEqual(page.count("<main>"),1)
                self.assertEqual(page.count("<script>"),1)
                self.assertEqual(scan.related_sections,1)
                self.assertEqual(scan.detail_open,0)
                self.assertIn("暂时不能在网站上购买服务",page)
                self.assertNotIn('class="kicker"',page)
                self.assertLess(page.index('href="'+action+'"'),page.index('class="g2c-related g2c-related-compact"'))

    def test_marketplace_and_talent_six_checklist_items_remain_in_explicit_fold(self):
        for route,key in (("marketplace/","marketplace"),("talent/","talent")):
            with self.subTest(route=route):
                page=self.pages[route]
                self.assertIn('<details class="guide-more">',page)
                self.assertEqual(page.count('<input type="checkbox"'),len(CHECKLISTS[key]))
                self.assertIn("不存储、不登录、不发送",page)
                self.assertIn("关闭或刷新后内容会消失",page)
                for item in CHECKLISTS[key]:
                    self.assertIn(item,page)
                self.assertIn('data-g2b-reset',page)
                self.assertIn('aria-live="polite"',page)

    def test_academy_uses_one_learning_selector_not_duplicate_five_card_catalog(self):
        page=self.pages["academy/"]
        self.assertEqual(page.count("data-g2b-plan="),len(ACADEMY_PLANS))
        self.assertEqual(page.count('<input type="checkbox"'),15)
        self.assertEqual(page.count('id="g2b-academy-choice"'),1)
        self.assertIn('href="/projects/"',page)
        self.assertNotIn("以后课程会怎么安排",page)
        self.assertNotIn("课程还在准备什么",page)
        self.assertNotIn("计划实战成果：",page)
        self.assertNotIn("在线报名",page.split("<script>")[0].split("没有可播放课程或报名入口")[0])

    def test_related_and_original_pages_retained(self):
        self.assertEqual(set(self.pages),set(PAGES))
        self.assertEqual(len(RELATED),9)
        self.assertEqual(sum(len(v) for v in RELATED.values()),27)
        for route in ("marketplace/","talent/","academy/"):
            page=self.pages[route]
            scan=Scan()
            scan.feed(page)
            self.assertIn('<details><summary>相关内容和下一步</summary>',page)
            for dest,_,_ in RELATED["/"+route]:
                self.assertIn('href="'+dest+'"',page)
            self.assertEqual(len(scan.ids),len(set(scan.ids)))

    def test_no_fake_transactions_or_hidden_network_behavior(self):
        for route in ("marketplace/","talent/","academy/"):
            page=self.pages[route]
            for token in ("立即竞标","正在招聘","立即申请入驻","已成交订单",
                          "已认证设计师","已上线付费课程",
                          "XMLHttpRequest","localStorage","sendBeacon","fetch("):
                self.assertNotIn(token,page,(route,token))
            self.assertIn('rel="canonical"',page)
            self.assertIn('href="/privacy/"',page)


if __name__=="__main__":
    unittest.main()
