import unittest
from pathlib import Path

class TestR82WatchlistAlertEngine(unittest.TestCase):
    def test_alert_schema_and_rls(self):
        sql=Path("db/migrations/0033_watchlist_alert_engine.sql").read_text(encoding="utf-8")
        for token in [
            "user_alert_events",
            "NEWLY_VALIDATED",
            "NEW_EVIDENCE",
            "SCORE_CHANGE",
            "enable row level security",
            "user_id=auth.uid()",
            "refresh_user_alert_events_v01",
            "my_alert_events_v01",
            "unique(watchlist_item_id,event_date,event_type)",
        ]:
            self.assertIn(token,sql)

    def test_alert_rules_use_existing_watch_preferences(self):
        sql=Path("db/migrations/0033_watchlist_alert_engine.sql").read_text(encoding="utf-8")
        self.assertIn("wi.alert_on_validation=true",sql)
        self.assertIn("wi.alert_on_new_evidence=true",sql)
        self.assertIn("wi.alert_on_score_change=true",sql)
        self.assertIn("abs(c.overall_delta_1d)>=wi.score_change_threshold",sql)

    def test_no_email_delivery_in_r82(self):
        sql=Path("db/migrations/0033_watchlist_alert_engine.sql").read_text(encoding="utf-8")
        self.assertNotIn("resend_api_key",sql)
        self.assertNotIn("net.http_post",sql)

    def test_runtime_order(self):
        runtime=Path("db/runtime/schedule_user_alerts.sql.template").read_text(encoding="utf-8")
        self.assertIn("jianshi-user-alerts-6h",runtime)
        self.assertIn("50 */6 * * *",runtime)

if __name__=="__main__":
    unittest.main()
