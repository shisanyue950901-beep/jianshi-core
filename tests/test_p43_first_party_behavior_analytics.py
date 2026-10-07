import json
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestP43FirstPartyBehaviorAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = (ROOT / "db/migrations/0050_first_party_behavior_analytics.sql").read_text(encoding="utf-8")
        cls.edge = (ROOT / "supabase/functions/behavior-track/index.ts").read_text(encoding="utf-8")
        cls.client = (ROOT / "web/static/analytics.js").read_text(encoding="utf-8")
        cls.build = (ROOT / "web/build.py").read_text(encoding="utf-8")
        cls.cfg = json.loads((ROOT / "config/behavior_analytics_v1.json").read_text(encoding="utf-8"))
        cls.workflow = (ROOT / ".github/workflows/publish-static.yml").read_text(encoding="utf-8")

    def test_private_event_store(self):
        self.assertIn("create table if not exists behavior_events", self.sql.lower())
        self.assertIn("enable row level security", self.sql.lower())
        self.assertIn("from public,anon,authenticated", self.sql)
        self.assertIn("to service_role", self.sql)
        self.assertIn("record_behavior_event_v01", self.sql)

    def test_privacy_minimization_contract(self):
        self.assertFalse(self.cfg["persist_ip"])
        self.assertFalse(self.cfg["persist_user_agent"])
        self.assertFalse(self.cfg["persist_email_or_name"])
        self.assertFalse(self.cfg["persist_full_search_text"])
        self.assertEqual(self.cfg["raw_event_retention_days"], 90)
        for forbidden in ["ip_address", "user_agent", "email"]:
            self.assertNotIn(forbidden, self.sql.lower())

    def test_client_respects_privacy_controls(self):
        self.assertIn("globalPrivacyControl", self.client)
        self.assertIn("doNotTrack", self.client)
        self.assertIn("jianshi_analytics_opt_out", self.client)
        self.assertIn("query_length", self.client)
        self.assertNotIn("query_text", self.client)
        self.assertIn("SECOND_OPPORTUNITY_VIEW", self.client)
        self.assertIn("ENGAGED_30S", self.client)
        self.assertIn("SCROLL_90", self.client)

    def test_edge_is_origin_and_payload_gated(self):
        self.assertIn("ORIGIN_FORBIDDEN", self.edge)
        self.assertIn("PAYLOAD_TOO_LARGE", self.edge)
        self.assertIn("cleanMetadata", self.edge)
        self.assertIn("record_behavior_event_v01", self.edge)
        self.assertNotIn("x-forwarded-for", self.edge.lower())

    def test_analytics_does_not_change_business_gates(self):
        lower = self.sql.lower()
        self.assertNotIn("opportunity_rank_current", lower)
        self.assertNotIn("public_opportunity_catalog_v01", lower)
        self.assertNotIn("product_feature_flags", lower)
        self.assertNotIn("newsletter_launch", lower)

    def test_static_build_wires_analytics(self):
        self.assertIn("JIANSHI_ANALYTICS_URL", self.build)
        self.assertIn('STATIC/"analytics.js"', self.build)
        self.assertIn('src="/analytics.js"', self.build)
        self.assertIn("data-analytics-opt-out", self.build)
        self.assertIn("analytics.js", self.workflow)

    def test_fixture_build_emits_disabled_analytics_config(self):
        env = os.environ.copy()
        env.pop("JIANSHI_API_URL", None)
        env.pop("JIANSHI_ANALYTICS_URL", None)
        subprocess.run(
            ["python", "web/build.py"],
            cwd=ROOT,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        html = (ROOT / "web/dist/index.html").read_text(encoding="utf-8")
        self.assertIn("JIANSHI_ANALYTICS_CONFIG", html)
        self.assertIn('"enabled":false', html)
        self.assertTrue((ROOT / "web/dist/analytics.js").exists())


if __name__ == "__main__":
    unittest.main()
