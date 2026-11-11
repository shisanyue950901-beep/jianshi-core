import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestP45BChildEvidenceMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=(ROOT/"db/migrations/0055_child_evidence_mapping_shadow.sql").read_text(encoding="utf-8")
        cls.doc=(ROOT/"docs/P45B_CHILD_EVIDENCE_MAPPING_STAGING.md").read_text(encoding="utf-8")
        cls.fk=(ROOT/"db/migrations/0056_child_evidence_mapping_fk_indexes.sql").read_text(encoding="utf-8")

    def test_internal_shadow_tables_exist(self):
        for name in [
            "child_opportunity_shadow_registry",
            "child_marketplace_mapping_rules",
            "child_marketplace_evidence_matches",
            "child_evidence_mapping_summary_v01",
            "child_evidence_review_queue_v01",
        ]:
            self.assertIn(name,self.sql)

    def test_eight_mapping_rules_are_seeded(self):
        for code in [
            "P45B_SAAS_VERTICAL",
            "P45B_AFFILIATE_CONTENT_SITE",
            "P45B_AMAZON_FBA",
            "P45B_YOUTUBE_MEDIA",
            "P45B_DIGITAL_PRODUCT",
            "P45B_NEWSLETTER_MEDIA",
            "P45B_AMAZON_KDP",
            "P45B_NON_AMAZON_ECOMMERCE",
        ]:
            self.assertIn(code,self.sql)

    def test_saas_is_reviewed_not_autoapproved(self):
        self.assertIn("'MEDIUM',false,'Structured SaaS monetization",self.sql)
        self.assertIn("REVIEW_REQUIRED",self.sql)

    def test_exact_rules_are_autoapproved_but_not_published(self):
        self.assertIn("'HIGH',true,'Exact structured Amazon FBA monetization.'",self.sql)
        self.assertIn("'publication_changed',false",self.sql)
        self.assertNotIn("update opportunities set status",self.sql.lower())

    def test_refresh_is_fail_closed_and_idempotent(self):
        self.assertIn("refresh_child_marketplace_evidence_v01",self.sql)
        self.assertIn("set active=false",self.sql.lower())
        self.assertIn("on conflict(child_slug,listing_id,rule_id) do update",self.sql.lower())

    def test_service_role_only(self):
        self.assertIn("from public,anon,authenticated",self.sql)
        self.assertIn("to service_role",self.sql)

    def test_no_scoring_or_publication_gate_change(self):
        lower=self.sql.lower()
        self.assertNotIn("opportunity_rank_current",lower)
        self.assertNotIn("public_opportunity_catalog_v01",lower)
        self.assertNotIn("create or replace view public_opportunity_catalog_v01",lower)
        self.assertNotIn("update opportunities set",lower)
        self.assertIn("P4.5B does not create a Production schedule",self.sql)

    def test_foreign_keys_have_covering_indexes(self):
        self.assertIn("idx_child_registry_parent_opportunity", self.fk)
        self.assertIn("idx_child_evidence_matches_rule_id", self.fk)
        self.assertIn("idx_child_evidence_matches_source_id", self.fk)

    def test_no_cron(self):
        self.assertNotIn("cron.schedule",self.sql.lower())

if __name__=="__main__":
    unittest.main()
