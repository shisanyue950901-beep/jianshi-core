"""P4.16: reviewed multidimensional filters for 20 named overseas projects."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/"web"/"prototypes"/"p412e"/"index.html"
SCHEMA=ROOT/"config"/"p416_editorial_facets.json"

class TestP416EditorialFacets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=HTML.read_text(encoding="utf-8")
        cls.data=json.loads(SCHEMA.read_text(encoding="utf-8"))
        match=re.search(r"const FACET_INDEX=(\{.*?\});\s*const facetControls=",cls.html,re.S)
        assert match, "Frontend taxonomy index missing"
        cls.index=json.loads(match.group(1))

    def test_twenty_tags_synced_with_editorial_schema(self):
        records=self.data["projects"]
        self.assertEqual(len(records),20)
        self.assertEqual(len({x["id"] for x in records}),20)
        self.assertEqual(set(self.index),{x["id"] for x in records})
        for entry in records:
            expected=["".join(entry["delivery"]),"".join(entry["revenue"]),"".join(entry["audience"])]
            self.assertEqual(self.index[entry["id"]],expected)
            self.assertTrue(all(expected))
            self.assertLessEqual(len(expected[0]),4)
            self.assertLessEqual(len(expected[1]),5)
            self.assertLessEqual(len(expected[2]),2)
            for k,allowed in [("delivery","dpsc"),("revenue","uotap"),("audience","bc")]:
                self.assertTrue(set(entry[k]).issubset(set(allowed)))
        self.assertEqual(set(self.index["payhip"][1]),{"u","t"})
        self.assertEqual(set(self.index["superside"][1]),{"u","p"})
        self.assertEqual(set(self.index["louise"][0]),{"d","p"})
        self.assertIn("NOT_AUDITED",self.data["status"])

    def test_visible_filters_accessible_and_resettable(self):
        self.assertIn('id="facetFilters" role="group"',self.html)
        self.assertIn('data-facet="0" aria-label="交付形式"',self.html)
        self.assertIn('data-facet="1" aria-label="收费方式"',self.html)
        self.assertIn('data-facet="2" aria-label="客户对象"',self.html)
        self.assertIn('id="facetReset"',self.html)
        self.assertIn("facetControls.every((sel,i)",self.html)
        self.assertIn("matchesFacets(item)&&(!term",self.html)
        self.assertIn("facetControls.forEach(sel=>sel.addEventListener('change'",self.html)
        self.assertIn("facetControls.forEach(sel=>sel.value='')",self.html)
        self.assertIn("btn.dataset.kind==='case'",self.html)
        self.assertIn("一家公司可能有多种收费方式",self.html)

    def test_motion_and_release_protection(self):
        h=self.html
        self.assertEqual(h.count("data:image/webp;base64,"),8)
        self.assertEqual(h.count("<style>"),1)
        self.assertEqual(h.count("<script>"),1)
        self.assertIn("ITEMS.filter(item=>!item.archiveOnly).forEach",h)
        self.assertIn("prefers-reduced-motion",h)
        self.assertIn("viewport-fit=cover",h)
        self.assertIn("100dvh",h)
        self.assertIn("inert",h)
        self.assertIn("研究",h)
        self.assertLess(len(h.encode("utf-8")),255000)
        node=shutil.which("node")
        if node:
            script=re.search(r"<script>([\s\S]*?)</script>",h)
            self.assertIsNotNone(script)
            check=subprocess.run([node,"--check","-"],input=script.group(1),text=True,capture_output=True,timeout=30)
            self.assertEqual(check.returncode,0,check.stderr)
        release=(ROOT/"scripts"/"release"/"p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn('OUTPUT = ROOT / "web" / "dist"',release)

if __name__=="__main__":
    unittest.main()
