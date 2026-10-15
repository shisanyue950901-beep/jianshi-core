"""B1 entry and signup-appearance checks; production account stays fail closed."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"release"))
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases
from p445_unified_home import build_home
from p412_build_public import assert_safe_source, publish_account_preview


def builder():
    spec=importlib.util.spec_from_file_location("b1_entry_account_builder",ROOT/"web"/"build.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class B1EntryAccountVisual(unittest.TestCase):
    def test_landing_editorial_brand_not_false_product_stats(self):
        page=build_home(eligible_cases(parse_cases()))
        assert_safe_source(page)
        for text in ("见势三步研究路径","发现方向","核查依据","决定下一步",
                     "j2-visual-panel","j2-journey","prefers-reduced-motion:reduce"):
            self.assertIn(text,page)
        self.assertEqual(page.count('<script>'),1)
        self.assertEqual(page.count('data:image/webp;base64,'),1)
        self.assertEqual(page.count('<article class="j2-project" data-t08-id="'),3)
        self.assertIn('class="j2-account-cta" href="/account/"',page)
        self.assertIn('href="/account/"',page)
        self.assertIn('aria-label="移动导航"',page)
        self.assertNotIn('type="email"',page)

    def test_account_closed_preview_is_noninteractive_and_noindex(self):
        b=builder()
        b.AUTH_ENABLED=False
        page=b.build_account_page()
        for text in ("账户功能正在完成最后的邮件登录配置",
                     'class="account-entry-shell"',"注册界面预览",
                     "邮箱注册／登录 · 即将开放","当前不收集注册邮箱",
                     'href="/discover/"','noindex,nofollow'):
            self.assertIn(text,page)
        self.assertNotIn("data-auth-email-form",page)
        self.assertNotIn('<form',page)
        self.assertNotIn('type="email"',page)
        self.assertNotIn("data-auth-logged-in",page)

    def test_ready_version_preserves_magic_link_and_existing_dashboard(self):
        b=builder()
        b.AUTH_ENABLED=True
        page=b.build_account_page()
        self.assertIn('data-auth-email-form',page)
        self.assertIn('name="email"',page)
        self.assertIn('autocomplete="email"',page)
        self.assertIn('type="email"',page)
        self.assertIn('aria-live="polite"',page)
        self.assertIn('data-auth-logged-out',page)
        self.assertIn('data-auth-logged-in hidden',page)
        for token in ('data-saved-list','data-watch-list','data-alert-list',
                      'data-auth-signout','data-clear-my-data',
                      "发送登录链接"):
            self.assertIn(token,page)
        self.assertIn('data-auth-register-form',page)
        self.assertIn('data-auth-login-form',page)
        self.assertIn('data-auth-reset-form',page)
        self.assertIn('data-auth-change-form',page)
        self.assertIn('name="password"',page)
        self.assertIn('autocomplete="new-password"',page)
        self.assertIn('autocomplete="current-password"',page)
        self.assertIn('data-auth-email-form',page)
        self.assertNotIn("action=\"http",page)

    def test_public_account_entry_is_reachable_without_activating_auth(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch("p412_build_public.OUTPUT",Path(temp)):
                publish_account_preview()
            account=(Path(temp)/"account/index.html").read_text(encoding="utf-8")
            doc=(Path(temp)/"account/preview/index.html").read_text(encoding="utf-8")
            self.assertIn('href="https://jianshi-bua.pages.dev/account/"',account)
            self.assertIn("账户注册／登录尚未开放",account)
            self.assertIn("noindex,nofollow",account)
            self.assertNotIn("<form",account)
            self.assertNotIn('type="email"',account)
            self.assertNotIn('http-equiv=',account)
            self.assertIn('class="account-entry-shell"',doc)
            self.assertIn('href="https://jianshi-bua.pages.dev/account/preview/"',doc)
            self.assertIn("noindex,nofollow",doc)
            self.assertIn('button type="button" disabled',doc)
            self.assertNotIn("data-auth-email-form",doc)
            self.assertNotIn("<form",doc)
        source=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertNotIn('"account": "/"',source)
        self.assertIn('account_dest = OUTPUT / "account" / "index.html"',source)
        self.assertIn("safe_redirect(target)",source)
        self.assertIn('href="/discover/"',doc)

    def test_account_styles_are_responsive_and_scoped(self):
        css=(ROOT/"web"/"static"/"styles.css").read_text(encoding="utf-8")
        for token in (".account-entry-shell",".account-story",".account-access",
                      ".account-input-example",".account-live-form",
                      "@media(max-width:840px)","@media(max-width:480px)",
                      "prefers-reduced-motion:reduce"):
            self.assertIn(token,css)
        self.assertIn(".account-form-preview button:disabled",css)


if __name__=="__main__":
    unittest.main()
