"""B1 minimum email/password account flows; keep production Auth completely closed."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load_builder():
    spec=importlib.util.spec_from_file_location("b1_password_builder",ROOT/"web"/"build.py")
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms=[]
        self.passwords=[]
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":
            self.forms.append(a)
        if tag=="input" and a.get("type")=="password":
            self.passwords.append(a)
        if "id" in a:self.ids.append(a["id"])


class PasswordAccountContract(unittest.TestCase):
    def test_closed_production_does_not_show_form_or_collect_email(self):
        b=load_builder();b.AUTH_ENABLED=False
        html=b.build_account_page()
        p=Inspect();p.feed(html)
        self.assertEqual(p.forms,[])
        self.assertEqual(p.passwords,[])
        self.assertIn("账户注册／登录尚未开放",html)
        self.assertIn("noindex,nofollow",html)
        self.assertIn('button type="button" disabled',html)
        self.assertNotIn('data-auth-register-form',html)
        self.assertNotIn('data-auth-login-form',html)
        self.assertNotIn('data-auth-reset-form',html)

    def test_enabled_fixture_exposes_register_login_and_recovery_forms(self):
        b=load_builder();b.AUTH_ENABLED=True
        html=b.build_account_page()
        p=Inspect();p.feed(html)
        self.assertEqual(len(p.ids),len(set(p.ids)))
        self.assertEqual(len(p.passwords),5)
        self.assertEqual(len(p.forms),6)
        for name in ("data-auth-register-form","data-auth-login-form",
                     "data-auth-reset-form","data-auth-change-form","data-auth-email-form"):
            self.assertIn(name,html)
        self.assertIn('data-auth-panel="login" hidden',html)
        self.assertIn('data-auth-panel="reset" hidden',html)
        self.assertIn('data-auth-switch="register" aria-pressed="true"',html)
        self.assertIn('data-auth-switch="login" aria-pressed="false"',html)
        self.assertIn("至少 8 位",html)
        self.assertIn("忘记密码？",html)
        self.assertIn("退出登录",html)
        self.assertIn('autocomplete="current-password"',html)
        self.assertIn('autocomplete="new-password"',html)
        self.assertIn("data-saved-list",html)
        self.assertIn("data-watch-list",html)
        self.assertIn("data-alert-list",html)
        self.assertIn("noindex,nofollow",html)

    def test_supabase_auth_sdk_used_for_real_password_apis_not_fake_ui(self):
        js=(ROOT/"web/static/account.js").read_text(encoding="utf-8")
        for token in ("supabase.auth.signUp(","supabase.auth.signInWithPassword(",
                      "supabase.auth.resetPasswordForEmail(","supabase.auth.updateUser(",
                      "supabase.auth.signOut(","emailRedirectTo:authRedirect()",
                      "autocomplete","passwordPair","showAuthPanel","onAuthStateChange"):
            if token!="autocomplete":self.assertIn(token,js)
        for banned in ("localStorage.setItem('password'","console.log(password",
                       "user_metadata.role","service_role"):
            self.assertNotIn(banned,js)
        css=(ROOT/"web/static/styles.css").read_text(encoding="utf-8")
        self.assertIn(".account-live-form[data-auth-panel][hidden]{display:none!important}",css)

    def test_original_auth_launch_gates_cannot_be_bypassed(self):
        b=load_builder()
        self.assertFalse(b.AUTH_ENABLED)
        source=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn('module.AUTH_ENABLED = False',source)
        self.assertIn('"account": "/"',source)
        gate=(ROOT/"db/migrations/0037_auth_launch_gate.sql").read_text(encoding="utf-8")
        for token in ("custom_smtp_configured","magic_link_e2e_pass","jwt_ab_isolation_pass",
                      "save_e2e_pass","watch_e2e_pass","alerts_isolation_pass",
                      "session_logout_refresh_pass","security_review_pass"):
            self.assertIn(token,gate)


if __name__=="__main__":
    unittest.main()
