import os, subprocess, sys, unittest
from pathlib import Path

class TestR85AccountLifecycle(unittest.TestCase):
    def test_lifecycle_rpc_contract(self):
        sql=Path("db/migrations/0036_account_lifecycle.sql").read_text(encoding="utf-8")
        for token in [
            "unsave_my_opportunity_v01",
            "unwatch_my_opportunity_v01",
            "get_my_alert_preferences_v01",
            "update_my_alert_preferences_v01",
            "clear_my_jianshi_data_v01",
            "auth.uid()",
            "auth_account_deleted",
        ]:
            self.assertIn(token,sql)
        self.assertIn("'auth_account_deleted',false",sql)

    def test_account_client_uses_lifecycle_rpcs(self):
        js=Path("web/static/account.js").read_text(encoding="utf-8")
        for token in [
            "unsave_my_opportunity_v01",
            "unwatch_my_opportunity_v01",
            "get_my_alert_preferences_v01",
            "update_my_alert_preferences_v01",
            "clear_my_jianshi_data_v01",
            "mark_my_alert_read_v01",
        ]:
            self.assertIn(token,js)
        self.assertIn('$$(["[data-alert-id]"])'.replace('["','"').replace('"]','"'),js)
        self.assertNotIn('$(["[data-alert-id]"]).forEach'.replace('["','"').replace('"]','"'),js)

    def test_enabled_account_has_management_ui(self):
        env=os.environ.copy()
        env["JIANSHI_AUTH_ENABLED"]="1"
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True,env=env)
        account=Path("web/dist/account/index.html").read_text(encoding="utf-8")
        self.assertIn("提醒偏好",account)
        self.assertIn("保存提醒偏好",account)
        self.assertIn("清空我的见势数据",account)
        self.assertIn("不会删除你的登录账号",account)
        env["JIANSHI_AUTH_ENABLED"]="0"
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True,env=env)

if __name__=="__main__":
    unittest.main()
