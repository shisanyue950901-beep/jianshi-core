"""P4.12B — public content value, consistency and no-fabrication guardrails."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"config"/"p412b_business_content.json"
BASE=ROOT/"config"/"p412a_user_product_model.json"
HTML=ROOT/"web"/"prototypes"/"p412a"/"index.html"
DOC=ROOT/"docs"/"P412B_BUSINESS_CONTENT_REVIEW.md"

class TestP412BBusinessContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content=json.loads(CONTENT.read_text(encoding="utf-8"))
        cls.base=json.loads(BASE.read_text(encoding="utf-8"))
        cls.html=HTML.read_text(encoding="utf-8")
        cls.models=cls.content["business_models"]

    def test_six_categories_have_unique_ids_and_known_slugs(self):
        self.assertEqual(len(self.models),6)
        self.assertEqual({x["id"] for x in self.models},{x["id"] for x in self.base["business_models"]})
        self.assertEqual({x["slug"] for x in self.models},{x["slug"] for x in self.base["business_models"]})
        self.assertEqual(self.content["state"],"EDITORIAL_REVIEW_NOT_PUBLIC")

    def test_every_category_answers_business_questions_with_specific_content(self):
        fields=["title","card_line","hook","offer","buyer","how_it_works","revenue","evidence","mistake"]
        arrays=["daily_work","costs","forms","unknowns","questions","tags"]
        for item in self.models:
            for field in fields:
                self.assertGreaterEqual(len(item[field]),3 if field=="title" else 8,(item["id"],field))
            self.assertGreaterEqual(len(item["how_it_works"]),70,item["id"])
            self.assertGreaterEqual(len(item["revenue"]),43,item["id"])
            for field in arrays:
                self.assertGreaterEqual(len(item[field]),3,(item["id"],field))
                self.assertTrue(all(isinstance(x,str) and len(x)>=4 for x in item[field]))
            self.assertRegex(item["evidence"]+" "+item["mistake"],r"不能|不等于|不代表|无法|不足以|不意味着")

    def test_no_fake_company_profiles_or_performance_numbers(self):
        raw=json.dumps(self.content,ensure_ascii=False)
        for forbidden in [
            "Empire Flippers","empireflippers","listing_number","source_url",
            "OFFICIAL_API","OPP_V0.2","月入十万","保证收益","躺赚","稳赚不赔",
        ]:
            self.assertNotIn(forbidden,raw)
        for item in self.models:
            self.assertNotRegex(item["revenue"],r"\$\s*\d|\d+%")
        self.assertIn("商业模式类别",self.content["editorial_rule"]["classification"])

    def test_prototype_content_is_in_sync_with_reviewed_json(self):
        match=re.search(r"const data=(\{.*?\});\s*const (?:home|caseProfiles)=",self.html,re.S)
        self.assertIsNotNone(match,"Static preview content not embedded as JSON")
        rendered=json.loads(match.group(1))
        self.assertEqual(set(rendered),{x["id"] for x in self.models})
        for item in self.models:
            record=rendered[item["id"]]
            self.assertEqual(record["title"],item["title"])
            self.assertEqual(record["lead"],item["card_line"])
            self.assertEqual(record["business"],item["how_it_works"])
            self.assertEqual(record["customer"],item["buyer"])
            self.assertEqual(record["revenue"],item["revenue"])
            self.assertEqual(record["operation"],"；".join(item["daily_work"])+"。")
            self.assertEqual(record["costs"],"、".join(item["costs"])+"。")
            self.assertEqual(record["evidence"],item["evidence"])
            self.assertEqual(record["unknowns"],"；".join(item["unknowns"])+"。")
            self.assertEqual(record["questions"],"；".join(item["questions"])+"。")

    def test_detail_has_customer_cost_and_next_question_sections(self):
        for id_ in ["detail-business","detail-customer","detail-revenue","detail-operation",
                    "detail-costs","detail-evidence","detail-unknowns","detail-questions"]:
            self.assertIn('id="'+id_+'"',self.html)
            self.assertIn("'"+id_.replace("detail-","")+"'",self.html)
        for label in ["卖给谁？","通常有哪些成本？","如果继续研究，可以先问什么？","主要收入："]:
            self.assertIn(label,self.html)

    def test_public_preview_contains_no_product_engineering_terms_or_supplier_identity(self):
        for term in [
            "Empire Flippers","empireflippers","listing_number","采集方式：",
            "源更新时间：","脱敏统计","OPA_GATE","OPP_V0.2",
            "统计管道","内部采集","原始项目标识不对外展示",
        ]:
            self.assertNotIn(term,self.html)

    def test_js_syntax_when_node_available(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node.js unavailable on runner")
        js=re.search(r"<script>(.*?)</script>",self.html,re.S)
        self.assertIsNotNone(js)
        result=subprocess.run([node,"--check","-"],input=js.group(1),
                              text=True,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_editorial_guide_preserves_release_boundary(self):
        guide=DOC.read_text(encoding="utf-8")
        self.assertIn("PRODUCTION_PUBLICATION = FALSE",guide)
        self.assertIn("没有可核实的具体公司资料",guide)

if __name__=="__main__":
    unittest.main()
