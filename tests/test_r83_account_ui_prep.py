import os, subprocess, sys, unittest
from pathlib import Path

class TestR83AccountUiPrep(unittest.TestCase):
    def build(self, enabled=False):
        env=os.environ.copy()
        env["JIANSHI_AUTH_ENABLED"]="1" if enabled else "0"
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True,env=env)

    def test_account_read_api_is_narrow(self):
        sql=Path("db/migrations/0034_account_read_api.sql").read_text(encoding="utf-8")
        for token in [
            "get_my_saved_opportunities_v01",
            "get_my_watchlist_items_v01",
            "get_my_alert_events_v01",
            "security definer",
            "auth.uid()",
            "grant execute",
        ]:
            self.assertIn(token,sql.lower() if token=="security definer" else sql)
        self.assertNotIn("grant select on opportunities to authenticated",sql.lower())

    def test_default_build_is_fail_closed(self):
        self.build(False)
        home=Path("web/dist/index.html").read_text(encoding="utf-8")
        account=Path("web/dist/account/index.html").read_text(encoding="utf-8")
        detail=Path("web/dist/opportunity/solo-saas/index.html").read_text(encoding="utf-8")
        self.assertNotIn('href="/account/"',home)
        self.assertIn("账户功能正在完成最后的邮件登录配置",account)
        self.assertIn('name="robots" content="noindex,nofollow"',account)
        self.assertNotIn("data-auth-email-form",account)
        self.assertNotIn("data-save-opportunity",detail)

    def test_enabled_build_contains_account_actions(self):
        self.build(True)
        home=Path("web/dist/index.html").read_text(encoding="utf-8")
        account=Path("web/dist/account/index.html").read_text(encoding="utf-8")
        detail=Path("web/dist/opportunity/solo-saas/index.html").read_text(encoding="utf-8")
        js=Path("web/dist/account.js").read_text(encoding="utf-8")
        self.assertIn('href="/account/"',home)
        self.assertIn("data-auth-email-form",account)
        self.assertIn("发送登录链接",account)
        self.assertIn("data-save-opportunity",detail)
        self.assertIn("data-watch-opportunity",detail)
        self.assertIn("@supabase/supabase-js@2.117.1",js)
        self.assertIn("get_my_saved_opportunities_v01",js)
        self.assertIn("get_my_watchlist_items_v01",js)
        self.assertIn("get_my_alert_events_v01",js)
        # Restore the default production artifact contract.
        self.build(False)

if __name__=="__main__":
    unittest.main()
