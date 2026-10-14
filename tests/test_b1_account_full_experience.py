"""B1: real registration UI contract, mocked authentication only in browser QA."""
from __future__ import annotations
import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def builder():
    spec=importlib.util.spec_from_file_location("full_account_ui",ROOT/"web/build.py")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.passwords=[]
        self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get("id"):self.ids.append(a["id"])
        if tag=="a":self.links.append(a.get("href"))
        if tag=="input" and a.get("type")=="password":self.passwords.append(a)


class AccountFullExperienceTests(unittest.TestCase):
    def test_enabled_page_has_complete_standard_account_path(self):
        b=builder();b.AUTH_ENABLED=True
        s=b.build_account_page()
        p=Elements();p.feed(s)
        self.assertEqual(len(p.ids),len(set(p.ids)))
        self.assertEqual(len(p.passwords),5)
        self.assertEqual(len(p.links),len([x for x in p.links]))
        for marker in (
            'data-auth-register-form','data-auth-login-form','data-auth-reset-form',
            'data-auth-change-form','data-auth-email-form','data-auth-resend',
            'data-auth-verification hidden','data-auth-privacy', # see below
            'data-auth-switch="register"','data-auth-switch="login"',
            'data-toggle-password="register-password"',
            'data-toggle-password="register-confirm"',
            'data-toggle-password="login-password"',
            'data-toggle-password="change-password"',
            'data-toggle-password="change-confirm"',
            'id="register-strength"','id="register-meter-bar"',
            'name="privacy_consent" required',
            'href="/privacy/"','rel="noopener noreferrer"',
            'data-auth-logged-in hidden','data-auth-signout'):
            if marker=='data-auth-privacy':
                self.assertIn('class="account-consent"',s)
            else:self.assertIn(marker,s)
        self.assertIn("创建我的见势账户",s)
        self.assertIn("重新发送验证邮件",s)
        self.assertIn("发送重置密码邮件",s)
        self.assertIn("邮箱和密码",s)
        self.assertNotIn('<script src="https://cdn',s)

    def test_disabled_preview_is_visible_but_cannot_capture_credentials(self):
        b=builder();b.AUTH_ENABLED=False
        s=b.build_account_page()
        self.assertIn("账户注册／登录尚未开放",s)
        self.assertIn("注册界面预览",s)
        self.assertIn("设置密码",s)
        self.assertIn("确认密码",s)
        self.assertIn('button type="button" disabled',s)
        self.assertNotIn("<form",s)
        self.assertNotIn('type="password"',s)
        self.assertNotIn('type="email"',s)
        self.assertNotIn("data-auth-register-form",s)
        self.assertNotIn("data-auth-logged-in",s)

    def test_robust_dom_and_real_supabase_method_paths(self):
        s=(ROOT/"web/static/account.js").read_text(encoding="utf-8")
        for marker in (
            'document.querySelectorAll("[data-auth-panel]")',
            'document.querySelectorAll("[data-auth-switch]")',
            'document.querySelectorAll("[data-toggle-password]")',
            'form.querySelectorAll(',
            'passwordPair(registerForm)',
            'privacy_consent',
            'supabase.auth.signUp({',
            'supabase.auth.resend({',
            'supabase.auth.signInWithPassword({',
            'supabase.auth.resetPasswordForEmail(',
            'supabase.auth.updateUser({password:',
            'supabase.auth.signOut()',
            'clearSensitiveInputs(loginForm)',
            'PASSWORD_RECOVERY'):
            self.assertIn(marker,s)
        self.assertNotIn('const authPanels=$("[data-auth-panel]")',s)
        self.assertNotIn('const authSwitches=$("[data-auth-switch]")',s)
        self.assertNotIn('$("[data-toggle-password]").forEach',s)
        self.assertNotIn('console.log(password',s)
        self.assertNotIn("service_role",s)

    def test_css_is_adaptive_and_hidden_forms_cannot_overlay_each_other(self):
        s=(ROOT/"web/static/styles.css").read_text(encoding="utf-8")
        for marker in (
            ".account-password-row", ".account-password-toggle",
            ".account-password-meter", ".account-strength-text",
            ".account-consent", ".account-verification",
            ".account-auth-tabs", ".account-preview-tabs",
            ".account-security-points",
            ".account-entry-shell[hidden]",
            "@media(max-width:480px)", "prefers-reduced-motion:reduce",
            '.account-live-form[data-auth-panel][hidden]{display:none!important}'
        ):
            self.assertIn(marker,s)

    def test_live_auth_stays_doubly_gated_in_real_public_release(self):
        b=builder()
        self.assertFalse(b.AUTH_ENABLED)
        s=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn("module.AUTH_ENABLED = False",s)
        self.assertIn('"account": "/"',s)
        self.assertIn('data-auth-email-form',s)
        db=(ROOT/"db/migrations/0037_auth_launch_gate.sql").read_text(encoding="utf-8")
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY",db)


if __name__=="__main__":
    unittest.main()
