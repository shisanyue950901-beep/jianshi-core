import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config"/"p412a_user_product_model.json"
PREVIEW=ROOT/"web"/"prototypes"/"p412a"/"index.html"
BUILD=ROOT/"web"/"build.py"

class _Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.buttons=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if "id" in d:self.ids.append(d["id"])
        if tag=="button":self.buttons+=1

class TestP412AUserProductRedesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.html=PREVIEW.read_text(encoding="utf-8")
        cls.build=BUILD.read_text(encoding="utf-8")

    def test_six_business_categories_are_not_fake_companies(self):
        models=self.cfg["business_models"]
        self.assertEqual(len(models),6)
        self.assertEqual(len({x["slug"] for x in models}),6)
        self.assertEqual(len({x["id"] for x in models}),6)
        for x in models:
            self.assertEqual(x["evidence_status"],"CATEGORY_OBSERVED")
            self.assertTrue(x["summary"])
            self.assertTrue(x["revenue_model"])
        self.assertIn("商业模式分类不等于",self.cfg["content_policy"]["project_identity_rule"])

    def test_design_reference_not_duplicated_literally(self):
        self.assertIn("prefers-reduced-motion",self.html)
        self.assertIn('lang="zh-CN"',self.html)
        self.assertIn("noindex,nofollow",self.html)
        self.assertEqual(self.html.count("<style>"),1)
        self.assertEqual(self.html.count("<script>"),1)
        for forbidden in [
            "Ethan Vale", "CloudFront", "d8j0ntlcm91z4", "hf_20260922",
            "I See Through the Wild", "<video", "21 stills"
        ]:
            self.assertNotIn(forbidden,self.html)

    def test_research_data_sources_remain_internal(self):
        for forbidden in [
            "Empire Flippers","empireflippers","OFFICIAL_API",
            "listing_number","source_url","source_updated_at","OPP_V0.2",
            "原始项目标识不对外展示","中文化与脱敏",
        ]:
            self.assertNotIn(forbidden,self.html)
        self.assertIn("数据供应商",self.cfg["content_policy"]["source_protection"])

    def test_navigation_filters_and_detail_interaction_exist(self):
        structure=_Structure()
        structure.feed(self.html)
        self.assertEqual(len(structure.ids),len(set(structure.ids)))
        self.assertGreaterEqual(structure.buttons,6)
        for value in [
            'data-filter="all"', 'data-filter="digital"', 'data-filter="content"',
            'data-filter="commerce"', 'data-filter="service"',
            'id="overview"', 'id="detail"', 'id="detail-articles"',
            'addEventListener("hashchange"', 'aria-pressed',
        ]:
            self.assertIn(value,self.html)

    def test_content_hierarchy_is_business_first(self):
        for title in [
            "这门生意具体做什么？",
            "收入从哪里来？",
            "通常需要做哪些工作？",
            "海外有哪些参考？",
            "还需要确认什么？",
        ]:
            self.assertIn(title,self.html)
        self.assertEqual([x["id"] for x in self.cfg["business_models"] if x["depth"]=="FULL_SAMPLE"],["digital","kdp"])

    def test_isolated_from_production_build(self):
        self.assertNotIn("web/prototypes/p412a",self.build)
        self.assertIn("P4.12A-V1",self.cfg["version"])
        self.assertEqual(self.cfg["publication_state"],"DESIGN_REVIEW_ONLY")
        self.assertNotIn("p412a",self.build.lower())

if __name__=="__main__":
    unittest.main()
