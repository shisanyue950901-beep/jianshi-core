import unittest
from pathlib import Path


class TestP3HighQualityCommercialSources(unittest.TestCase):
    def test_quality_layer_contract(self):
        sql=Path("db/migrations/0043_high_quality_commercial_source_layer.sql").read_text(encoding="utf-8")
        for token in [
            "commercial_market_source_tiers",
            "commercial_market_source_priority_v01",
            "empire_flippers",
            "acquire",
            "fe_international",
            "flippa",
            "microns",
            "investors_club",
            "motion_invest",
            "WRITTEN_DATA_LICENSE_OR_AUTHORIZED_PARTNER_FEED_REQUIRED",
        ]:
            self.assertIn(token,sql)

    def test_restricted_sources_remain_fail_closed(self):
        sql=Path("db/migrations/0043_high_quality_commercial_source_layer.sql").read_text(encoding="utf-8")
        self.assertIn("auto_collect=false",sql)
        self.assertIn("redisplay_allowed=false",sql)
        self.assertIn("written_permission_required",sql)
        self.assertNotIn("source_status='GREEN'",sql)

    def test_permission_scopes_are_explicit(self):
        sql=Path("db/migrations/0043_high_quality_commercial_source_layer.sql").read_text(encoding="utf-8")
        for scope in [
            "AUTOMATED_API_OR_FEED",
            "HISTORICAL_SNAPSHOT_STORAGE",
            "DERIVED_ANALYTICS",
            "PUBLIC_SUMMARY_DISPLAY",
            "COMMERCIAL_PRODUCT_USE",
        ]:
            self.assertIn(scope,sql)

    def test_strategy_doc_preserves_no_scrape_rule(self):
        doc=Path("docs/P3_HIGH_QUALITY_COMMERCIAL_SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("Acquire.com",doc)
        self.assertIn("直接抓 Acquire",doc)
        self.assertIn("Written Reply → Policy Review",doc)


if __name__=="__main__":
    unittest.main()
