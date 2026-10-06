import json, unittest
from pathlib import Path

class TestR76SourcePolicy(unittest.TestCase):
    def test_registry_marketplace_policy(self):
        d=json.loads(Path("config/source_registry.json").read_text(encoding="utf-8"))
        by={x["code"]:x for x in d["sources"]}
        self.assertEqual(by["acquire"]["status"],"RED")
        self.assertFalse(by["acquire"]["auto_collect"])
        self.assertFalse(by["acquire"]["redisplay_allowed"])
        self.assertTrue(by["acquire"]["written_permission_required"])

        for code in ("trustmrr","catchbuys","acquirebase","sideprojectors"):
            self.assertEqual(by[code]["status"],"YELLOW")
            self.assertFalse(by[code]["auto_collect"])
            self.assertFalse(by[code]["redisplay_allowed"])
            self.assertFalse(by[code]["derived_public_analytics_allowed"])

        self.assertEqual(by["deal_slide"]["status"],"RED")
        self.assertTrue(by["empire_flippers"]["auto_collect"])
        self.assertTrue(by["empire_flippers"]["redisplay_allowed"])

    def test_db_publication_gate_contract(self):
        m24=Path("db/migrations/0024_marketplace_source_policy_v2.sql").read_text(encoding="utf-8")
        m25=Path("db/migrations/0025_green_source_policy_normalization.sql").read_text(encoding="utf-8")
        self.assertIn("source_permission_requests",m24)
        self.assertIn("assert_source_publication_allowed_v01",m24)
        self.assertIn("PUBLICATION_FORBIDDEN_BY_SOURCE_POLICY",m25)
        self.assertIn("derived_public_analytics_allowed is not true",m25)
        self.assertIn("OFFICIAL_API_EXPLICIT_SYNDICATION_PERMISSION",m25)

if __name__=="__main__":
    unittest.main()
