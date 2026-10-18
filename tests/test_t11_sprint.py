#!/usr/bin/env python3
"""T11 static sprint contract, source transparency, URL gate, copy safety."""
from __future__ import annotations
import json
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"release"))
from t11_sprint import PROVIDERS, _form_url, publish, render_sprint

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.buttons=[]
        self.scripts=[]
        self.provider_rows=[]
        self.checkbox_ids=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=="a":self.links.append(d)
        if tag=="button":self.buttons.append(d)
        if tag=="script" and "src" in d:self.scripts.append(d["src"])
        if tag=="input" and "data-t11-check" in d:self.checkbox_ids.append(d["data-t11-check"])
        if tag=="tr" and "data-t11-provider" in d:self.provider_rows.append(d["data-t11-provider"])

class TestT11Sprint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markup=render_sprint("")
        cls.page=PageParser()
        cls.page.feed(cls.markup)
    def test_render_and_build_path(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            cfg=out/"site.json"
            cfg.write_text('{"diagnose_form_url":""}',encoding="utf-8")
            dest=publish(out,config_file=cfg)
            self.assertEqual(dest,out/"sprint"/"index.html")
            self.assertTrue(dest.is_file())
            self.assertIn('<link rel="canonical" href="https://jianshi-bua.pages.dev/sprint/">',dest.read_text(encoding="utf-8"))
        dist=ROOT/"web"/"dist"/"sprint"/"index.html"
        if dist.exists():self.assertIn("冲刺目标",dist.read_text(encoding="utf-8"))
    def test_blank_cta_is_not_link(self):
        self.assertEqual(json.loads((ROOT/"config"/"site.json").read_text(encoding="utf-8"))["diagnose_form_url"],"")
        self.assertFalse(any("data-t11-diagnose" in a for a in self.page.links))
        self.assertTrue(any("disabled" in b and b.get("aria-disabled")=="true" for b in self.page.buttons))
        self.assertIn("表单即将开放",self.markup)
    def test_official_url_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"site.json"
            for bad in ("http://feishu.cn/form/a","https://evil.example/form","javascript:alert(1)","https://feishu.cn.evil.test/"):
                path.write_text(json.dumps({"diagnose_form_url":bad}),encoding="utf-8")
                with self.assertRaises(ValueError):_form_url(path)
            official="https://www.feishu.cn/share/base/form/shrABC"
            path.write_text(json.dumps({"diagnose_form_url":official}),encoding="utf-8")
            self.assertEqual(_form_url(path),official)
            enabled=render_sprint(official)
            self.assertIn('data-t11-diagnose',enabled)
            self.assertIn('rel="noopener noreferrer"',enabled)
            self.assertNotIn("表单即将开放",enabled)
    def test_payment_table_sources_dates_and_rates(self):
        self.assertEqual(self.page.provider_rows,["Creem","Dodo Payments","Waffo Pancake"])
        self.assertEqual(len(PROVIDERS),3)
        for p in PROVIDERS:
            with self.subTest(provider=p["name"]):
                self.assertIn('data-t11-provider="'+p["name"]+'"',self.markup)
                self.assertTrue(p["sources"])
                for _,url in p["sources"]:
                    self.assertTrue(url.startswith("https://"))
                    self.assertIn('href="'+url+'"',self.markup)
                self.assertIn("2026-10-18",self.markup)
        for fee in ("3.9% + $0.40","4% + $0.40","3.9% + $0.50"):
            self.assertIn(fee,self.markup)
    def test_all_checkboxes_only_use_localstorage(self):
        self.assertEqual(len(self.page.checkbox_ids),len(set(self.page.checkbox_ids)))
        self.assertGreaterEqual(len(self.page.checkbox_ids),12)
        js=(ROOT/"web"/"static"/"sprint.js").read_text(encoding="utf-8")
        self.assertIn("localStorage",js)
        self.assertNotIn("fetch(",js)
        self.assertNotIn("XMLHttpRequest",js)
        self.assertIn("/sprint.js",self.page.scripts)
        self.assertIn("/analytics.js",self.page.scripts)
    def test_document_has_at_most_ten_fields(self):
        md=(ROOT/"docs"/"T11_DIAGNOSE_FORM_CN.md").read_text(encoding="utf-8")
        rows=re.findall(r"(?m)^\|\s*(\d+)\s*\|",md)
        self.assertEqual(rows,[str(i) for i in range(1,10)])
        for title in ("项目名称","一句话（给谁省什么）","项目链接","当前进度","海外同类付费证据链接","目标用户在哪","已有收入","最想解决的卡点","联系方式（微信或邮箱）"):
            self.assertIn(title,md)
        self.assertIn("已收到，见势会在 7 天内回复诊断结果。",md)
    def test_no_income_promise_terms(self):
        for word in ("保证","月入","躺赚"):self.assertNotIn(word,self.markup)
        self.assertIn("冲刺目标 = 30 天内拿到第一笔可被第三方验证的收入。",self.markup)
    def test_all_plan_sections_present(self):
        for ident in ("step0","week1","week23","week4","fallback","payments","checklist","case0"):
            self.assertIn('id="'+ident+'"',self.markup)
        for phrase in ("私信","50 人","20 次真实对话","≥ $9","≥ $29","/log","第 0 步","服务条款","隐私政策"):
            self.assertIn(phrase,self.markup)
    def test_built_sitemap_and_navigation_when_present(self):
        dist=ROOT/"web"/"dist"
        if not (dist/"index.html").exists() or not (dist/"sprint"/"index.html").exists():
            self.skipTest("Build web/build.py then p412 release to check output")
        self.assertIn("https://jianshi-bua.pages.dev/sprint/",(dist/"sitemap.xml").read_text(encoding="utf-8"))
        # Other test suites also build the intermediate anonymous research homepage.
        # Verify the T11 link when this is the final JIANSHI2 public homepage;
        # T07 release CI always checks the final page explicitly.
        home=(dist/"index.html").read_text(encoding="utf-8")
        if "JIANSHI 2.0" in home:
            self.assertIn('href="/sprint/"',home)
        self.assertIn("/sprint /sprint/ 301",(dist/"_redirects").read_text(encoding="utf-8"))
if __name__=="__main__":
    unittest.main()
