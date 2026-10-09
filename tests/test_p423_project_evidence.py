"""P4.23 independently sourced dossiers: 20 entries, no industry-to-company inference."""
import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/release/p423_build_project_proofs.py"
BASE=ROOT/"scripts/release/p412_build_public.py"
DIST=ROOT/"web/dist"
HTML=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
PROOF=(ROOT/"web/prototypes/p422/evidence.html").read_text(encoding="utf-8")

class TestP423NamedEvidence(unittest.TestCase):
    def test_build_and_project_provenance(self):
        p=subprocess.run([sys.executable,str(SCRIPT)],cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(p.returncode,0,p.stderr)
        report=json.loads(p.stdout)
        self.assertEqual(report["cases"],20)
        self.assertEqual(report["public_pages"],21)
        html=(DIST/"projects/index.html").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'href="/projects/[a-z0-9-]+/"',html)),20)
        self.assertIn("产品存在",html)
        self.assertIn("待补证据优先",html)
        self.assertIn("证据层级优先",html)
        profiles=list((DIST/"projects").glob("*/index.html"))
        self.assertEqual(len(profiles),20)
        for p in profiles:
            s=p.read_text(encoding="utf-8")
            for marker in ("官方依据","收费机制：有公开说明","真实交易／客户：待独立核实",
                           "打开项目官方网站",
                           "打开产品／收费核对依据","独立客户需求"):
                if marker == "官方依据":
                    self.assertIn(marker,s.replace("官方页面", "官方依据"))
                else:
                    self.assertIn(marker,s,str(p))
            if p.parent.name == "nerdwallet":
                self.assertIn("历史公司级财务：有监管披露",s)
            elif p.parent.name in ("plausible","carrd"):
                self.assertIn("历史收入：创始人／企业公开自述",s)
            else:
                self.assertIn("利润／经营成果：待独立核实",s)
            self.assertIn('rel="noopener noreferrer"',s)
            self.assertIn('data-theme="light"',s)
            self.assertIn('html[data-theme=dark]',s)
            self.assertIn('id="themeToggle"',s)
            self.assertIn("localStorage.setItem('jianshi-theme',next)",s)
            self.assertNotIn("Empire Flippers",s)
            self.assertNotIn("listing_number",s)
            self.assertNotIn("source_url",s)
            self.assertNotIn("OPP_V0.2",s)

    def test_first_two_cases_get_only_audited_official_context(self):
        easlo=(DIST/"projects/easlo/index.html").read_text(encoding="utf-8")
        louise=(DIST/"projects/louise/index.html").read_text(encoding="utf-8")
        self.assertIn("https://www.notion.com/templates/creators/easlo",easlo)
        self.assertIn("https://www.aboutamazon.com/news/books-and-authors/",louise)
        self.assertIn("不能推断当前版税",louise)
        for x in [easlo,louise]:
            self.assertIn("2026-10-08",x)
            self.assertIn("不使用行业匿名挂牌推断它的收入",x)
            self.assertIn("尚无该项目可计入的需求实证",x)

    def test_new_cases_and_home_detail_links_are_unchanged(self):
        self.assertIn("'/projects/'+item.id+'/'",HTML)
        self.assertIn('href="/projects/"',HTML)
        self.assertIn("href=\"/projects/\"",PROOF)
        self.assertEqual(HTML.count("data:image/webp;base64,"),8)
        self.assertEqual(HTML.count("<style>"),1)
        self.assertEqual(HTML.count("<script>"),1)
        self.assertLess(len(HTML.encode("utf-8"))+124,260000)
        release=BASE.read_text(encoding="utf-8")
        self.assertIn("from p423_build_project_proofs import build as build_project_proofs",release)
        self.assertIn('project_result = build_project_proofs()',release)
        self.assertIn('DEST = ROOT / "web/dist/projects"',SCRIPT.read_text(encoding="utf-8"))
        self.assertIn("project_result[\"cases\"] != 20",release)
        self.assertIn('OUTPUT = ROOT / "web" / "dist"',release)

if __name__=="__main__":
    unittest.main()
