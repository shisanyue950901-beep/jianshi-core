import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"config"/"p48d_user_test_review_gate.json"
DOC=ROOT/"docs"/"P48D_FIRST_REVIEW_GATE.md"


class TestP48DFirstReviewGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads(CFG.read_text(encoding="utf-8"))
        cls.doc=DOC.read_text(encoding="utf-8")

    def test_first_review_gate_is_sample_not_success_threshold(self):
        self.assertEqual(
            self.cfg["minimum_target_detail_sessions_before_first_review"],30
        )
        self.assertFalse(self.cfg["fixed_success_thresholds"])
        self.assertEqual(
            self.cfg["first_review_gate"],
            "target_detail_sessions >= 30"
        )
        self.assertIn("不是成功阈值",self.doc)

    def test_business_scoring_cannot_be_changed_from_early_usage(self):
        prohibited=set(self.cfg["pre_gate_prohibited_changes"])
        for token in [
            "RECOMMENDATION_STATUS","OPP_V0.2","PROJECT_RANKING",
            "SOURCE_EXPANSION","NOINDEX_BOUNDARY","AUTH_LAUNCH"
        ]:
            self.assertIn(token,prohibited)

    def test_only_quality_defects_can_bypass_sample_gate(self):
        allowed=set(self.cfg["pre_gate_allowed_changes"])
        self.assertEqual(allowed,{
            "FUNCTIONAL_BUG",
            "FACTUAL_ERROR",
            "SEVERE_MISLEADING_COPY",
            "ANALYTICS_FAILURE",
            "ACCESSIBILITY_BLOCKER",
        })

    def test_four_funnel_layers_are_frozen(self):
        self.assertEqual(
            self.cfg["primary_metrics"],
            [
                "entry_click_rate_pct",
                "engaged_30s_rate_pct",
                "scroll_90_rate_pct",
                "second_target_project_rate_pct",
            ],
        )
        self.assertEqual(len(self.cfg["diagnostic_order"]),4)

    def test_no_outreach_is_claimed(self):
        self.assertFalse(self.cfg["outreach_sent"])
        self.assertIn("P48D_OUTREACH_SENT = FALSE",self.doc)


if __name__=="__main__":
    unittest.main()
