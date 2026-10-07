import json
import unittest
from pathlib import Path


class TestP34PartnerOutreachPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads(Path("config/partner_outreach_v1.json").read_text(encoding="utf-8"))
        cls.plan=Path("docs/P34_PARTNERSHIP_OUTREACH_PLAN.md").read_text(encoding="utf-8")

    def test_first_wave_matches_product_fit(self):
        self.assertEqual(self.cfg["first_wave"],["acquire","microns","flippa"])
        self.assertIn("fe_international",self.cfg["second_wave"])

    def test_outreach_stays_non_mirroring(self):
        self.assertFalse(self.cfg["full_listing_mirror"])
        self.assertFalse(self.cfg["private_data_request"])
        self.assertEqual(self.cfg["request_mode"],"LIMITED_PUBLIC_FIELDS_PLUS_ATTRIBUTION_AND_REFERRAL")

    def test_external_send_is_not_automatic(self):
        self.assertTrue(self.cfg["send_requires_user_confirmation"])
        self.assertFalse(self.cfg["paid_license_auto_accept"])

    def test_plan_is_partner_value_first(self):
        self.assertIn("新增中文市场的高意向流量",self.plan)
        self.assertIn("不复制完整 listing",self.plan)
        self.assertIn("不虚构用户数",self.plan)
        self.assertIn("原始 listing deep link",self.plan)


if __name__=="__main__":
    unittest.main()
