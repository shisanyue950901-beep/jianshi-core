"""P4.12F — accessible dialogs and offscreen animation scheduling."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/"web"/"prototypes"/"p412e"/"index.html"

class TestP412FMotionQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=PAGE.read_text(encoding="utf-8")

    def test_visual_and_single_file_contract_unchanged(self):
        self.assertEqual(self.html.count("<style>"),1)
        self.assertEqual(self.html.count("<script>"),1)
        self.assertEqual(self.html.count("data:image/webp;base64,"),8)
        self.assertIn("Playfair+Display",self.html)
        self.assertIn("family=Inter",self.html)
        self.assertIn("--bg:#000",self.html)
        self.assertIn("viewport-fit=cover",self.html)
        self.assertIn("safe-area-inset-bottom",self.html)
        self.assertIn("100dvh",self.html)
        self.assertIn("prefers-reduced-motion",self.html)
        self.assertLess(len(self.html.encode("utf-8")),250000)

    def test_dialog_inert_prevents_background_focus(self):
        for snippet in [
            "function syncLock(){",
            "const blocked=!splashDone||menuOpen||lbOpen;",
            "header.inert=blocked",
            "main.inert=blocked",
            "activeMenu.inert=!menuOpen",
            "lightbox.inert=!lbOpen",
            "splashNode.inert=splashDone",
            "function keepFocus(e,node)",
            "syncLock();\n  const clamp=",
        ]:self.assertIn(snippet,self.html)
        self.assertIn("aria-modal=\"true\"",self.html)
        self.assertIn("aria-expanded",self.html)

    def test_animation_stops_when_not_visible_and_resumes(self):
        for snippet in [
            "function stopFrames()",
            "cancelAnimationFrame(raf)",
            "function startFrames()",
            "if(reduced||raf||!visible||document.hidden)return;",
            "if(visible)startFrames();else stopFrames();",
            "if(document.hidden)stopFrames();else startFrames()",
            "layout();startFrames();"
        ]:self.assertIn(snippet,self.html)
        self.assertNotIn("raf=requestAnimationFrame(frame);\n  }\n  if('IntersectionObserver'",self.html)
        self.assertIn("if($('ringStatus').textContent!==status)",self.html)

    def test_existing_navigation_regressions_remain_blocked(self):
        self.assertIn("function openLb(index,filtered)",self.html)
        self.assertIn("lightboxOrder=filtered?tiles.filter",self.html)
        self.assertIn("function routeItemFromHash()",self.html)
        self.assertIn("function keepFocus(e,node)",self.html)
        self.assertIn("document.querySelectorAll('.find__filters [data-kind]')",self.html)
        self.assertNotIn("document.querySelectorAll('[data-kind]')",self.html)
        self.assertIn("history.pushState",self.html)

    def test_no_sensitive_sources_in_public_html(self):
        for forbidden in [
            "Empire Flippers","empireflippers",
            "source_ref_ids","source_url","OFFICIAL_API",
            "listing_number","OPP_V0.2",
            "EASLO_OWN_SITE_01","LENNOX_AMAZON_02",
            "保证盈利","预计利润率"
        ]:self.assertNotIn(forbidden,self.html)

    def test_javascript_syntax(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node.js unavailable")
        script=re.search(r"<script>([\s\S]*?)</script>",self.html)
        self.assertIsNotNone(script)
        proc=subprocess.run([node,"--check","-"],input=script.group(1),capture_output=True,text=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stderr)

if __name__=="__main__":
    unittest.main()
