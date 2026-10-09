"""P4.18: editorial hierarchy, legible type, actual project detail emphasis."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")

class TestP418TypographyAndHierarchy(unittest.TestCase):
    def test_primary_content_readable_and_discoverable(self):
        for key in [
            '20 个具名项目 · 6 类商业模式','hero__cta',
            'href="#archive">开始研究项目',
            '先看他们卖什么','再看如何收费',
            'href="#researchLibrary">直达具名项目研究库',
            "pLabel.textContent='收费机制'",
            "pValue.textContent=item.revenue",
            'card.append(area,name,blurb,price,foot)',
            "nodes.slice(0,3).forEach(node=>node.classList.add('detail__primary'))"
        ]: self.assertIn(key,HTML)
        self.assertRegex(HTML,r'\.research-entry__desc\{font-size:15px')
        self.assertRegex(HTML,r'\.detail__rows p,\.detail__rows li\{font-size:16px')
        self.assertRegex(HTML,r'\.find__search\{height:50px;font:400 16px')
        self.assertRegex(HTML,r'\.archive-lead\{font:500 clamp\(')

    def test_research_jump_restores_named_projects(self):
        for marker in ('id="kindAll"','id="kindCase"','id="kindModel"',
                       "querySelector('.archive-jump').addEventListener('click'",
                       "kind='case';search.value=''",
                       "facetControls.forEach(sel=>sel.value='')",
                       "filterTiles();"):
            self.assertIn(marker,HTML)

    def test_important_behavior_unchanged(self):
        self.assertIn('<html lang="zh-CN" data-theme="light">',HTML)
        self.assertIn('themeToggle.addEventListener',HTML)
        self.assertIn("localStorage.setItem('jianshi-theme',next)",HTML)
        self.assertIn('const FACET_INDEX=',HTML)
        self.assertIn('const P415_CASES=',HTML)
        self.assertIn('官方入口与核对依据',HTML)
        self.assertIn('prefers-reduced-motion',HTML)
        self.assertIn('inert',HTML)
        self.assertEqual(HTML.count('data:image/webp;base64,'),8)
        self.assertEqual(HTML.count('<script>'),1)
        self.assertEqual(HTML.count('<style>'),1)
        self.assertLess(len(HTML.encode('utf-8')),260000)

    def test_inline_script_parses(self):
        node=shutil.which('node')
        if node:
            script=re.search(r'<script>([\s\S]*?)</script>',HTML)
            self.assertIsNotNone(script)
            proc=subprocess.run([node,'--check','-'],input=script.group(1),text=True,
                                capture_output=True,timeout=25)
            self.assertEqual(proc.returncode,0,proc.stderr)

if __name__=="__main__":
    unittest.main()
