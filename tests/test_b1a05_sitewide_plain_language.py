"""Sitewide public language acceptance: users see business answers, not internal stages.

The test inspects actual Python-rendered public HTML, not a sample screenshot.
It intentionally doesn't treat engineering sources as user-facing content.
"""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from p423_build_project_proofs import project_page,parse_cases,index_page
from p425_public_admission import eligible_cases
from p445_unified_home import build_home
from p446_content_hubs import render_pages
from p448_v2_local_drafts import render_one,PAGES as DRAFT_PAGES

class HumanText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden=0
        self.visible=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","head"):
            self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","head") and self.hidden:
            self.hidden-=1
    def handle_data(self,data):
        if self.hidden==0 and data.strip():
            self.visible.append(data.strip())

def displayed(html):
    p=HumanText()
    p.feed(html)
    return " ".join(p.visible)


class SitewidePlainLanguage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=eligible_cases(parse_cases())
        cls.pages={"/":build_home(cls.cases),"/projects/":index_page(cls.cases)}
        cls.pages.update({"/projects/"+c["id"]+"/":project_page(c) for c in cls.cases})
        cls.pages.update({"/"+k:v for k,v in render_pages().items()})
        cls.pages.update({"/"+k:render_one(k) for k in DRAFT_PAGES})

    def test_no_internal_release_or_english_stage_labels_visible(self):
        forbidden=("CONTENT / EDITORIAL","DECISION FILE","FOUNDER WORKBOOK",
                   "PAIN POINT","GOOD FIT","QUALITY GATE","CURRICULUM PLAN",
                   "DELIVERY PROCESS","SOLUTION CATALOG","L3 ·","L4 ·",
                   "OPP_V0.2","P4.41","Fail Closed")
        for route,page in self.pages.items():
            with self.subTest(route=route):
                text=displayed(page)
                for token in forbidden:
                    self.assertNotIn(token,text)

    def test_named_dossiers_start_with_business_answers_before_methodology(self):
        for c in self.cases:
            with self.subTest(slug=c["id"]):
                page=self.pages["/projects/"+c["id"]+"/"]
                self.assertLess(page.index('aria-label="项目概况"'),
                                page.index('id="decision-report"'))
                self.assertIn("30 秒看懂这门生意",page)
                self.assertIn("查看原始经营依据",page)
                self.assertIn("照着做也能赚钱",page)
                self.assertIn("不是投资建议、收益预测",page)
        directory=self.pages["/projects/"]
        self.assertIn("谁在用：",directory)
        self.assertIn("谁付钱：",directory)
        self.assertIn("怎么赚钱：",directory)
        self.assertIn("不是赚钱排名",directory)

    def test_solution_pages_communicate_user_actions_and_still_mark_unreleased(self):
        directory=self.pages["/solutions/"]
        self.assertIn("选一个业务问题",directory)
        self.assertIn("暂时不能在网站上购买服务",directory)
        self.assertEqual(directory.count('class="card link"'),4)
        for page in self.pages.values():
            self.assertNotIn("保证赚到钱",displayed(page))
        for route in ("/marketplace/","/talent/","/academy/"):
            self.assertIn("暂时不能在网站上购买服务",self.pages[route])
        for route in ("/marketplace/brief/","/talent/portfolio/"):
            self.assertIn("关闭或刷新页面后内容会消失",self.pages[route])

    def test_evidence_and_private_safety_gates_stay_unchanged(self):
        self.assertEqual({c["id"] for c in self.cases},{"nerdwallet","plausible","carrd"})
        self.assertEqual(len(self.pages),15)
        for c in self.cases:
            page=self.pages["/projects/"+c["id"]+"/"]
            self.assertIn(c["research_evidence"]["source_url"],page)
        workflow=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(workflow.count("cron: '55 0 * * *'"),1)
        self.assertEqual(workflow.count("cron: '55 6,12,18 * * *'"),1)
        self.assertIn('JIANSHI_AUTH_ENABLED: "0"',workflow)

if __name__=="__main__":
    unittest.main()
