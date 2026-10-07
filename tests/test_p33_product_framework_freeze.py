import json
import unittest
from pathlib import Path


class TestP33ProductFrameworkFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads(Path("config/product_framework_v1.json").read_text(encoding="utf-8"))
        cls.doc=Path("docs/P33_PRODUCT_FRAMEWORK_FREEZE.md").read_text(encoding="utf-8")

    def test_core_positioning_is_frozen(self):
        c=self.contract
        self.assertEqual(c["status"],"FROZEN")
        self.assertEqual(c["product_category"],"商业机会发现与决策平台")
        self.assertEqual(c["primary_user"],"中国个人创业者")
        self.assertEqual(c["secondary_user"],"内容创作者")
        self.assertFalse(c["frontend_overseas_narrative"])
        self.assertTrue(c["opportunity_is_product"])
        self.assertFalse(c["raw_source_is_product"])

    def test_scoring_and_source_gates_remain_frozen(self):
        c=self.contract
        self.assertEqual(c["score_model"],"OPP_V0.2")
        self.assertEqual(c["score_dimensions"],["HEAT","CONTENT","BUILD","BUSINESS"])
        self.assertFalse(c["public_ready_gate_change_allowed"])
        self.assertTrue(c["source_policy_fail_closed"])
        self.assertFalse(c["full_listing_mirror_allowed"])

    def test_access_model_is_value_progression(self):
        c=self.contract
        self.assertIn("四维评分",c["public_access"])
        self.assertIn("完整机会分析",c["registered_target_access"])
        self.assertIn("收藏",c["registered_target_access"])
        self.assertEqual(c["registered_analysis_model"],"TARGET")

    def test_outreach_waits_for_freeze(self):
        c=self.contract
        self.assertFalse(c["partnership_outreach_before_freeze"])
        self.assertEqual(c["outreach_priority_target"][:3],["acquire","microns","flippa"])

    def test_doc_contains_non_mirror_and_dual_view_rules(self):
        self.assertIn("Opportunity 才是产品",self.doc)
        self.assertIn("创业者与创作者",self.doc)
        self.assertIn("不复制完整 listing",self.doc)
        self.assertIn("原站导流",self.doc)


if __name__=="__main__":
    unittest.main()
