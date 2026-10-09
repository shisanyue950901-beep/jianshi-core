"""P4.15: Eight evidenced new projects; twenty named cases; six business models."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web/prototypes/p412e/index.html"
DATA = ROOT / "config/p415_public_case_growth.json"

class TestP415CaseGrowth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        match = re.search(r"const P415_CASES=(\[.*?\]);\s*ITEMS\.push\(\.\.\.P415_CASES\)", cls.html, re.S)
        assert match, "P4.15 案例没有完整写入可检索的单文件"
        cls.render = json.loads(match.group(1))
        original = re.search(r"const EXTRA_CASES=(\[.*?\]);\s*ITEMS\.push\(\.\.\.EXTRA_CASES\)", cls.html, re.S)
        assert original, "P4.13 内容合同不应改变"
        cls.previous = json.loads(original.group(1))

    def test_twenty_named_six_models_and_all_eight_editorial_records(self):
        items = self.data["cases"]
        self.assertEqual(len(items), 8)
        self.assertEqual(len(self.render), 8)
        self.assertEqual(len(self.previous), 10)
        self.assertEqual(len({x["id"] for x in items + self.previous}), 18)
        self.assertIn("const LIBRARY_CASES=[...EXTRA_CASES,...P415_CASES];", self.html)
        self.assertIn("LIBRARY_CASES.forEach(item=>{", self.html)
        self.assertIn("ITEMS.push(...P415_CASES);", self.html)
        for ix, x in enumerate(items):
            shown = self.render[ix]
            self.assertEqual(shown["id"], x["id"])
            self.assertEqual(shown["number"], ix + 19)
            self.assertEqual(shown["verifiedOn"], self.data["verified_on"])
            for k,v in x.items():
                self.assertEqual(shown[k], v, (x["id"], k))
        # ITEMS consists of original two named cases, six models, ten P4.13 and eight P4.15.
        self.assertEqual(2+6+len(self.previous)+len(items), 26)

    def test_first_party_links_and_editorial_disclaimers(self):
        for item in self.data["cases"]:
            self.assertEqual(item["kind"], "case")
            self.assertTrue(item["archiveOnly"])
            self.assertIn(item["model"], {"saas","digital","kdp","content","fba","agency"})
            for key in ("officialHomeUrl","sourceUrl"):
                parsed = urlsplit(item[key])
                self.assertEqual(parsed.scheme, "https")
                self.assertTrue(parsed.hostname)
                self.assertFalse(parsed.username)
                self.assertFalse(parsed.password)
            self.assertGreaterEqual(len(item["facts"]), 2)
            self.assertGreaterEqual(len(item["unknowns"]), 2)
            self.assertGreaterEqual(len(item["learning"]), 18)
            self.assertRegex(" ".join(item["unknowns"]), "未|无法|不能|缺少|未经|不")
        self.assertEqual(self.data["status"], "EDITORIALLY_RESEARCHED_NOT_FINANCIALLY_VERIFIED")
        for forbidden in ("Empire Flippers","empireflippers","listing_number","source_ref_ids","保证盈利"):
            self.assertNotIn(forbidden, self.html)

    def test_motion_accessibility_and_single_file_preserved(self):
        self.assertEqual(self.html.count("data:image/webp;base64,"),8)
        self.assertEqual(self.html.count("<style>"),1)
        self.assertEqual(self.html.count("<script>"),1)
        self.assertIn("ITEMS.filter(item=>!item.archiveOnly).forEach", self.html)
        self.assertIn("N=cards.length;", self.html)
        for indicator in ("prefers-reduced-motion","100dvh","viewport-fit=cover","inert","research-official-links"):
            self.assertIn(indicator,self.html)
        self.assertLess(len(self.html.encode("utf-8")), 250000)
        node=shutil.which("node")
        if node:
            script=re.search(r"<script>([\s\S]*?)</script>", self.html)
            self.assertIsNotNone(script)
            p=subprocess.run([node,"--check","-"],input=script.group(1),capture_output=True,text=True,timeout=30)
            self.assertEqual(p.returncode,0,p.stderr)

if __name__ == "__main__":
    unittest.main()
