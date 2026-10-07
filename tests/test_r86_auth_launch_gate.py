import os, subprocess, sys, unittest
from pathlib import Path

class TestR86AuthLaunchGate(unittest.TestCase):
    def test_database_gate_contract(self):
        sql=Path("db/migrations/0037_auth_launch_gate.sql").read_text(encoding="utf-8")
        for token in [
            "auth_launch_gates",
            "custom_smtp_configured",
            "magic_link_e2e_pass",
            "jwt_ab_isolation_pass",
            "save_e2e_pass",
            "watch_e2e_pass",
            "alerts_isolation_pass",
            "session_logout_refresh_pass",
            "security_review_pass",
            "AUTH_LAUNCH_GATE_NOT_READY",
            "get_public_feature_flags_v01",
        ]:
            self.assertIn(token,sql)

    def test_build_requires_remote_gate_for_real_api(self):
        build=Path("web/build.py").read_text(encoding="utf-8")
        self.assertIn("AUTH_REQUESTED",build)
        self.assertIn("remote_auth_enabled",build)
        self.assertIn("AUTH_REQUESTED and (remote_auth_enabled if API else True)",build)

    def test_magic_link_has_client_cooldown(self):
        js=Path("web/static/account.js").read_text(encoding="utf-8")
        self.assertIn("AUTH_COOLDOWN_MS=60_000",js)
        self.assertIn("jianshi_auth_otp_cooldown_until",js)
        self.assertIn("authCooldownRemaining",js)
        self.assertIn("setAuthCooldown",js)
        self.assertIn("60 秒内请勿重复请求",js)

    def test_fixture_enabled_ui_still_testable(self):
        env=os.environ.copy()
        env["JIANSHI_AUTH_ENABLED"]="1"
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True,env=env)
        account=Path("web/dist/account/index.html").read_text(encoding="utf-8")
        self.assertIn("data-auth-email-form",account)
        env["JIANSHI_AUTH_ENABLED"]="0"
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True,env=env)

if __name__=="__main__":
    unittest.main()
