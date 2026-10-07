import os, subprocess, sys, unittest
from pathlib import Path

class TestR84AccountWriteApi(unittest.TestCase):
    def test_write_api_contract(self):
        sql=Path("db/migrations/0035_account_write_api.sql").read_text(encoding="utf-8")
        for token in [
            "save_my_opportunity_v01",
            "watch_my_opportunity_v01",
            "mark_my_alert_read_v01",
            "auth.uid()",
            "security definer",
            "revoke all on saved_opportunities from authenticated",
            "revoke all on watchlists from authenticated",
            "revoke all on watchlist_items from authenticated",
            "revoke all on user_alert_events from authenticated",
        ]:
            self.assertIn(token.lower() if token=="security definer" else token, sql.lower() if token=="security definer" else sql)

    def test_client_has_no_direct_account_table_writes(self):
        js=Path("web/static/account.js").read_text(encoding="utf-8")
        self.assertIn("save_my_opportunity_v01",js)
        self.assertIn("watch_my_opportunity_v01",js)
        self.assertIn("mark_my_alert_read_v01",js)
        self.assertNotIn('supabase.from("saved_opportunities")',js)
        self.assertNotIn('supabase.from("watchlist_items")',js)
        self.assertNotIn('.from("watchlists")',js)

    def test_default_production_build_stays_closed(self):
        env=os.environ.copy()
        env["JIANSHI_AUTH_ENABLED"]="0"
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True,env=env)
        home=Path("web/dist/index.html").read_text(encoding="utf-8")
        account=Path("web/dist/account/index.html").read_text(encoding="utf-8")
        self.assertNotIn('href="/account/"',home)
        self.assertNotIn("data-auth-email-form",account)
        self.assertIn("账户功能正在完成最后的邮件登录配置",account)

if __name__=="__main__":
    unittest.main()
