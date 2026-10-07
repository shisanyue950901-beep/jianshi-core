import unittest
from pathlib import Path


class TestP11NewsletterLaunchGate(unittest.TestCase):
    def test_launch_gate_is_fail_closed(self):
        sql=Path("db/migrations/0042_newsletter_launch_gate.sql").read_text(encoding="utf-8")
        for token in [
            "newsletter_launch_control",
            "newsletter_launch_ready_v01",
            "newsletter_provider_ready_v01",
            "sender_domain_verified",
            "confirmation_e2e_pass",
            "daily_digest_e2e_pass",
            "unsubscribe_e2e_pass",
            "bounce_complaint_handling_pass",
            "security_review_pass",
            "default false",
        ]:
            self.assertIn(token,sql)

    def test_public_send_paths_use_launch_gate(self):
        for path in [
            "supabase/functions/newsletter-subscribe/index.ts",
            "supabase/functions/newsletter-dispatch-confirmations/index.ts",
            "supabase/functions/newsletter-daily/index.ts",
        ]:
            body=Path(path).read_text(encoding="utf-8")
            self.assertIn("newsletter_launch_ready_v01",body)

    def test_cron_workers_report_closed_gate_without_sending(self):
        for path in [
            "supabase/functions/newsletter-dispatch-confirmations/index.ts",
            "supabase/functions/newsletter-daily/index.ts",
        ]:
            body=Path(path).read_text(encoding="utf-8")
            self.assertIn("NEWSLETTER_LAUNCH_GATE_CLOSED",body)
            self.assertIn("launch_ready",body)

    def test_frontend_resets_after_confirmation_queue(self):
        body=Path("web/static/search.js").read_text(encoding="utf-8")
        self.assertIn("CONFIRMATION_QUEUED",body)


if __name__=="__main__":
    unittest.main()
