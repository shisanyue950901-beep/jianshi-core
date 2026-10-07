import json
import unittest
from pathlib import Path


class TestP35BusinessModelStrategy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads(Path("config/business_model_v1.json").read_text(encoding="utf-8"))
        cls.doc=Path("docs/P35_BUSINESS_MODEL_AUDIT_AND_5Y_ROADMAP.md").read_text(encoding="utf-8")

    def test_business_model_is_managed_marketplace_not_open_store(self):
        c=self.cfg
        self.assertEqual(c["business_model"],"INTELLIGENCE_LED_MANAGED_MARKETPLACE")
        self.assertEqual(c["generic_agent_store"],"FORBIDDEN")
        self.assertEqual(c["generic_outsourcing_marketplace"],"FORBIDDEN")
        self.assertEqual(c["open_marketplace_before_gate_d"],"FORBIDDEN")

    def test_consulting_is_demand_discovery(self):
        c=self.cfg
        self.assertEqual(c["consulting"],"STRUCTURED_DEMAND_DISCOVERY")
        self.assertEqual(c["current_stage"],"OPPORTUNITY_INTELLIGENCE_VALIDATION")
        self.assertEqual(c["registration"],"NEXT_IDENTITY_LAYER")

    def test_enterprise_is_long_term_primary_revenue(self):
        c=self.cfg
        self.assertEqual(c["enterprise_role"],"LONG_TERM_PRIMARY_REVENUE")
        self.assertEqual(c["primary_moat"],"DEMAND_PLUS_DELIVERY_OUTCOMES")

    def test_transaction_infra_is_deferred(self):
        c=self.cfg
        self.assertEqual(c["transaction_infrastructure"],"DEFERRED")
        self.assertEqual(c["own_escrow_before_legal_payment_gate"],"FORBIDDEN")
        self.assertTrue(c["managed_matching_before_open_marketplace"])

    def test_doc_contains_stage_gates_and_failure_rules(self):
        self.assertIn("Gate A",self.doc)
        self.assertIn("Gate D",self.doc)
        self.assertIn("关键失败信号与转向规则",self.doc)
        self.assertIn("告诉见势你的业务问题",self.doc)
        self.assertIn("发现机会，让机会变成生意",self.doc)


if __name__=="__main__":
    unittest.main()
