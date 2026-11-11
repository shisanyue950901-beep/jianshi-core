#!/usr/bin/env python3
"""T11b: readable public Chinese copy, audit isolation and frozen financial baseline.

The scanner looks only at user-visible HTML text nodes; links, script, CSS,
machine-readable ISO timestamps and private project records are not copied into it.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"projects.json"
BASELINE=ROOT/"tests"/"fixtures"/"t11b_main_baseline.json"
DIST=ROOT/"web"/"dist"
MAIN_TOP=("1clickwebsite-ai","sonar-aso-tool","3dplotter")

# Official product/brand names may contain English; do not suppress adjacent copy.
BRAND_ALLOWLIST=("ChatGPT","Product Hunt","TrustMRR","Creem","Stripe",
                 "Dodo Payments","Waffo Pancake","Google Play","GitHub")

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.suppressed=[]
        self.chunks=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in ("script","style","head","template","noscript"):
            self.suppressed.append(tag)
        elif not self.suppressed and ("hidden" in d or d.get("aria-hidden")=="true"
                or "display:none" in d.get("style","").replace(" ","")):
            self.suppressed.append(tag)
    def handle_endtag(self,tag):
        if self.suppressed and tag==self.suppressed[-1]:
            self.suppressed.pop()
    def handle_data(self,data):
        if not self.suppressed and data.strip():
            self.chunks.append(data.strip())

def visible(raw):
    p=VisibleText()
    p.feed(raw)
    return " ".join(p.chunks)

PATTERNS = (
    r"T\d+[a-z]?\s*：",
    r"(?<![A-Za-z])Hark(?![A-Za-z])",r"(?<![A-Za-z])GPT(?![A-Za-z])",r"(?<![A-Za-z])Codex(?![A-Za-z])",
    r"(?<![A-Za-z])slug(?![A-Za-z])",r"\.md(?![A-Za-z])",r"(?<![A-Za-z])Markdown(?![A-Za-z])",r"API\s*key",
    r"(?<![A-Za-z])localStorage(?![A-Za-z])",r"PROJECT LIBRARY",r"FIELD GUIDE",
    r"\bSTEP\s+\d+",r"\bWEEK\s+\d+",r"\bPLAN B\b",
    r"\bCHECKLIST\b",r"\bCASE\s+\d+",r"Last updated",
    r"UTC\+",r"(?<![A-Za-z])CST(?![A-Za-z])",r"\sPM\s",r"\sAM\s",r"A/A-",
    r"同源",r"上游",r"JIANSHI\s*/\s*RESEARCH",
    r"Discover\s*·\s*Verify\s*·\s*Decide",
)
BAD=[re.compile(p,re.I if p in (r"\bslug\b",r"\.md\b",r"\bMarkdown\b") else 0) for p in PATTERNS]
def has_unexplained_kyc(text):
    for found in re.finditer(r"(?<![A-Za-z])KYC(?![A-Za-z])",text):
        next_text=text[found.end():found.end()+18]
        prev=text[max(0,found.start()-18):found.start()]
        if not re.search("实名|企业认证|身份",next_text+prev):
            return True
    return False

class T11bPlainChinese(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build full release rather than relying on cached web/dist from the
        # repository or an unrelated test. API/network use is disabled.
        env=dict(os.environ)
        for key in ("JIANSHI_API_URL","JIANSHI_ANALYTICS_URL","JIANSHI_NEWSLETTER_URL"):
            env[key]=""
        env["JIANSHI_AUTH_ENABLED"]="0"
        subprocess.run([sys.executable,"web/build.py"],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable,"scripts/release/p412_build_public.py"],cwd=ROOT,
                       env=env,check=True,stdout=subprocess.DEVNULL)
        cls.rows=json.loads(DATA.read_text(encoding="utf-8"))

    def test_every_public_html_visible_text(self):
        failures=[]
        pages=sorted(DIST.rglob("*.html"))
        self.assertGreaterEqual(len(pages),60,"Must scan all released HTML, not a sample")
        for page in pages:
            text=visible(page.read_text(encoding="utf-8"))
            for pattern in BAD:
                m=pattern.search(text)
                if m:
                    failures.append((str(page.relative_to(DIST)),pattern.pattern,text[max(0,m.start()-40):m.end()+40]))
            if has_unexplained_kyc(text):
                failures.append((str(page.relative_to(DIST)),"unexplained KYC",""))
        self.assertFalse(failures,"\n".join(map(str,failures[:35])))
        for name in ("index.html","projects/index.html","sprint/index.html"):
            self.assertIn('lang="zh-CN"',(DIST/name).read_text(encoding="utf-8"))

    def test_risk_public_and_private_notes_isolated(self):
        self.assertEqual(len(self.rows),30)
        for p in self.rows:
            with self.subTest(project=p["id"]):
                risk=p.get("risk_public")
                self.assertIsInstance(risk,str)
                self.assertTrue(risk and len(risk)<=40)
                page=(DIST/"projects"/p["id"]/"index.html").read_text(encoding="utf-8")
                self.assertIn(risk,page)
                self.assertIn(risk,(DIST/"projects"/"index.html").read_text(encoding="utf-8"))
                self.assertNotIn("Hark",visible(page))
                for flag in p["flags"]:
                    self.assertNotIn(flag,visible(page))

    def test_income_dates_order_and_home_featured_unchanged_from_main(self):
        frozen=json.loads(BASELINE.read_text(encoding="utf-8"))
        self.assertEqual(len(frozen),30)
        self.assertEqual([p["id"] for p in self.rows],[p["id"] for p in frozen])
        for old,p in zip(frozen,self.rows,strict=True):
            for field in ("id","revenue","founded_date","growth_30d","updated_at","total_score","verdict"):
                self.assertEqual(old[field],p[field],f"Frozen main baseline changed: {p['id']}.{field}")
        sys.path.insert(0,str(ROOT/"scripts"/"release"))
        from t08_project_selection import featured_projects
        self.assertEqual(tuple(p["id"] for p in featured_projects()),MAIN_TOP)
        self.assertIn('href="/projects/"',(DIST/"index.html").read_text(encoding="utf-8"))

    def test_primary_hero_cta_and_customer_safe_sources(self):
        home=visible((DIST/"index.html").read_text(encoding="utf-8"))
        projects=(DIST/"projects"/"index.html").read_text(encoding="utf-8")
        detail=(DIST/"projects"/"datafast"/"index.html").read_text(encoding="utf-8")
        sprint=(DIST/"sprint"/"index.html").read_text(encoding="utf-8")
        for expected,markup in (("先看项目",home),("看推荐项目",visible(projects)),
                                ("打开官网",visible(detail)),("从第 0 步开始",visible(sprint))):
            self.assertIn(expected,markup)
        for markup in (projects,detail):
            self.assertNotIn("T08b：",visible(markup))
            self.assertNotIn("Hark",visible(markup))
            self.assertNotIn("Markdown",visible(markup))
        self.assertIn("表单即将开放",sprint)
        self.assertNotIn('href="/log/"',sprint)

if __name__=="__main__":
    unittest.main()
