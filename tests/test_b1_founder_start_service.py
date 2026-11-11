"""B1 public self-service: research guidance must be real and fail-closed."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"release"))
from p450_founder_start import (render,publish,model_payload,MODEL_SUMMARIES,
                               WARNINGS,SKILL_ORDER,ALLOWED_MODELS,SCRIPT)
from p445_unified_home import build_home
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.selects=[]
        self.forms=0
        self.h1=0
        self.inputs=0
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="a":self.links.append(a.get("href"))
        if tag=="select":self.selects.append(a.get("id"))
        if tag=="input":self.inputs+=1
        if tag=="form":self.forms+=1
        if tag=="h1":self.h1+=1
        if a.get("id"):self.ids.append(a["id"])


class FounderStartTests(unittest.TestCase):
    def test_only_six_existing_approved_business_models(self):
        self.assertEqual(len(MODEL_SUMMARIES),6)
        self.assertEqual(set(ALLOWED_MODELS),set(MODEL_SUMMARIES))
        self.assertEqual(set(WARNINGS),set(MODEL_SUMMARIES))
        for row in SKILL_ORDER.values():
            self.assertEqual(len(row),6)
            self.assertEqual(set(row),set(ALLOWED_MODELS))
        payload=model_payload()
        for key in ALLOWED_MODELS:
            self.assertIn(MODEL_SUMMARIES[key]["title"],payload)
            self.assertIn(MODEL_SUMMARIES[key]["first"],payload)

    def test_real_three_question_interface_local_and_no_users(self):
        html=render()
        s=Scan();s.feed(html)
        self.assertEqual(s.h1,1)
        self.assertEqual(s.forms,0)
        self.assertEqual(s.inputs,0)
        self.assertEqual(len(s.ids),len(set(s.ids)))
        self.assertEqual(set(s.selects),{"service-skill","service-preference","service-resource"})
        for button in ("service-demo","service-generate","service-copy","service-reset"):
            self.assertIn('id="'+button+'"',html)
        self.assertIn("体验一个示例",html)
        self.assertIn("不是 AI 收益预测",html)
        self.assertIn("按预设的公开编辑规则排序",html)
        self.assertIn('role="status" aria-live="polite"',html)
        self.assertIn('id="service-result" hidden',html)
        self.assertIn('id="service-copy" disabled',html)
        self.assertIn('href="/discover/"',html)
        self.assertIn('href="/projects/"',html)
        self.assertIn('href="/research/"',html)
        self.assertIn('href="/sources/"',html)
        self.assertIn('type="application/json" id="service-models"',html)
        self.assertIn('output.hidden=!visible',SCRIPT)
        self.assertIn("navigator.clipboard.writeText",SCRIPT)
        self.assertIn('textContent=text',SCRIPT)
        self.assertNotIn("innerHTML",html)
        for dangerous in ('<form','type="email"','fetch(','XMLHttpRequest','sendBeacon',
                          'localStorage','sessionStorage','indexedDB','WebSocket',
                          '数据已上传','保证收益','稳赚','注册并领取'):
            self.assertNotIn(dangerous,html)

    def test_offline_release_generates_exactly_one_real_page(self):
        with TemporaryDirectory() as td:
            result=publish(Path(td))
            page=Path(td)/"start/index.html"
            self.assertEqual(result,1)
            self.assertTrue(page.exists())
            self.assertIn("生成我的研究卡",page.read_text(encoding="utf-8"))
            self.assertFalse((Path(td)/"account").exists())

    def test_home_entry_leads_to_real_service_without_replacing_projects(self):
        html=build_home(eligible_cases(parse_cases()))
        self.assertIn('class="j2-first-service" href="/start/"',html)
        self.assertIn('href="/projects/">先看项目 →',html)
        self.assertEqual(html.count("<main "),1)
        self.assertEqual(html.count("<script>"),1)
        self.assertNotIn('type="email"',html)


if __name__=="__main__":
    unittest.main()
