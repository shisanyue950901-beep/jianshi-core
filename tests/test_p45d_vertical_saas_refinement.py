import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestP45DVerticalSaaSRefinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=(ROOT/"db/migrations/0058_vertical_saas_rule_refinement.sql").read_text(encoding="utf-8")
        cls.doc=(ROOT/"docs/P45D_VERTICAL_SAAS_REVIEW_REFINEMENT.md").read_text(encoding="utf-8")

    def test_old_broad_rule_is_disabled(self):
        self.assertIn("rule_code='P45B_SAAS_VERTICAL'",self.sql)
        self.assertIn("active=false",self.sql)

    def test_primary_saas_rule_is_high_auto(self):
        self.assertIn("P45D_SAAS_PRIMARY_TITLE",self.sql)
        self.assertIn("SaaS Business",self.sql)
        self.assertIn("'HIGH'",self.sql)
        self.assertIn("true,",self.sql)

    def test_mixed_subscription_rule_stays_reviewable(self):
        self.assertIn("P45D_SAAS_SUBSCRIPTION_MIXED",self.sql)
        self.assertIn("Subscription Business",self.sql)
        self.assertIn("'MEDIUM'",self.sql)
        self.assertIn("false,",self.sql)

    def test_digital_product_primary_is_not_promoted_by_new_rules(self):
        self.assertNotIn("Digital Product Business",self.sql)
        self.assertIn("EXCLUDE_FROM_VERTICAL_SAAS_MAPPING",self.doc)

    def test_rule_version_and_expected_counts_are_documented(self):
        self.assertIn("P45D_V1",self.sql)
        self.assertIn("auto approved = 4",self.doc)
        self.assertIn("review required = 1",self.doc)
        self.assertIn("excluded = 1",self.doc)

    def test_no_production_or_publication_changes(self):
        lower=self.sql.lower()
        self.assertNotIn("cron.schedule",lower)
        self.assertNotIn("update opportunities set",lower)
        self.assertNotIn("public_opportunity_catalog_v01",lower)

if __name__=="__main__":
    unittest.main()
