import json
import unittest
from pathlib import Path


class TestP41SignalSourceExpansion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = Path("db/migrations/0047_signal_source_expansion_foundation.sql").read_text(encoding="utf-8")
        cls.cfg = json.loads(Path("config/source_expansion_v1.json").read_text(encoding="utf-8"))
        cls.doc = Path("docs/P41_SIGNAL_SOURCE_EXPANSION_AUDIT.md").read_text(encoding="utf-8")
        cls.cron = Path("db/migrations/0048_npm_signal_cron.sql").read_text(encoding="utf-8")
        cls.fk_fix = Path("db/migrations/0049_external_signal_fk_index.sql").read_text(encoding="utf-8")

    def test_source_policy_is_fail_closed(self):
        c = self.cfg["first_wave"]
        self.assertEqual(c["npm"], "GREEN_IMPLEMENT")
        self.assertEqual(c["stack_exchange"], "GREEN_NEXT")
        self.assertIn("PERMISSION_REQUIRED", c["product_hunt"])
        self.assertIn("CONTRACT_REQUIRED", c["reddit"])
        self.assertIn("ALPHA_ACCESS_REQUIRED", c["google_trends"])

    def test_new_evidence_is_shadow_only(self):
        self.assertTrue(self.cfg["public_ready_unchanged"])
        self.assertTrue(self.cfg["opp_v02_unchanged"])
        for evidence_type in self.cfg["shadow_only_evidence_types"]:
            self.assertIn(evidence_type, self.sql)
        self.assertIn("'NPM_PACKAGE','TECHNICAL_SUPPLY',false", self.sql)
        self.assertIn("'STACKEXCHANGE_TAG','DEMAND_SIGNAL',false", self.sql)

    def test_generic_signal_layer_is_internal(self):
        for table in [
            "external_signal_queries",
            "external_signal_entities",
            "external_signal_discoveries",
            "external_signal_snapshots",
            "opportunity_external_query_map",
        ]:
            self.assertIn(table, self.sql)
        self.assertIn("from public,anon,authenticated", self.sql)

    def test_no_scoring_gate_change(self):
        lower = self.sql.lower()
        self.assertNotIn("create or replace view opportunity_rank_current", lower)
        self.assertNotIn("create or replace view public_opportunity_catalog_v01", lower)
        self.assertNotIn("refresh_opportunity_scores_v01", lower)

    def test_npm_cron_is_internal_and_six_hourly(self):
        self.assertIn("jianshi-npm-signals-6h", self.cron)
        self.assertIn("27 */6 * * *", self.cron)
        self.assertIn("jianshi_publishable_key", self.cron)

    def test_external_signal_evidence_fk_is_indexed(self):
        self.assertIn("idx_external_signal_queries_evidence_type", self.fk_fix)
        self.assertIn("external_signal_queries(evidence_type)", self.fk_fix)

    def test_quality_not_source_count(self):
        self.assertFalse(self.cfg["source_count_is_kpi"])
        self.assertIn("不直接人工批量创建 50 个 ACTIVE Opportunity", self.doc)


if __name__ == "__main__":
    unittest.main()
