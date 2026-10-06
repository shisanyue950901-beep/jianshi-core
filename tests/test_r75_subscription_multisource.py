import subprocess, sys, unittest
from pathlib import Path

class TestR75SubscriptionAndMultisource(unittest.TestCase):
    def test_multisource_mapping_contract(self):
        sql=Path("db/migrations/0021_expand_multisource_github_mapping.sql").read_text(encoding="utf-8")
        for token in [
            "ecommerce","affiliate_marketing","newsletter","youtube",
            "opportunity_github_query_map","refresh_opportunity_evidence_v01",
            "ecommerce-brands","affiliate-content","creator-media"
        ]:
            self.assertIn(token,sql)

    def test_newsletter_privacy_contract(self):
        sql=Path("db/migrations/0022_newsletter_waitlist.sql").read_text(encoding="utf-8")
        for token in [
            "PENDING_CONFIRMATION","ACTIVE","UNSUBSCRIBED",
            "confirmation_token_hash","unsubscribe_token_hash",
            "enable row level security","10 minutes",
            "request_newsletter_subscription_v01",
            "confirm_newsletter_subscription_v01",
            "unsubscribe_newsletter_v01",
            "service_role"
        ]:
            self.assertIn(token,sql)
        self.assertIn("revoke all on newsletter_subscribers,newsletter_events from anon,authenticated",sql)

    def test_newsletter_edge_contract(self):
        fn=Path("supabase/functions/newsletter-subscribe/index.ts").read_text(encoding="utf-8")
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY",fn)
        self.assertIn("Honeypot",fn)
        self.assertIn("sha256Hex",fn)
        self.assertIn("WAITLIST",fn)
        self.assertIn("CONFIRMATION_QUEUED",fn)
        self.assertNotIn('message: "确认邮件已发送',fn)

    def test_public_signup_ui(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        home=Path("web/dist/index.html").read_text(encoding="utf-8")
        js=Path("web/dist/search.js").read_text(encoding="utf-8")
        self.assertIn("每天把 Top 10 机会发给我",home)
        self.assertIn("不需要注册账号",home)
        self.assertIn("未确认前不会发送每日邮件",home)
        self.assertIn("data-newsletter-form",home)
        self.assertIn("newsletter-subscribe",Path("web/build.py").read_text(encoding="utf-8"))
        self.assertIn("source_path",js)
        self.assertIn("fetch(endpoint",js)

if __name__=="__main__":
    unittest.main()
