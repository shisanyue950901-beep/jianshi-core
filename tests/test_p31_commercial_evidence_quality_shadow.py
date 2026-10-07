import unittest
from pathlib import Path


class TestP31CommercialEvidenceQualityShadow(unittest.TestCase):
    def test_shadow_model_contract(self):
        sql=Path("db/migrations/0044_commercial_evidence_quality_shadow.sql").read_text(encoding="utf-8")
        for token in [
            "commercial_source_quality_rules",
            "commercial_evidence_quality_shadow_v01",
            "quality_weighted_evidence_count",
            "avg_source_quality_weight",
            "eligible_commercial_source_count",
            "source_status='GREEN'",
            "commercial_use_allowed=true",
            "automated_collection_allowed=true",
            "derived_public_analytics_allowed=true",
        ]:
            self.assertIn(token,sql)

    def test_quality_never_opens_restricted_sources(self):
        sql=Path("db/migrations/0044_commercial_evidence_quality_shadow.sql").read_text(encoding="utf-8")
        self.assertIn("'quiet_light','Quiet Light'",sql)
        self.assertIn("'startupmkt','StartupMKT'",sql)
        self.assertIn("auto_collect,false",sql.replace(" ",""))
        self.assertIn("redisplay_allowed,false",sql.replace(" ",""))
        self.assertNotIn("source_status='GREEN'", sql.split("insert into data_sources",1)[1].split("create table if not exists commercial_source_quality_rules",1)[0])

    def test_no_score_or_public_ready_redefinition(self):
        sql=Path("db/migrations/0044_commercial_evidence_quality_shadow.sql").read_text(encoding="utf-8")
        self.assertNotIn("create or replace view opportunity_rank_current",sql.lower())
        self.assertNotIn("create or replace view opportunity_scored_v01",sql.lower())
        self.assertNotIn("update score_snapshots",sql.lower())

    def test_new_candidates_have_permission_drafts(self):
        sql=Path("db/migrations/0044_commercial_evidence_quality_shadow.sql").read_text(encoding="utf-8")
        self.assertIn("quiet_light",sql)
        self.assertIn("startupmkt",sql)
        for scope in [
            "AUTOMATED_API_OR_FEED",
            "HISTORICAL_SNAPSHOT_STORAGE",
            "DERIVED_ANALYTICS",
            "PUBLIC_SUMMARY_DISPLAY",
            "COMMERCIAL_PRODUCT_USE",
        ]:
            self.assertIn(scope,sql)


if __name__=="__main__":
    unittest.main()
