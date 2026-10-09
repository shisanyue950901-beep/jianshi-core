"""P4.19 spacing and reading-rhythm release contract.

Keep the production HTML single-file while protecting existing motion, themes,
content evidence and interaction contracts. Only layout/CSS is changed.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
CSS=HTML.split("<style>",1)[1].split("</style>",1)[0]

class TestP419SpacingRhythm(unittest.TestCase):
    def test_layout_has_deliberate_whitespace_at_all_scales(self):
        for marker in (
            ".sec{max-width:1380px;margin-inline:auto;",
            "padding:clamp(88px,9vw,148px)",
            ".grid{grid-template-columns:repeat(4,minmax(0,1fr))}",
            ".research-library__list{grid-template-columns:repeat(3,minmax(0,1fr))}",
            "gap:clamp(14px,2vw,24px);border:0;background:none",
            "margin-top:82px;padding-top:48px",
            ".detail__rows{gap:clamp(28px,3.5vw,50px)}",
            "@media(max-width:650px){.sec{padding-top:clamp(70px,10vw,94px)",
            ".research-entry{padding:24px}",
        ):
            self.assertIn(marker,CSS)

    def test_discovery_panel_theme_tokens_are_scoped(self):
        self.assertIn("--panel:#0a0a0a;",CSS)
        self.assertIn("--panel:#fffefa;",CSS)
        for selector in (".find{", ".facet-filters{", ".facet-note{", ".find__result{"):
            self.assertIn(selector,CSS)
        self.assertGreaterEqual(CSS.count("background:var(--panel)"),4)
        self.assertIn(".model-list button{background:#050505;border:1px solid var(--line)",CSS)
        self.assertIn("html[data-theme=light] .model-list button",CSS)
        self.assertIn('data-theme="light"',HTML)
        self.assertIn("localStorage.setItem('jianshi-theme',next)",HTML)

    def test_final_cloudflare_html_under_250kb(self):
        # Mirror P4.12 public-only link/wording injection; test actual ship size.
        html=HTML
        self.assertIn("此文件为独立网站预览，不收集访客信息。",html)
        html=html.replace("此文件为独立网站预览，不收集访客信息。",
                          "本站暂不提供在线留言功能，也不会通过本页面收集访客信息。")
        old='© 2026 见势 JIANSHI</span><a href="#top">'
        self.assertIn(old,html)
        html=html.replace(old,'© 2026 见势 JIANSHI</span><a href="/privacy/">隐私说明</a><a href="#top">')
        html=html.replace("</head>",'<link rel="canonical" href="https://jianshi-bua.pages.dev/">\\n</head>',1)
        self.assertLess(len(html.encode("utf-8")),250000)

    def test_content_motion_and_budget_are_frozen(self):
        self.assertEqual(HTML.count("data:image/webp;base64,"),8)
        self.assertEqual(HTML.count("<style>"),1)
        self.assertEqual(HTML.count("<script>"),1)
        self.assertLess(len(HTML.encode("utf-8")),250000)
        self.assertEqual(CSS.count("{"),CSS.count("}"))
        for marker in ("const FACET_INDEX=", "const P415_CASES=", "const LIBRARY_CASES=",
                       "prefers-reduced-motion", "function renderRing()", "syncLock();\n  const clamp=",
                       "官方入口与核对依据", "收费机制", "id=\"kindAll\"",
                       "href=\"#researchLibrary\""):
            self.assertIn(marker,HTML)
        node=shutil.which("node")
        if node:
            script=re.search(r"<script>([\s\S]*?)</script>",HTML)
            self.assertIsNotNone(script)
            checked=subprocess.run([node,"--check","-"],input=script.group(1),
                                   text=True,capture_output=True,timeout=30)
            self.assertEqual(checked.returncode,0,checked.stderr)

if __name__=="__main__":
    unittest.main()
