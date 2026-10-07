import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestP412StackExchangeDemandSignals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = (ROOT / "db/migrations/0051_stackexchange_demand_queries.sql").read_text(encoding="utf-8")
        cls.cron = (ROOT / "db/migrations/0052_stackexchange_signal_cron.sql").read_text(encoding="utf-8")
        cls.edge = (ROOT / "supabase/functions/collect-stackexchange-signals/index.ts").read_text(encoding="utf-8")

    def test_queries_use_shadow_demand_evidence(self):
        self.assertIn("STACKEXCHANGE_TAG_COUNT", self.sql)
        self.assertIn("'STACKEXCHANGE_TAG'", self.sql)
        for tag in ["openai-api", "langchain", "shopify", "stripe", "saas", "youtube-api"]:
            self.assertIn(tag, self.sql)

    def test_collector_uses_official_count_only_api(self):
        self.assertIn("https://api.stackexchange.com/2.3/search", self.edge)
        self.assertIn('url.searchParams.set("filter", "total")', self.edge)
        self.assertIn('url.searchParams.set("fromdate"', self.edge)
        self.assertIn("questions_7d", self.edge)
        self.assertIn("questions_30d", self.edge)
        self.assertIn("fulltext_stored: false", self.edge)
        for forbidden in ["body_markdown", "question.body", "owner.display_name"]:
            self.assertNotIn(forbidden, self.edge)

    def test_source_policy_gate_is_required(self):
        self.assertIn('source.source_status === "GREEN"', self.edge)
        self.assertIn("commercial_use_allowed", self.edge)
        self.assertIn("automated_collection_allowed", self.edge)
        self.assertIn("redisplay_allowed", self.edge)

    def test_scoring_is_not_changed(self):
        lower = self.sql.lower()
        self.assertNotIn("opportunity_rank_current", lower)
        self.assertNotIn("public_opportunity_catalog_v01", lower)
        self.assertIn("scoring_changed: false", self.edge)

    def test_six_hour_cron(self):
        self.assertIn("jianshi-stackexchange-signals-6h", self.cron)
        self.assertIn("37 */6 * * *", self.cron)
        self.assertIn("collect-stackexchange-signals", self.cron)


if __name__ == "__main__":
    unittest.main()
