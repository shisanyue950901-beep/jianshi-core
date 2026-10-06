import json, unittest
from pathlib import Path

class TestR79MarketplacePermissionQueue(unittest.TestCase):
    def test_new_sources_fail_closed(self):
        d=json.loads(Path("config/source_registry.json").read_text(encoding="utf-8"))
        by={x["code"]:x for x in d["sources"]}
        self.assertEqual(by["fe_international"]["status"],"RED")
        for code in ("investors_club","motion_invest"):
            self.assertEqual(by[code]["status"],"YELLOW")
        for code in ("fe_international","investors_club","motion_invest"):
            self.assertFalse(by[code]["auto_collect"])
            self.assertFalse(by[code]["redisplay_allowed"])
            self.assertFalse(by[code]["derived_public_analytics_allowed"])
            self.assertTrue(by[code]["written_permission_required"])

    def test_permission_scope_contract(self):
        sql=Path("db/migrations/0028_more_marketplace_permission_candidates.sql").read_text(encoding="utf-8")
        for token in [
            "AUTOMATED_API_OR_FEED",
            "HISTORICAL_SNAPSHOT_STORAGE",
            "DERIVED_ANALYTICS",
            "PUBLIC_SUMMARY_DISPLAY",
            "COMMERCIAL_PRODUCT_USE",
        ]:
            self.assertIn(token,sql)

if __name__=="__main__":
    unittest.main()
