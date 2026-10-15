"""B1 founder-first homepage: isolated, source-constrained release contract tests.

All samples are existing, independently source-admitted named cases.
This does not simulate real customer interviews, traffic or PMF.
"""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))

import p442_jianshi2_live_home as portal
import p445_unified_home as home
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors=[]
        self.forms=0
        self.scripts=0
        self.inputs=0
        self.ids=[]
        self.headers=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="a":self.anchors.append(a.get("href"))
        if tag=="form":self.forms+=1
        if tag=="input":self.inputs+=1
        if tag=="script":self.scripts+=1
        if a.get("id"):self.ids.append(a["id"])
        if tag=="h1":self.headers.append(tag)


class TestB1FounderResearchJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=eligible_cases(parse_cases())
        cls.rendered=home.build_home(cls.cases)
        cls.parsed=Elements()
        cls.parsed.feed(cls.rendered)

    def test_primary_user_sees_founder_explanation_and_only_one_hero(self):
        self.assertEqual(self.rendered.count("<h1>"),1)
        self.assertIn("想找个项目做？",self.rendered)
        self.assertIn("发现值得研究的",self.rendered)
        self.assertIn("商业机会。</em>",self.rendered)
        self.assertIn("不仅研究 AI",self.rendered)
        self.assertIn("直接看项目 ↓",self.rendered)
        self.assertLess(
            self.rendered.index('href="#j2-opportunities"'),
            self.rendered.index('href="#j2-solutions"')
        )
        self.assertIn("<title>见势｜找创业项目，看懂怎么赚钱</title>",self.rendered)
        self.assertIn('property="og:title"',self.rendered)

    def test_study_paths_are_real_public_destinations_and_usable_without_auth(self):
        html=self.rendered
        self.assertEqual(html.count('class="j2-study-path"'),3)
        for label,path in (("找真实案例","/projects/"),
                           ("比较商业模式","/research/"),
                           ("按主题探索","/discover/")):
            self.assertIn(label,html)
            self.assertIn('href="'+path+'"',html)
            self.assertIn(path,self.parsed.anchors)
        self.assertNotIn('type="email"',html)
        self.assertEqual(self.parsed.forms,0)
        self.assertEqual(self.parsed.inputs,0)
        self.assertEqual(self.parsed.scripts,1)
        self.assertEqual(len(self.parsed.ids),len(set(self.parsed.ids)))
        for script_marker in ("navigator.sendBeacon","localStorage.setItem",
                              "sessionStorage.setItem","fetch(","XMLHttpRequest("):
            self.assertNotIn(script_marker,html)

    def test_all_named_cases_are_short_revenue_first_cards(self):
        self.assertEqual(set(portal.PROJECT_PREVIEWS),set(portal.CASES))
        self.assertEqual({c["id"] for c in self.cases},set(portal.CASES))
        self.assertEqual(self.rendered.count('class="j2-project-facts"'),3)
        self.assertEqual(self.rendered.count('class="j2-project-action"'),3)
        self.assertEqual(self.rendered.count('class="j2-project-action" href="/projects/"'),3)
        for case in self.cases:
            slug=case["id"]
            preview=portal.PROJECT_PREVIEWS[slug]
            for field in ("headline","buyer","revenue","difficulty","label"):
                self.assertIn(preview[field],self.rendered)
            self.assertNotIn('href="/projects/'+slug+'/"',self.rendered)
        for label in ("谁需要","怎么赚钱","上手门槛"):
            self.assertEqual(self.rendered.count('<dt>'+label+'</dt>'),3)
        self.assertNotIn('class="j2-research-check"',self.rendered)
        self.assertLess(self.rendered.index('class="j2-projects"'),
                        self.rendered.index('class="j2-study-paths"'))
        self.assertLess(self.rendered.index('class="j2-projects"'),
                        self.rendered.index('class="j2-shortcuts"'))

    def test_research_never_claims_proven_entrepreneurial_return_or_users(self):
        for bad in ("保证赚钱","保证收益","已有 500 家企业",
                    "10,000+","立即竞标","已验证可以直接启动"):
            self.assertNotIn(bad,self.rendered)
        self.assertIn("历史案例不代表照着做就能赚钱",self.rendered)
        self.assertIn("概念配图不是项目证明",self.rendered)
        self.assertIn("尚未开放真实服务采购",self.rendered)
        self.assertIn("<strong>0</strong><span>已验证可直接启动的项目",self.rendered)

    def test_original_five_routes_protected_and_enterprise_secondary(self):
        for anchor in ("j2-opportunities","j2-solutions","j2-marketplace",
                       "j2-talent","j2-academy"):
            self.assertEqual(self.rendered.count('id="'+anchor+'"'),1)
            self.assertIn('href="#'+anchor+'"',self.rendered)
        self.assertLess(self.rendered.index("现在可以看的创业案例"),
                        self.rendered.index("企业 AI 方案、合作与学习"))
        self.assertLess(self.rendered.index('id="j2-opportunities"'),
                        self.rendered.index('id="j2-solutions"'))

    def test_only_source_admitted_three_cases_can_appear(self):
        with self.assertRaises(RuntimeError):
            home.build_home(self.cases[:2])
        test=portal.PROJECT_PREVIEWS.copy()
        try:
            with patch.dict(portal.PROJECT_PREVIEWS,{"carrd":{
                    **portal.PROJECT_PREVIEWS["carrd"],
                    "headline":'<img onerror=alert(1)>'
                }},clear=False):
                unsafe=home.build_home(self.cases)
            self.assertNotIn('<img onerror=alert(1)>',unsafe)
            self.assertIn('&lt;img onerror=alert(1)&gt;',unsafe)
        finally:
            self.assertEqual(portal.PROJECT_PREVIEWS,test)

    def test_static_publication_and_p441_schedule_unchanged(self):
        self.assertEqual(self.rendered.count("<main "),1)
        self.assertEqual(self.rendered.count("data:image/webp;base64,"),1)
        self.assertLess(len(self.rendered.encode("utf8")),200000)
        workflow=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf8")
        self.assertEqual(workflow.count("cron: '55 0 * * *'"),1)
        self.assertEqual(workflow.count("cron: '55 6,12,18 * * *'"),1)
        self.assertIn('JIANSHI_AUTH_ENABLED: "0"',workflow)


if __name__=="__main__":
    unittest.main()
