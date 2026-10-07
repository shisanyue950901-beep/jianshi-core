import unittest
from pathlib import Path

class TestR710NewsletterRuntime(unittest.TestCase):
    def test_sql_runtime_contract(self):
        sql=Path("db/migrations/0029_newsletter_runtime.sql").read_text(encoding="utf-8")
        for token in [
            "newsletter_signing_secret",
            "newsletter_daily_sends",
            "newsletter_unsubscribe_token_v01",
            "unsubscribe_newsletter_signed_v01",
            "request_newsletter_subscription_v02",
            "prepare_waitlist_confirmation_v01",
            "revert_pending_confirmation_to_waitlist_v01",
            "queue_newsletter_confirmation_v02",
            "queue_newsletter_daily_v01",
            "unique(subscriber_id,send_date)",
            "EMAIL_PROVIDER_NOT_CONFIGURED",
        ]:
            self.assertIn(token,sql)

    def test_subscribe_uses_v02_and_signed_unsubscribe(self):
        fn=Path("supabase/functions/newsletter-subscribe/index.ts").read_text(encoding="utf-8")
        self.assertIn("request_newsletter_subscription_v02",fn)
        self.assertIn("queue_newsletter_confirmation_v02",fn)
        self.assertIn("unsubscribe_newsletter_signed_v01",fn)
        self.assertIn("revert_pending_confirmation_to_waitlist_v01",fn)

    def test_confirmation_dispatch_fail_closed(self):
        fn=Path("supabase/functions/newsletter-dispatch-confirmations/index.ts").read_text(encoding="utf-8")
        self.assertIn("newsletter_launch_ready_v01",fn)
        self.assertIn("WAITLIST",fn)
        self.assertIn("prepare_waitlist_confirmation_v01",fn)
        self.assertIn("revert_pending_confirmation_to_waitlist_v01",fn)

    def test_daily_sender_contract(self):
        fn=Path("supabase/functions/newsletter-daily/index.ts").read_text(encoding="utf-8")
        self.assertIn("public_daily_brief_v01",fn)
        self.assertIn('eq("status", "ACTIVE")',fn)
        self.assertIn("newsletter_unsubscribe_token_v01",fn)
        self.assertIn("queue_newsletter_daily_v01",fn)
        self.assertIn("见势每日 Top 10",fn)

    def test_runtime_schedule(self):
        s=Path("db/runtime/schedule_newsletter.sql.template").read_text(encoding="utf-8")
        self.assertIn("jianshi-newsletter-confirmations-hourly",s)
        self.assertIn("12 * * * *",s)
        self.assertIn("jianshi-newsletter-daily-top10",s)
        self.assertIn("10 1 * * *",s)

if __name__=="__main__":
    unittest.main()
