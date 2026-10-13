"""G2-C: authored contextual journeys, responsive markup and fail-closed release audit."""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from f21_g2c_related_quality import RELATED, CSS, render_related, audit_release
from p446_content_hubs import render_pages
from f21_g2_discovery import render as discovery_render

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.sections=0
    def handle_starttag(self,tag,attrs):
        attr=dict(attrs)
        if tag=="a" and attr.get("class")=="g2c-link":
            self.links.append(attr.get("href"))
        if tag=="section" and "g2c-related" in attr.get("class","").split():
            self.sections+=1

def shell(route:str,contents:str|None=None)->str:
    body=contents if contents is not None else (render_related(route) if route in RELATED else '<p>已公开站内内容</p>')
    return ('<!doctype html><html lang="zh-CN"><head><title>受控测试</title>'
            '<meta name="description" content="人工审核后发布">'
            '<meta name="viewport" content="width=device-width">'
            '<link rel="canonical" href="https://jianshi-bua.pages.dev/'
            +route.lstrip('/')+'"></head><body><main><h1>测试</h1>'
            +body+'</main></body></html>')

class G2CContentQuality(unittest.TestCase):
    def test_link_graph_is_curated_and_not_self_referential(self):
        self.assertEqual(len(RELATED),9)
        self.assertEqual(sum(len(rows) for rows in RELATED.values()),27)
        for route,rows in RELATED.items():
            with self.subTest(route=route):
                self.assertEqual(len(rows),3)
                self.assertEqual(len(set(x[0] for x in rows)),3)
                self.assertNotIn(route,[x[0] for x in rows])
                for dest,title,description in rows:
                    self.assertTrue(dest.startswith("/") and dest.endswith("/"))
                    self.assertNotIn("?",dest)
                    self.assertNotIn("#",dest)
                    self.assertNotIn("://",dest)
                    self.assertGreaterEqual(len(title),4)
                    self.assertGreaterEqual(len(description),12)

    def test_nine_real_rendered_pages_have_exact_contextual_cards(self):
        pages={"/"+p:s for p,s in render_pages().items()}
        pages["/discover/"]=discovery_render()
        self.assertEqual(set(pages),set(RELATED))
        for path,document in pages.items():
            with self.subTest(path=path):
                parser=Links()
                parser.feed(document)
                self.assertEqual(parser.sections,1)
                self.assertEqual(parser.links,[x[0] for x in RELATED[path]])
                self.assertIn('aria-label="相关内容与下一步"',document)
                self.assertIn("不代表在线服务、课程或商单已开放",document)
                self.assertEqual(document.count("<main"),1)
                self.assertEqual(document.count("</main>"),1)
                self.assertIn("minmax(0,1fr)",document)
                self.assertIn("@media(max-width:600px)",document)
                self.assertLess(len(document.encode("utf-8")),115_000)
                for forbidden in ("sb_secret_","PRIVATE_RESEARCH","SMTP_PASSWORD",
                                  "synthetic_g1f","service_role_key"):
                    self.assertNotIn(forbidden.lower(),document.lower())

    def test_keyboard_mobile_and_motion_styles(self):
        for important in (".g2c-link:focus-visible",".g2c-links",
                          "@media(max-width:600px)","@media(prefers-reduced-motion:reduce)"):
            self.assertIn(important,CSS)
        self.assertIn("grid-template-columns:1fr",CSS)
        self.assertIn("min-height:0",CSS)

    def test_audit_rejects_missing_target_and_broken_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            all_paths=set(RELATED)|{r[0] for rows in RELATED.values() for r in rows}
            for route in all_paths:
                dest=root/route.lstrip("/")/"index.html"
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text(shell(route),encoding="utf-8")
            proof=audit_release(root)
            self.assertEqual(proof["audited_pages"],9)
            self.assertEqual(proof["related_links"],27)
            self.assertGreaterEqual(proof["unique_targets"],9)
            # Audit must block a public-page target disappearing after curation.
            lost=root/"sources/index.html"
            lost.unlink()
            with self.assertRaisesRegex(RuntimeError,"broken internal link"):
                audit_release(root)
            lost.write_text("<html><p>redirect-only</p></html>",encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"destination not a content page"):
                audit_release(root)
            lost.write_text(shell("/sources/"),encoding="utf-8")
            first=root/"academy/index.html"
            first.write_text(shell("/academy/").replace('class="g2c-related"','class="lost-section"'),
                             encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"integrity failure"):
                audit_release(root)

    def test_builder_runs_audit_before_release_success(self):
        script=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn("related_quality = audit_g2c_release(OUTPUT)",script)
        self.assertIn("g2c_related_quality",script)
        self.assertLess(script.index("related_quality = audit_g2c_release"),
                        script.index('"status": "PASS"'))
        for banned in ("fetch(","requests.get(","urllib.request","create_user",
                       "SUPABASE_SERVICE_ROLE_KEY"):
            module=(ROOT/"scripts/release/f21_g2c_related_quality.py").read_text()
            self.assertNotIn(banned,module)

if __name__=="__main__":
    unittest.main()
