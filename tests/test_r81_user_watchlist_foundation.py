import unittest
from pathlib import Path

class TestR81UserWatchlistFoundation(unittest.TestCase):
    def test_private_user_schema(self):
        sql=Path("db/migrations/0032_user_watchlist_foundation.sql").read_text(encoding="utf-8")
        for token in [
            "user_profiles",
            "saved_opportunities",
            "watchlists",
            "watchlist_items",
            "alert_preferences",
            "references auth.users(id) on delete cascade",
            "enable row level security",
            "auth.uid()",
            "handle_new_auth_user_v01",
            "on_auth_user_created_jianshi",
            "我的观察清单",
            "my_saved_opportunities_v01",
            "my_watchlist_items_v01",
        ]:
            self.assertIn(token,sql)

    def test_anon_has_no_private_grants(self):
        sql=Path("db/migrations/0032_user_watchlist_foundation.sql").read_text(encoding="utf-8")
        self.assertIn(
            "revoke all on user_profiles,saved_opportunities,watchlists,watchlist_items,alert_preferences",
            sql,
        )
        self.assertIn("from anon,authenticated",sql)
        self.assertIn("revoke all on my_saved_opportunities_v01,my_watchlist_items_v01 from anon",sql)

    def test_alerts_are_prepared_not_enabled_by_default(self):
        sql=Path("db/migrations/0032_user_watchlist_foundation.sql").read_text(encoding="utf-8")
        self.assertIn("email_enabled boolean not null default false",sql)
        self.assertIn("daily_digest_enabled boolean not null default false",sql)
        self.assertIn("weekly_digest_enabled boolean not null default false",sql)

if __name__=="__main__":
    unittest.main()
