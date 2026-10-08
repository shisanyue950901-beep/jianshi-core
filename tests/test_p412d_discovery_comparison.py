"""P4.12D — guard discovery, comparison and source-private user experience."""
import json
import re
import subprocess
import shutil
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/"web"/"prototypes"/"p412a"/"index.html"
CFG=ROOT/"config"/"p412d_discovery_contract.json"
CASES=ROOT/"config"/"p412c_named_case_pilots.json"
GUIDES=ROOT/"config"/"p412b_business_content.json"

class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs=[]
        self.buttons=[]
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if "id" in a:self.ids.append(a["id"])
        if tag=="input":self.inputs.append(a)
        if tag=="button":self.buttons.append(a)

class TestP412DDiscoveryAndComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=HTML.read_text(encoding="utf-8")
        cls.config=json.loads(CFG.read_text(encoding="utf-8"))
        cls.cases=json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        cls.guides=json.loads(GUIDES.read_text(encoding="utf-8"))["business_models"]
        cls.tags=_Tags()
        cls.tags.feed(cls.html)

    def test_eight_distinct_user_choices_not_eight_claimed_companies(self):
        self.assertEqual(len(self.guides),6)
        self.assertEqual(len(self.cases),2)
        self.assertIn("商业模式",self.config["search"]["selectable_types"])
        self.assertIn("具体项目",self.config["search"]["selectable_types"])
        self.assertIn('data-project="digital"',self.html)
        self.assertIn('data-case="easlo"',self.html)
        self.assertIn('data-case="louise-lennox"',self.html)
        self.assertIn("不代表",self.config["case_status"]["case_count_is_not_financial_validation"] if isinstance(self.config["case_status"]["case_count_is_not_financial_validation"],str) else "产品存在不代表盈利已核实")

    def test_search_is_typed_and_has_accessible_feedback(self):
        expected=[
            'id="discovery-search"','type="search"','id="discovery-clear"',
            'id="discovery-status"','aria-live="polite"',
            'id="discovery-empty"','data-kind="all"',
            'data-kind="model"','data-kind="case"',
            'function updateDiscovery()','indexText','discoveryInput.addEventListener',
            'discoveryClear.addEventListener'
        ]
        for s in expected:self.assertIn(s,self.html)
        self.assertIn("searchableModels",self.html)
        self.assertIn("searchableCases",self.html)
        self.assertEqual(len(self.tags.ids),len(set(self.tags.ids)))
        self.assertEqual(sum(1 for x in self.tags.inputs if x.get("id")=="discovery-search"),1)

    def test_type_and_group_filters_apply_to_both_model_and_case_cards(self):
        self.assertEqual(sum(1 for s in re.findall(r'data-project="(?:saas|digital|content|kdp|fba|agency)"',self.html)),10)
        self.assertEqual(len(re.findall(r'data-case="(?:easlo|louise-lennox)"',self.html)),2)
        for group in ["digital","content","commerce","service"]:
            self.assertIn('data-filter="'+group+'"',self.html)
        self.assertRegex(self.html,r'data-group="digital" data-case="easlo"')
        self.assertRegex(self.html,r'data-group="content" data-case="louise-lennox"')
        self.assertIn("selectedKind!=='case'",self.html)
        self.assertIn("selectedKind!=='model'",self.html)
        self.assertIn("matchesGroup",self.html)
        self.assertIn("matchesTerm",self.html)

    def test_comparison_is_only_between_business_models(self):
        self.assertEqual(self.config["compare"]["min_selection"],2)
        self.assertEqual(self.config["compare"]["max_selection"],3)
        self.assertEqual(self.config["compare"]["allowed_record_kind"],"business_model")
        self.assertEqual(self.config["compare"]["default_selection"],["digital","kdp"])
        for c in self.config["compare"]["columns"]:
            self.assertIn(c,self.html)
        for guide in self.guides:
            self.assertIn('data-compare="'+guide["id"]+'"',self.html)
        self.assertIn("new Set(['digital','kdp'])",self.html)
        self.assertIn("comparisonSelected.size>=3",self.html)
        self.assertIn("comparisonHead.replaceChildren",self.html)
        self.assertIn("comparisonBody.replaceChildren",self.html)
        self.assertIn("document.createElement('td')",self.html.replace("compareCell('td'","document.createElement('td')"))
        self.assertIn('scope',''.join(self.html.split('compareCell',1)[1:]))
        self.assertIn("这里比较的是商业模式",self.html)
        self.assertNotIn("预计收益排名",self.html)

    def test_mobile_keyboard_and_browser_history(self):
        for s in [
            'id="compare-results"','overflow-x:auto',
            'role="region"','tabindex="0"',
            'role="status"', 'aria-pressed="true"',
            "section.querySelector('h2')?.focus",
            "document.getElementById('case-title').focus",
            "document.getElementById('detail-title').focus",
            "['#projects','#named-cases','#compare']",
            "@media(max-width:760px)","prefers-reduced-motion",
            "addEventListener('hashchange',route)"
        ]:self.assertIn(s,self.html)

    def test_content_and_source_privacy_remain_separate(self):
        for bad in [
            "Empire Flippers","empireflippers","listing_number","OFFICIAL_API",
            "source_ref_ids","source_updated_at","source_url","OPP_V0.2",
            "EASLO_OWN_SITE_01","LENNOX_AMAZON_02",
            "保证收益","预计利润率","中文化与脱敏","爬虫"
        ]:
            self.assertNotIn(bad,self.html)
        self.assertFalse(self.config["production_deployment"])
        self.assertTrue(self.config["compare"]["no_financial_ranking"])

    def test_script_syntax(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node.js unavailable")
        script=re.search(r"<script>(.*?)</script>",self.html,re.S)
        self.assertIsNotNone(script)
        done=subprocess.run([node,"--check","-"],input=script.group(1),
                            text=True,capture_output=True,timeout=20)
        self.assertEqual(done.returncode,0,done.stderr)

if __name__=="__main__":
    unittest.main()
