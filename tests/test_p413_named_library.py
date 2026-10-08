"""P4.13: real named business profiles and discovery integration."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"config"/"p413_public_project_library.json"
HTML=ROOT/"web"/"prototypes"/"p412e"/"index.html"
RELEASE=ROOT/"scripts"/"release"/"p412_build_public.py"

class TestP413NamedBusinessLibrary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(DOC.read_text(encoding="utf-8"))
        cls.html=HTML.read_text(encoding="utf-8")
        match=re.search(r"const EXTRA_CASES=(\[.*?\]);\s*ITEMS\.push\(\.\.\.EXTRA_CASES\)",cls.html,re.S)
        if match is None: raise AssertionError("Missing JS case data insertion")
        cls.render=json.loads(match.group(1))

    def test_ten_verified_official_project_entries_across_six_categories(self):
        projects=self.data["cases"]
        self.assertEqual(len(projects),10)
        self.assertEqual(len(self.render),10)
        self.assertEqual(len({x["id"] for x in projects}),10)
        self.assertEqual({x["model"] for x in projects},{"saas","digital","kdp","content","fba","agency"})
        self.assertEqual({x["id"] for x in projects},{x["id"] for x in self.render})
        for record in projects:
            self.assertTrue(record["archiveOnly"],record["id"])
            self.assertEqual(record["kind"],"case")
            self.assertTrue(record["sourceUrl"].startswith("https://"))
            self.assertGreaterEqual(len(record["facts"]),2)
            self.assertGreaterEqual(len(record["unknowns"]),2)
            self.assertGreaterEqual(len(record["offer"]),15)
            self.assertGreaterEqual(len(record["learning"]),18)
            self.assertRegex(" ".join(record["unknowns"]),r"无法|未经|未知|不能|没有|未独立|未核实|不可|没有经")
            jsitem=next(x for x in self.render if x["id"]==record["id"])
            for key,value in record.items():
                self.assertEqual(jsitem[key],value,(record["id"],key))
            self.assertEqual(jsitem["number"],9+projects.index(record))
        self.assertEqual(self.data["status"],"EDITORIALLY_RESEARCHED_NOT_FINANCIALLY_VERIFIED")

    def test_added_entries_do_not_change_photo_ring_size_or_original_visual(self):
        self.assertEqual(self.html.count("data:image/webp;base64,"),8)
        self.assertIn("ITEMS.filter(item=>!item.archiveOnly).forEach",self.html)
        self.assertIn("N=cards.length;",self.html)
        self.assertIn("const EXTRA_CASES=",self.html)
        self.assertIn("ITEMS.push(...EXTRA_CASES);",self.html)
        self.assertEqual(self.html.count("<style>"),1)
        self.assertEqual(self.html.count("<script>"),1)
        self.assertIn("--bg:#000",self.html)
        self.assertIn("Playfair+Display",self.html)
        self.assertIn("family=Inter",self.html)
        self.assertLess(len(self.html.encode("utf-8")),250000)

    def test_discovery_query_filters_new_real_business_entries(self):
        for contract in [
            'id="researchLibrary"','id="libraryList"',
            'className=\'research-entry\'',
            "libraryEntries.forEach(({card,item})=>",
            "card.hidden=!match;if(match){found++;libraryFound++}",
            "const match=(kind==='all'||kind==='case')",
            "card.addEventListener('click',()=>openDetail(index))",
            "const item=ITEMS[i];if(!item)return;",
            "history.pushState({item:item.id}",
            "item.sourceUrl",
            "link.target='_blank'",
            "link.rel='noopener noreferrer'",
            "text(searchStatus,'共找到 '+found",
        ]:
            self.assertIn(contract,self.html)

    def test_official_public_links_not_internal_supplier_records(self):
        for banned in [
            "Empire Flippers","empireflippers","listing_number",
            "source_ref_ids","source_url","OFFICIAL_API",
            "EASLO_OWN_SITE_01","LENNOX_AMAZON_02",
            "保证盈利","保证收益","预计利润率"
        ]:
            self.assertNotIn(banned,self.html)
        self.assertTrue(self.data["public_policy"]["no_marketplace_reidentification"])
        self.assertTrue(self.data["public_policy"]["no_unverified_profit"])
        self.assertIn("SOURCE = ROOT / \"web\" / \"prototypes\" / \"p412e\" / \"index.html\"",RELEASE.read_text(encoding="utf-8"))

    def test_javascript_parses(self):
        node=shutil.which("node")
        if node is None:self.skipTest("Node.js unavailable")
        match=re.search(r"<script>([\s\S]*?)</script>",self.html)
        self.assertIsNotNone(match)
        p=subprocess.run([node,"--check","-"],input=match.group(1),text=True,capture_output=True,timeout=30)
        self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__":
    unittest.main()
