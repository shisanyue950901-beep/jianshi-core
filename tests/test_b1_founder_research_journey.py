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
        self.assertIn("个人创业机会发现与决策",self.rendered)
        self.assertIn("发现值得研究的",self.rendered)
        self.assertIn("商业机会。</em>",self.rendered)
        self.assertIn("不仅研究 AI",self.rendered)
        self.assertIn("面向个人创业者",self.rendered)
        self.assertLess(
            self.rendered.index('href="#j2-opportunities"'),
            self.rendered.index('href="#j2-solutions"')
        )
        self.assertIn("<title>见势 JIANSHI 2.0｜个人创业机会发现与商业研究</title>",self.rendered)
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
        self.assertIn("不要求注册",html)
        self.assertEqual(self.parsed.forms,0)
        self.assertEqual(self.parsed.inputs,0)
        self.assertEqual(self.parsed.scripts,1)
        self.assertEqual(len(self.parsed.ids),len(set(self.parsed.ids)))
        for script_marker in ("navigator.sendBeacon","localStorage.setItem",
                              "sessionStorage.setItem","fetch(","XMLHttpRequest("):
            self.assertNotIn(script_marker,html)

    def test_all_named_cases_have_a_question_gap_and_research_step(self):
        self.assertEqual(set(portal.RESEARCH_QUESTIONS),set(portal.CASES))
        self.assertEqual({c["id"] for c in self.cases},set(portal.CASES))
        self.assertEqual(self.rendered.count('class="j2-research-check"'),3)
        for case in self.cases:
            slug=case["id"]
            q=portal.RESEARCH_QUESTIONS[slug]
            self.assertEqual(len(q),3)
            for sentence in q:
                self.assertGreater(len(sentence),18)
                self.assertIn(sentence,self.rendered)
            self.assertIn('href="/projects/'+slug+'/"',self.rendered)
        for text in ("先研究什么","哪些问题还不知道","可以怎样开始核实"):
            self.assertEqual(self.rendered.count(text),3)

    def test_research_never_claims_proven_entrepreneurial_return_or_users(self):
        for bad in ("保证赚钱","保证收益","已有 500 家企业",
                    "10,000+","立即竞标","已验证可以直接启动"):
            self.assertNotIn(bad,self.rendered)
        self.assertIn("历史经营不代表可复制收益",self.rendered)
        self.assertIn("概念配图不是项目证明",self.rendered)
        self.assertIn("尚未开放真实服务采购",self.rendered)
        self.assertIn("<strong>0</strong><span>已验证可直接启动的项目",self.rendered)

    def test_original_five_routes_protected_and_enterprise_secondary(self):
        for anchor in ("j2-opportunities","j2-solutions","j2-marketplace",
                       "j2-talent","j2-academy"):
            self.assertEqual(self.rendered.count('id="'+anchor+'"'),1)
            self.assertIn('href="#'+anchor+'"',self.rendered)
        self.assertLess(self.rendered.index("找项目，先从可信的研究开始。"),
                        self.rendered.index("从商业机会研究，延伸到企业 AI 应用。"))
        self.assertLess(self.rendered.index('id="j2-opportunities"'),
                        self.rendered.index('id="j2-solutions"'))

    def test_only_source_admitted_three_cases_can_appear(self):
        with self.assertRaises(RuntimeError):
            home.build_home(self.cases[:2])
        test=portal.RESEARCH_QUESTIONS.copy()
        try:
            with patch.dict(portal.RESEARCH_QUESTIONS,{"carrd":("<img onerror=alert(1)>","需核实","不确定")},clear=False):
                unsafe=home.build_home(self.cases)
            self.assertNotIn("<img onerror=alert(1)>",unsafe)
            self.assertIn("&lt;img onerror=alert(1)&gt;",unsafe)
        finally:
            self.assertEqual(portal.RESEARCH_QUESTIONS,test)

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
