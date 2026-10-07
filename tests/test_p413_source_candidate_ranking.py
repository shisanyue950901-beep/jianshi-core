import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestP413SourceCandidateRanking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "config/source_candidate_ranking_v2.json").read_text(encoding="utf-8"))
        cls.doc = (ROOT / "docs/P413_SOURCE_CANDIDATE_RANKING.md").read_text(encoding="utf-8")

    def test_next_staging_target_is_pypi(self):
        self.assertEqual(self.cfg["next_step"], "PYPI_STAGING_ONLY")
        self.assertEqual(self.cfg["ranking"][0]["source"], "pypi")
        self.assertEqual(self.cfg["ranking"][0]["decision"], "NEXT_STAGING_TARGET")

    def test_source_count_is_not_kpi(self):
        self.assertFalse(self.cfg["source_count_is_kpi"])
        self.assertTrue(self.cfg["policy_veto_overrides_score"])

    def test_no_production_change_in_audit(self):
        self.assertFalse(self.cfg["production_change"])
        self.assertIn("P413_NO_PRODUCTION_CHANGE = TRUE", self.doc)

    def test_high_value_but_policy_constrained_sources_stay_held(self):
        decisions = {x["source"]: x["decision"] for x in self.cfg["ranking"]}
        self.assertEqual(decisions["wordpress_plugins"], "POLICY_REVIEW_THEN_INTEGRATE")
        self.assertEqual(decisions["youtube_data_api"], "HOLD_POLICY_MISMATCH")
        self.assertEqual(decisions["jetbrains_marketplace"], "HOLD_WRITTEN_PERMISSION")


if __name__ == "__main__":
    unittest.main()
