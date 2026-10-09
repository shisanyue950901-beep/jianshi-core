"""P4.17 light-default/dark-optional theme without altering public design contracts."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")

class TestP417LightTheme(unittest.TestCase):
    def test_first_visit_light_and_control_accessible(self):
        self.assertIn('<html lang="zh-CN" data-theme="light">',HTML)
        self.assertIn('id="themeToggle"',HTML)
        self.assertIn('aria-label="切换到深色模式"',HTML)
        self.assertIn('aria-pressed="false"',HTML)
        self.assertIn("let theme='light'",HTML)
        self.assertIn("localStorage.getItem('jianshi-theme')==='dark'",HTML)
        self.assertIn("localStorage.setItem('jianshi-theme',next)",HTML)
        self.assertIn("themeToggle.addEventListener('click'",HTML)
        self.assertIn("themeToggle.setAttribute('aria-pressed',String(next==='dark'))",HTML)
        self.assertIn("try{if(localStorage.getItem",HTML)
        self.assertIn("if(persist)try{localStorage.setItem",HTML)
        self.assertNotIn("prefers-color-scheme: dark",HTML)

    def test_light_component_contrast_and_dark_preservation(self):
        self.assertIn('--bg:#000;--ink:#f4f2ef',HTML)
        self.assertIn(':root{color-scheme:dark}',HTML)
        self.assertIn('html[data-theme=light]{--bg:#f7f6f1;--ink:#202823',HTML)
        for component in [
            '.splash,.menu,.lb','.top','.hero__copy',
            '.hero__aux button','.model-list button',
            '.research-entry','.facet-filters select',
            '.card__name','.splash__skip'
        ]:
            self.assertIn(component,HTML)
        self.assertIn('html[data-theme=light] .lb__more:hover{color:var(--bg)}',HTML)
        self.assertIn('.top__tools{display:flex',HTML)

    def test_unchanged_carousel_and_static_release_contract(self):
        self.assertEqual(HTML.count('data:image/webp;base64,'),8)
        self.assertEqual(HTML.count('<script>'),1)
        self.assertEqual(HTML.count('<style>'),1)
        self.assertLess(len(HTML.encode("utf-8")),255000)
        for marker in ('function renderRing()','function endDrag','function openLb(index,filtered)',
                       'prefers-reduced-motion','viewport-fit=cover','100dvh','inert',
                       'const FACET_INDEX=','const P415_CASES=','访问项目官方网站（首页）'):
            self.assertIn(marker,HTML)
        release=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn('OUTPUT = ROOT / "web" / "dist"',release)
        node=shutil.which("node")
        if node:
            script=re.search(r'<script>([\s\S]*?)</script>',HTML)
            self.assertIsNotNone(script)
            p=subprocess.run([node,"--check","-"],input=script.group(1),text=True,
                             capture_output=True,timeout=30)
            self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__":
    unittest.main()
