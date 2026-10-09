"""P4.21 comparison selection clarity and scannable summary cards."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
CSS=PAGE.split("<style>",1)[1].split("</style>",1)[0]

class TestP421ComparisonClarity(unittest.TestCase):
    def test_selected_buttons_are_legible_in_both_themes(self):
        self.assertIn('html lang="zh-CN" data-theme="light"',PAGE)
        self.assertIn("id=\"themeToggle\"",PAGE)
        self.assertIn(".compare__choices button[aria-pressed=true]{color:var(--ink);",CSS)
        self.assertIn("color-mix(in srgb,var(--accent) 16%,var(--bg))",CSS)
        self.assertIn("border:2px solid var(--accent)",CSS)
        self.assertIn(".compare__choices button:focus-visible",CSS)
        self.assertIn("btn.setAttribute('aria-pressed',String(active))",PAGE)
        self.assertIn("btn.textContent=(active?'✓ 已选 · ':'＋ ')+item.title",PAGE)
        self.assertIn("btn.setAttribute('aria-label',(active?'取消对比 ':'加入对比 ')+item.title)",PAGE)
        self.assertIn("picked.size>=3",PAGE)

    def test_quick_insight_cards_and_full_details(self):
        self.assertIn('id="compareSummaryTitle"',PAGE)
        self.assertIn('id="compareQuick"',PAGE)
        self.assertIn('id="compareDetails"',PAGE)
        self.assertIn('id="compareOverflow"',PAGE)
        self.assertIn("details class=\"compare__details\"",PAGE)
        self.assertIn("quick.replaceChildren()",PAGE)
        self.assertIn("quick.hidden=selected.length<2",PAGE)
        self.assertIn("tips={saas:",PAGE)
        for fragment in (
            "digital:['单次购买','制作、交付与更新']",
            "kdp:['图书销售结算','写作、编辑与发行']",
            "fba:['商品销售','供应链与库存']",
            "agency:['项目或服务合同','客户沟通与交付']",
            "const fields=[['收费方式','revenue']",
            "if(key==='revenue')row.className='compare__money'",
            "grid-template-columns:repeat(auto-fit,minmax(min(270px,100%),1fr))",
            "position:sticky;left:0",
            "@media(max-width:760px){.compare__quick{grid-template-columns:1fr}",
        ):
            self.assertIn(fragment,PAGE)

    def test_release_scope_animation_data_and_cost_budget(self):
        self.assertEqual(PAGE.count("<style>"),1)
        self.assertEqual(PAGE.count("<script>"),1)
        self.assertEqual(PAGE.count("data:image/webp;base64,"),8)
        self.assertLess(len(PAGE.encode("utf-8")),260000)
        self.assertIn("const P415_CASES=",PAGE)
        self.assertIn("const FACET_INDEX=",PAGE)
        self.assertIn("timeZone:'Asia/Shanghai'",PAGE)
        self.assertIn("prefers-reduced-motion",PAGE)
        self.assertIn("function renderRing()",PAGE)
        self.assertNotIn("Empire Flippers",PAGE)
        node=shutil.which("node")
        if node:
            code=re.search(r"<script>([\s\S]*?)</script>",PAGE)
            self.assertIsNotNone(code)
            res=subprocess.run([node,"--check","-"],input=code.group(1),text=True,capture_output=True,timeout=30)
            self.assertEqual(res.returncode,0,res.stderr)

if __name__=="__main__":
    unittest.main()
