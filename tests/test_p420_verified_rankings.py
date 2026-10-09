"""P4.20 ranked research list: real audit dates, first-party provenance and safe behavior."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
P413=json.loads((ROOT/"config/p413_public_project_library.json").read_text(encoding="utf-8"))
P415=json.loads((ROOT/"config/p415_public_case_growth.json").read_text(encoding="utf-8"))

class TestP420VerifiedRanking(unittest.TestCase):
    def test_real_editorial_time_windows_and_missing_date_exclusion(self):
        self.assertEqual(P413["verified_on"],"2026-10-09")
        self.assertEqual(P415["verified_on"],"2026-10-09")
        self.assertEqual(len(P413["cases"]),10)
        self.assertEqual(len(P415["cases"]),8)
        self.assertIn("EXTRA_CASES.forEach(item=>item.verifiedOn='2026-10-09')",HTML)
        match=re.search(r"const P415_CASES=(\\[.*?\\]);\\s*ITEMS\\.push\\(\\.\\.\\.P415_CASES\\)",HTML,re.S)
        self.assertIsNotNone(match)
        for item in json.loads(match.group(1)):
            self.assertEqual(item["verifiedOn"],P415["verified_on"])
        self.assertIn('data-rank-period="today"',HTML)
        self.assertIn('data-rank-period="week"',HTML)
        self.assertIn('data-rank-period="month"',HTML)
        self.assertIn("timeZone:'Asia/Shanghai'",HTML)
        self.assertIn("getUTCDay()",HTML)
        self.assertIn("item.verifiedOn>=since&&item.verifiedOn<=today",HTML)
        self.assertIn("localeCompare(a.item.verifiedOn)",HTML)
        self.assertIn("libraryList.append(card)",HTML)
        self.assertIn("不是热度或盈利榜",HTML)
        self.assertIn("首次发现渠道尚未逐项记录",HTML)

    def test_top_ten_read_more_and_scannable_provenance(self):
        self.assertIn('id="photoGallery"',HTML)
        self.assertIn('id="rankStatus"',HTML)
        self.assertIn('id="rankMore"',HTML)
        self.assertIn("rankExpanded||i<10",HTML)
        self.assertIn("rankExpanded=!rankExpanded",HTML)
        self.assertIn("row.className='rank-row'",HTML)
        self.assertIn("card.append(area,name,blurb,price,foot)",HTML)
        self.assertIn("src.className='rank-sources'",HTML)
        self.assertIn("caption.textContent='信息依据：官方公开页面'",HTML)
        self.assertIn("[['officialHomeUrl','官方网站'],['sourceUrl','核验依据']]",HTML)
        self.assertIn("a.rel='noopener noreferrer'",HTML)
        self.assertIn("if(link.protocol!=='https:'||link.username||link.password)return",HTML)
        self.assertIn("card.addEventListener('click',()=>openDetail(index))",HTML)
        for item in P413["cases"]+P415["cases"]:
            self.assertTrue(item["officialHomeUrl"].startswith("https://"))
            self.assertTrue(item["sourceUrl"].startswith("https://"))

    def test_theme_animation_privacy_and_255kb_transitional_budget(self):
        self.assertEqual(HTML.count("<style>"),1)
        self.assertEqual(HTML.count("<script>"),1)
        self.assertEqual(HTML.count("data:image/webp;base64,"),8)
        self.assertLess(len(HTML.encode("utf-8")),255000)
        self.assertIn('data-theme="light"',HTML)
        self.assertIn("localStorage.setItem('jianshi-theme',next)",HTML)
        self.assertIn("prefers-reduced-motion",HTML)
        self.assertIn("id=\"grid\"",HTML)
        self.assertIn("const P415_CASES=",HTML)
        self.assertNotIn("Empire Flippers",HTML)
        self.assertNotIn("listing_number",HTML)
        node=shutil.which("node")
        if node:
            script=re.search(r"<script>([\s\S]*?)</script>",HTML)
            self.assertIsNotNone(script)
            result=subprocess.run([node,"--check","-"],input=script.group(1),
                                  text=True,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)

if __name__=="__main__":
    unittest.main()
