#!/usr/bin/env python3
"""Full registered UX browser test with MOCK Supabase ESM. Never hits real Auth.

Generated enabled HTML is served only via a Playwright route. Production
web/dist/account/ stays a blocked redirect; no mail, user or session is created.
"""
from __future__ import annotations

import functools
import importlib.util
import json
import os
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "web" / "dist"
OUT = ROOT / "browser-smoke-evidence" / "auth-fixture"
SDK_URL = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.1/+esm"
VIEWPORTS = [390, 1440]

MOCK_SDK = r"""
const calls=[];
let current=null;
const session={user:{id:"isolated-ui-fixture",email:"demo@example.invalid"}};
window.__mockAuthCalls=calls;
function record(method){calls.push(method);}
export function createClient(url,key,options){
  if(!url||!key||!options)throw Error("Auth config missing");
  return {
    auth:{
      getSession:async()=>({data:{session:current},error:null}),
      onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),
      signUp:async()=>{record("signUp");return {data:{session:null,user:session.user},error:null};},
      resend:async()=>{record("resend");return {data:{},error:null};},
      signInWithPassword:async()=>{record("signInWithPassword");current=session;return {data:{session},error:null};},
      resetPasswordForEmail:async()=>{record("resetPasswordForEmail");return {data:{},error:null};},
      updateUser:async()=>{record("updateUser");return {data:{user:session.user},error:null};},
      signInWithOtp:async()=>{record("signInWithOtp");return {data:{},error:null};},
      signOut:async()=>{record("signOut");current=null;return {error:null};}
    },
    rpc:async(name)=>{record("rpc:"+name);return {data:[],error:null};}
  };
}
"""


def enabled_markup():
    spec = importlib.util.spec_from_file_location("isolated_signup_fixture", ROOT / "web/build.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.AUTH_ENABLED = True
    html = builder.build_account_page()
    assert 'data-auth-register-form' in html and "window.JIANSHI_AUTH_CONFIG" in html
    assert 'href="/privacy/"' in html and 'name="robots" content="noindex,nofollow"' in html
    return html


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def verify(page, base: str, width: int):
    page.goto(base + "/account/", wait_until="load")
    expect(page.locator('[data-auth-register-form]')).to_be_visible()
    expect(page.locator('[data-auth-login-form]')).to_be_hidden()
    assert page.locator('#register-password').get_attribute('type') == 'password'
    assert page.locator('#register-meter-bar').get_attribute('data-level') is None

    size = page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
    assert size['scroll'] <= size['width'] + 2, f"Horizontal overflow {size}"
    OUT.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUT / f"registration-{width}.png"), full_page=True, animations="disabled")

    # Live strength, show/hide, actual mismatch validation.
    page.locator('#register-password').fill('abc')
    expect(page.locator('#register-strength')).to_contain_text('密码太短')
    page.locator('#register-password').fill('DistinctLongExample2026!')
    expect(page.locator('#register-meter-bar')).to_have_attribute('data-level', '3')
    page.locator('[data-toggle-password="register-password"]').click()
    assert page.locator('#register-password').get_attribute('type') == 'text'
    page.locator('[data-toggle-password="register-password"]').click()
    assert page.locator('#register-password').get_attribute('type') == 'password'

    page.locator('#register-email').fill('demo@example.invalid')
    page.locator('#register-confirm').fill('MismatchExample2026!')
    page.locator('[name="privacy_consent"]').check()
    page.locator('[data-auth-register-form] button[type="submit"]').click()
    expect(page.locator('[data-auth-register-status]')).to_contain_text('两次输入的密码不一致')
    assert 'signUp' not in page.evaluate('window.__mockAuthCalls')

    page.locator('#register-confirm').fill('DistinctLongExample2026!')
    page.locator('[data-auth-register-form] button[type="submit"]').click()
    expect(page.locator('[data-auth-verification]')).to_be_visible()
    expect(page.locator('[data-auth-register-status]')).to_contain_text('检查收件箱')
    assert page.evaluate('window.__mockAuthCalls.filter(x=>x==="signUp").length') == 1
    assert page.locator('#register-password').input_value() == ''
    page.screenshot(path=str(OUT / f"confirmation-{width}.png"), full_page=True, animations="disabled")

    # The email cooldown is a UX throttle; the server owns abuse prevention.
    page.evaluate('localStorage.removeItem("jianshi_auth_otp_cooldown_until")')
    page.locator('[data-auth-resend]').click()
    expect(page.locator('[data-auth-resend-status]')).to_contain_text('已请求发送')
    assert 'resend' in page.evaluate('window.__mockAuthCalls')

    page.locator('[data-auth-switch="login"]').click()
    expect(page.locator('[data-auth-login-form]')).to_be_visible()
    expect(page.locator('[data-auth-register-form]')).to_be_hidden()
    page.screenshot(path=str(OUT / f"login-{width}.png"), full_page=True, animations="disabled")
    page.locator('[data-auth-forgot]').click()
    expect(page.locator('[data-auth-reset-form]')).to_be_visible()
    page.locator('#reset-email').fill('demo@example.invalid')
    page.evaluate('localStorage.removeItem("jianshi_auth_otp_cooldown_until")')
    page.locator('[data-auth-reset-form] button[type="submit"]').click()
    expect(page.locator('[data-auth-reset-status]')).to_contain_text('请检查密码重置邮件')
    assert 'resetPasswordForEmail' in page.evaluate('window.__mockAuthCalls')
    page.locator('[data-auth-back]').click()
    expect(page.locator('[data-auth-login-form]')).to_be_visible()

    page.locator('#login-email').fill('demo@example.invalid')
    page.locator('#login-password').fill('DistinctLongExample2026!')
    page.locator('[data-auth-login-form] button[type="submit"]').click()
    expect(page.locator('[data-auth-logged-in]')).to_be_visible()
    expect(page.locator('[data-auth-logged-out]')).to_be_hidden()
    expect(page.locator('[data-auth-user-email]')).to_have_text('demo@example.invalid')
    assert 'signInWithPassword' in page.evaluate('window.__mockAuthCalls')

    page.locator('#change-password').fill('DifferentPassword2026!')
    page.locator('#change-confirm').fill('DifferentPassword2026!')
    page.locator('[data-auth-change-form] button[type="submit"]').click()
    expect(page.locator('[data-auth-change-status]')).to_have_text('密码已更新。')
    assert 'updateUser' in page.evaluate('window.__mockAuthCalls')
    assert page.locator('#change-password').input_value() == ''
    page.locator('[data-auth-signout]').click()
    page.wait_for_url(base + "/")
    return {'viewport':width,'result':'PASS','mode':'Supabase Auth ESM mocked; no real email/API'}


def main():
    assert DIST.is_dir() and (DIST / 'account.js').is_file()
    html = enabled_markup()
    srv = ThreadingHTTPServer(('127.0.0.1',0),
            functools.partial(QuietHandler,directory=str(DIST)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base=f'http://127.0.0.1:{srv.server_port}'
    results=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            for width in VIEWPORTS:
                context=browser.new_context(viewport={'width':width,'height':844 if width==390 else 900},
                        device_scale_factor=1,is_mobile=(width==390),
                        reduced_motion='reduce')
                context.route('**/*',lambda route:route.continue_()
                        if route.request.url.startswith(base+'/') else route.abort())
                context.route('https://cdn.jsdelivr.net/**',lambda route:route.fulfill(
                    status=200,content_type='application/javascript',
                    headers={'access-control-allow-origin':'*','cache-control':'no-store'},
                    body=MOCK_SDK))
                context.route(base+'/account/',lambda route:route.fulfill(
                    status=200,content_type='text/html; charset=utf-8',body=html))
                page=context.new_page()
                errors=[]
                page.on('pageerror',lambda err: errors.append(str(err)))
                try:
                    row=verify(page,base,width)
                    assert not errors, errors
                    results.append(row)
                    print(f'AUTH_UI_MOCK_{width}: PASS',flush=True)
                except Exception as exc:
                    results.append({'viewport':width,'result':'FAIL','error':str(exc)[:500]})
                    page.screenshot(path=str(OUT / f'FAILED-{width}.png'),full_page=True)
                    print(f'AUTH_UI_MOCK_{width}: FAIL: {exc}',flush=True)
                context.close()
            browser.close()
    finally:
        srv.shutdown();srv.server_close()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'README_CN.md').write_text(
        '# 见势邮箱注册交互隔离验收\n\n'
        '真实 Chromium 测试表单切换、密码显示和强度、重复输入验证、隐私勾选、'
        '模拟邮件发送与重发、密码重置、登录、修改密码和退出。\n\n'
        '**Supabase Auth 全部采用本地模拟模块，未发送邮件、未创建真实用户，'
        '不构成生产 Auth 端到端验收。**\n\n'
        +json.dumps(results,ensure_ascii=False,indent=2)+'\n',
        encoding='utf-8')
    passed=sum(row['result']=='PASS' for row in results)
    print(f'AUTH_UI_MOCK_RESULT: {passed}/{len(results)} PASS; {len(results)-passed} FAIL',flush=True)
    raise SystemExit(0 if passed==len(results) else 1)


if __name__=='__main__':
    main()
