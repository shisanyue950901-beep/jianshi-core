"""P4.12C named project integrity / privacy / business evidence gates."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/"config"/"p412c_named_case_pilots.json"
GUIDES=ROOT/"config"/"p412b_business_content.json"
HTML=ROOT/"web"/"prototypes"/"p412a"/"index.html"
AUDIT=ROOT/"docs"/"P412C_NAMED_CASE_EVIDENCE_AUDIT.md"

class TestP412CNamedCaseProfiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(CASES.read_text(encoding="utf-8"))
        cls.guides=json.loads(GUIDES.read_text(encoding="utf-8"))
        cls.html=HTML.read_text(encoding="utf-8")

    def test_two_real_named_cases_no_fabricated_financials(self):
        self.assertEqual(self.data["state"],"EDITORIAL_REVIEW_NOT_PUBLIC")
        self.assertEqual(len(self.data["cases"]),2)
        self.assertEqual({c["id"] for c in self.data["cases"]},{"easlo","louise-lennox"})
        existing={x["id"] for x in self.guides["business_models"]}
        for case in self.data["cases"]:
            self.assertIn(case["category_id"],existing)
            self.assertGreaterEqual(len(case["confirmed"]),2)
            self.assertGreaterEqual(len(case["unknowns"]),3)
            self.assertIn("无",case["income_status"])
            self.assertGreaterEqual(len(case["what_sells"]),20)
            self.assertGreaterEqual(len(case["revenue_model"]),22)
        self.assertIn("不得展示未经核实",self.data["trust_policy"]["finances"])

    def test_public_case_content_is_a_strict_explicit_whitelist(self):
        match=re.search(r"const caseProfiles=(\{.*?\});\s*const caseView=",self.html,re.S)
        self.assertIsNotNone(match)
        exposed=json.loads(match.group(1))
        safe_keys={
            "id","name","zh_category","category_id","display_title","brief",
            "what_sells","buyer","revenue_model","confirmed",
            "income_status","business_observation","unknowns","action"
        }
        for case in self.data["cases"]:
            public=exposed[case["id"]]
            self.assertEqual(set(public.keys()),safe_keys)
            for key in safe_keys:self.assertEqual(public[key],case[key])
        self.assertEqual(len(exposed),2)

    def test_no_internal_provenance_or_marketplace_linkage_on_public_page(self):
        for forbidden in [
            "source_ref_ids","EASLO_OWN_SITE_01","LENNOX_AMAZON_02",
            "Empire Flippers","empireflippers", "listing_number",
            "OFFICIAL_API","source_url","https://www.easlo.co",
            "https://www.authorlouiselennox.com","aboutamazon.com",
            "月入十万","轻松赚钱","稳定盈利","保证收益"
        ]:
            self.assertNotIn(forbidden,self.html)
        self.assertIn("这两份项目并非从受保护",self.data["trust_policy"]["relationship"])

    def test_home_has_two_visible_case_navigation_links(self):
        for val in [
            'id="named-cases"','data-case="easlo"','data-case="louise-lennox"',
            'id="case-view"','id="case-breadcrumb"',
            'id="case-facts"','id="case-unknowns"',
            'id="case-related-model"','const caseProfiles=',
            "function showNamedCase(id)","match(/^#case-"
        ]:
            self.assertIn(val,self.html)
        self.assertIn("商品展示和出版经历可以核对",self.html)

    def test_identity_is_not_sales_or_business_profit(self):
        for case in self.data["cases"]:
            text=" ".join([case["brief"],case["revenue_model"],case["business_observation"]])
            self.assertNotRegex(text,r"\b\d+(?:\.\d+)?\s*(?:万)?美元|\$\d+|\d+%")
            self.assertTrue(any(token in case["income_status"] for token in ["无","未"]))
        self.assertIn("商品展示",self.html)
        self.assertIn("不能",self.data["trust_policy"]["commercial"])

    def test_internal_claims_have_audit_trail(self):
        audit=AUDIT.read_text(encoding="utf-8")
        for case in self.data["cases"]:
            for ref in case["source_ref_ids"]:
                self.assertIn(ref,audit)
        self.assertIn("P412C_PRODUCTION_PUBLICATION = FALSE",audit)

if __name__=="__main__":
    unittest.main()
