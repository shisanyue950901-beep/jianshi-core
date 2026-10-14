#!/usr/bin/env python3
"""Real Chromium smoke/viewport audit of GENERATED public static JianShi pages.

Runs against a loopback HTTP server serving web/dist. No prod, logins, network
collectors, data submissions, Supabase or other external traffic. No fake
"real people tested" conclusions; browser automation is not human validation.
"""
from __future__ import annotations

import functools
import json
import os
from pathlib import Path
import sys
import threading
import traceback
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

try:
    from playwright.sync_api import sync_playwright
except ImportError as exc:
    raise SystemExit("Install playwright and Chromium before running this audit") from exc

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "web" / "dist"
OUT = ROOT / "browser-smoke-evidence"
VIEWPORTS = (390, 1440)
ROUTES = {
    "/": "home",
    "/start/": "founder-research-start",
    "/projects/": "company-directory",
    "/discover/": "discover",
    "/projects/carrd/": "carrd-detail",
    "/solutions/": "solutions",
    "/solutions/automation/": "automation-solution",
    "/marketplace/": "marketplace",
    "/talent/": "talent",
    "/academy/": "academy",
    "/marketplace/brief/": "demand-draft",
    "/talent/portfolio/": "portfolio-draft",
    "/account/": "registration-entry",
    "/account/preview/": "registration-preview",
}
results: list[dict] = []


class SilentStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, _fmt, *_args):
        return


def check(label: str, operation, *, viewport: int, page=None):
    try:
        operation()
        results.append({"viewport": viewport, "check": label, "status": "PASS"})
        print(f"PASS {viewport}px | {label}", flush=True)
    except Exception as exc:
        detail = str(exc).splitlines()[0][:450]
        results.append({"viewport": viewport, "check": label,
                        "status": "FAIL", "error": detail})
        print(f"FAIL {viewport}px | {label}: {detail}", flush=True)
        if page is not None:
            try:
                page.screenshot(path=str(OUT / f"{viewport}-{label}-failure.png"),
                                full_page=True, animations="disabled", timeout=8000)
            except Exception:
                pass
        traceback.print_exception(exc, limit=3)


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def snapshot(page, base: str, route: str, slug: str, width: int):
    response = page.goto(base + route, wait_until="load", timeout=25000)
    require(response is not None and response.status == 200,
            f"{route} unexpected HTTP status {response.status if response else None}")
    require(page.locator("main").count() == 1, f"{route} has no single main")
    heading = page.locator("h1").first
    require(heading.is_visible(), f"{route} primary heading hidden")
    size = page.evaluate("""() => ({
        viewport: window.innerWidth,
        htmlWidth: document.documentElement.scrollWidth,
        bodyWidth: document.body.scrollWidth
    })""")
    require(size["viewport"] == width, f"{route} viewport mismatch {size}")
    require(size["htmlWidth"] <= width + 2 and size["bodyWidth"] <= width + 2,
            f"{route} HORIZONTAL OVERFLOW: {size}")
    screenshot = OUT / str(width) / f"{slug}.png"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot), full_page=True,
                    animations="disabled", timeout=25000)
    require(screenshot.stat().st_size > 1500, "Empty screenshot file")


def ui_secondary_mobile_menu(page, base: str, width: int):
    # Explicit computed CSS checks: a browser can otherwise produce a giant
    # white box around <details class="mobile"> while all links still work.
    routes = ("/solutions/", "/discover/", "/marketplace/brief/", "/talent/portfolio/")
    for route in routes:
        page.goto(base + route, wait_until="load")
        menu = page.locator(".top .mobile")
        summary = menu.locator("summary")
        popup = menu.locator("nav")
        if width > 1050:
            require(not menu.is_visible(), f"{route}: mobile control shown on desktop")
            require(page.locator(".top .desktop").is_visible(), f"{route}: desktop nav hidden")
            continue
        require(menu.is_visible(), f"{route}: mobile control hidden")
        require(not popup.is_visible(), f"{route}: closed dropdown is visible")
        appearance = menu.evaluate("""el => {
          const container = getComputedStyle(el);
          const button = getComputedStyle(el.querySelector('summary'));
          return { background: container.backgroundColor, padding: container.paddingTop,
                   margin: container.marginTop, border: container.borderTopWidth,
                   buttonBackground: button.backgroundColor, buttonColor: button.color,
                   buttonHeight: el.querySelector('summary').getBoundingClientRect().height,
                   menuWidth: el.getBoundingClientRect().width };
        }""")
        require(appearance["background"] in ("rgba(0, 0, 0, 0)", "transparent"),
                f"{route}: WHITE MENU BOX detected: {appearance}")
        require(appearance["padding"] == "0px" and appearance["margin"] == "0px",
                f"{route}: mobile nav inherited article panel padding: {appearance}")
        require(appearance["border"] == "0px", f"{route}: mobile nav inherited border")
        require(appearance["buttonBackground"] != "rgb(255, 255, 255)",
                f"{route}: menu trigger became white")
        require(appearance["buttonHeight"] <= 50 and appearance["menuWidth"] <= 105,
                f"{route}: mobile trigger is oversized: {appearance}")
        summary.click()
        require(menu.get_attribute("open") is not None,
                f"{route}: menu cannot open")
        require(popup.is_visible(), f"{route}: opened dropdown missing")
        popupBackground = popup.evaluate("el => getComputedStyle(el).backgroundColor")
        require(popupBackground not in ("rgb(255, 255, 255)", "rgba(0, 0, 0, 0)"),
                f"{route}: opened dropdown lacks dark surface: {popupBackground}")
        image_name = route.strip("/").replace("/", "-") + "-menu-open"
        page.screenshot(path=str(OUT / str(width) / f"{image_name}.png"),
                        full_page=False, animations="disabled", timeout=8000)
        summary.click()
        require(not popup.is_visible(), f"{route}: menu can't close")


def ui_founder_start(page, base: str):
    page.goto(base + "/start/",wait_until="load")
    require(page.locator("#service-skill").is_visible(), "Service question missing")
    require(page.locator("select[id^='service-']").count()==3,
            "Three-choice research flow changed")
    require(page.locator("#service-empty").is_visible(), "Empty research state missing")
    require(page.locator("#service-copy").is_disabled(), "Copy should be disabled before card")
    page.locator("#service-generate").click()
    require("请先选择三个问题的答案" in page.locator("#service-message").inner_text(),
            "Unanswered questions must be handled")
    page.locator("#service-demo").click()
    choices=page.locator(".service-pick")
    require(choices.count()==2, "Demonstration must produce exactly two research directions")
    first=choices.nth(0)
    require("靠专业服务接项目" in first.inner_text(),
            "Demonstration does not use reviewed agency model")
    require(choices.nth(1).get_by_text("卖模板、资料和数字工具").is_visible(),
            "Second demonstration direction missing")
    require(page.locator("#service-plan li").count()==4, "7-day plan should have 4 tasks")
    require(page.locator("#service-copy").is_enabled(), "Copy must enable after generation")
    require(page.locator(".service-picks a[href^='/research/']").count()==2,
            "Recommended direction links must lead to public model records")
    page.locator("#service-skill").select_option("writing")
    page.locator("#service-preference").select_option("content")
    page.locator("#service-resource").select_option("low")
    page.locator("#service-generate").click()
    require("做内容，再通过推荐赚钱" in choices.nth(0).inner_text(),
            "Different preferences must change the first direction")
    require("写书并在线销售" in choices.nth(1).inner_text(),
            "Different preferences must change the second direction")
    page.locator("#service-reset").click()
    require(page.locator("#service-empty").is_visible(), "Reset must restore empty guidance")
    require(page.locator("#service-result").is_hidden(), "Reset left sensitive result visible")
    require(page.locator("#service-copy").is_disabled(), "Reset left copy enabled")
    require(page.locator("#service-skill").input_value()=="", "Reset did not clear choices")


def ui_home(page, base: str, mobile: bool):
    page.goto(base + "/", wait_until="load")
    if mobile:
        menu = page.locator(".j2-mobile summary")
        require(menu.is_visible(), "Mobile menu is inaccessible")
        menu.click()
        require(page.locator(".j2-mobile[open]").count() == 1, "Mobile menu won't open")
        require(page.locator(".j2-mobile-list a[href='#j2-opportunities']").is_visible(),
                "Mobile menu project entry hidden")
        # The dropdown intentionally covers the area beneath it. A user must
        # dismiss it before touching the covered hero CTA, not click through.
        page.mouse.click(12, 180)
        require(page.locator(".j2-mobile[open]").count() == 0,
                "Mobile menu did not close on outside pointer tap")
        menu.click()
        page.keyboard.press("Escape")
        require(page.locator(".j2-mobile[open]").count() == 0,
                "Mobile menu did not close with Escape")
    else:
        require(page.locator(".j2-nav").is_visible(), "Desktop navigation hidden")
    entry=page.locator(".j2-top .j2-account-cta[href='/account/']")
    require(entry.count()==1 and entry.is_visible(),
            "Visible registration link missing from website header")
    entry.click()
    require(page.url.endswith("/account/"), "Header registration link does not open /account/")
    require(page.locator(".account-entry-shell").count()==1,
            "Registration entry does not render the account page")
    page.goto(base + "/", wait_until="load")
    page.locator(".j2-actions a[href='/discover/']").click()
    require(page.url.endswith("/discover/"), "Home to discover navigation failed")


def ui_company(page, base: str):
    page.goto(base + "/projects/", wait_until="load")
    require(page.locator(".case-directory-hero").is_visible(),
            "Branded company index header missing")
    require(page.locator(".case-directory-proof span").count() == 2,
            "Visible case/evidence boundaries absent")
    require(page.locator("a[href='/projects/carrd/']").count() >= 1, "Carrd link missing")
    page.locator("a[href='/projects/carrd/']").first.click()
    require(page.url.endswith("/projects/carrd/"), "Company card navigation failed")
    require(page.locator(".case-detail-hero").is_visible(),
            "Consistent project evidence header missing")
    fold = page.locator("#case-details summary")
    require(fold.count() == 1, "Detailed company evidence fold missing")
    fold.click()
    require(page.locator("#case-details[open]").count() == 1,
            "Company evidence does not expand")


def ui_discover(page, base: str):
    page.goto(base + "/discover/", wait_until="load")
    require(page.locator(".discover-steps span").count() == 5,
            "Branded research process steps missing")
    cards = page.locator("[data-discover-card]:visible")
    require(cards.count() == 9, f"Expected 9 default research cards, got {cards.count()}")
    reset = page.locator("#discover-reset")
    require(not reset.is_visible(), "Reset should not clutter the default view")
    page.locator("[data-discover-category='projects']").click()
    require(cards.count() == 3, "Company category must contain 3 verified cases")
    require(reset.is_visible(), "Reset missing after category change")
    page.locator("[data-discover-category='research']").click()
    require(cards.count() == 6, "Research category must contain 6 models")
    page.locator("#discover-query").fill("必然不存在的查找词-sanity-8241")
    require(cards.count() == 0, "Zero-match search should hide all cards")
    require(page.locator("#discover-empty").is_visible(), "No-result helper missing")
    reset.click()
    require(cards.count() == 9, "Reset must restore default 9 research cards")
    require(not reset.is_visible(), "Reset should hide again")
    fold = page.locator("details.discover-notice")
    fold.locator("summary").click()
    require(fold.get_attribute("open") is not None, "Disclosure didn't open")
    related = page.locator(".g2c-related-compact details")
    related.locator("summary").click()
    require(related.get_attribute("open") is not None, "Secondary links didn't open")


def ui_solutions(page, base: str):
    page.goto(base + "/solutions/", wait_until="load")
    require(page.locator(".solution-journey span").count() == 5,
            "Solution process overview lost")
    require(page.locator(".solution-icon").count() == 4,
            "Four styled solution directions missing")
    cards = page.locator("[data-f21-solution]:visible")
    require(cards.count() == 4, f"Expected four AI directions; got {cards.count()}")
    reset = page.locator("#f21-reset")
    require(not reset.is_visible(), "Default reset unexpectedly visible")
    page.locator("#f21-category").select_option("creative")
    require(cards.count() == 2, "Creative category should show 2 directions")
    require(reset.is_visible(), "Filter reset not visible")
    page.locator("#f21-category").select_option("all")
    page.locator("#f21-search").fill("自动化")
    require(cards.count() == 1, "Search automation should show 1 direction")
    page.locator("#f21-search").fill("必然不存在的查找词-sanity-8241")
    require(cards.count() == 0, "Zero-match solutions must be empty")
    require(page.locator("#f21-empty").is_visible(), "Solutions no-result helper missing")
    reset.click()
    require(cards.count() == 4 and not reset.is_visible(), "Solutions reset failed")


def ui_solution_detail(page, base: str):
    page.goto(base + "/solutions/automation/", wait_until="load")
    require(page.locator(".solution-journey span").count() == 5,
            "Detailed solution visual process missing")
    require(page.locator(".solution-detail-guide").count() == 1,
            "Detailed content branding lost")
    require(page.locator("#delivery").count() == 1,
            "Evidence-grounded delivery checklist missing")
    fold = page.locator(".solution-technical")
    require(not fold.get_attribute("open"), "Technical guidance should be folded by default")
    fold.locator("summary").click()
    require(fold.get_attribute("open") is not None,
            "Solution implementation steps did not expand")
    require(page.locator('a[href="/marketplace/brief/"]').count() >= 1,
            "Local-only preparation draft link is missing")


def ui_guides(page, base: str, route: str, tool: str):
    page.goto(base + route, wait_until="load")
    require(page.locator(f"a[href='{tool}']").count() >= 1,
            f"{route} local tool missing")
    fold = page.locator("details.guide-more")
    fold.locator("summary").click()
    require(fold.get_attribute("open") is not None, f"{route} checklist won't open")
    first = fold.locator('input[type="checkbox"]').first
    first.check()
    require(first.is_checked(), f"{route} checklist can't be checked")
    require("1 / 6" in fold.inner_text(), f"{route} tally did not update")
    fold.locator("[data-g2b-reset]").click()
    require(not first.is_checked(), f"{route} checklist can't reset")
    page.locator(f"a[href='{tool}']").first.click()
    require(page.url.endswith(tool), f"{route} local draft link failed")


def ui_academy(page, base: str):
    page.goto(base + "/academy/", wait_until="load")
    selector = page.locator("#g2b-academy-choice")
    require(selector.is_visible(), "Academy learning selector missing")
    selector.select_option("agent")
    agent = page.locator("[data-g2b-plan='agent']")
    require(agent.is_visible(), "Agent plan not visible when selected")
    require(page.locator("[data-g2b-plan='visual']").is_hidden(),
            "Unselected course plan should be hidden")
    first = agent.locator('input[type="checkbox"]').first
    first.check()
    require(first.is_checked(), "Academy checklist interaction failed")
    require("1 / 3" in agent.inner_text(), "Academy progress count did not update")


def ui_account_preview(page, base: str):
    page.goto(base + "/account/", wait_until="load")
    require(page.locator(".account-entry-shell").count() == 1,
            "Registration visual shell missing")
    require(page.get_by_text("邮箱注册／登录 · 即将开放").is_visible(),
            "Closed registration entry unavailable")
    require(page.locator(".account-form-preview button").is_disabled(),
            "Closed registration must not have an active submit button")
    require(page.locator("form").count() == 0,
            "Fail-closed account route rendered a live form")
    require(page.locator('input[type="email"]').count() == 0,
            "Account must not collect email before SMTP/auth gates")
    page.locator(".account-back-link").click()
    require(page.url.endswith("/discover/"), "Account browse-without-login link failed")


def ui_draft(page, base: str, kind: str):
    route = "/marketplace/brief/" if kind == "marketplace" else "/talent/portfolio/"
    page.goto(base + route, wait_until="load")
    fields = (
        ("#draft-project", "示例：电商新品视觉"),
        ("#draft-scene", "活动期间主图制作低效"),
        ("#draft-goal", "制作两张示例主图"),
    ) if kind == "marketplace" else (
        ("#draft-skill", "AI 商品视觉"),
        ("#draft-sample", "自制练习图片"),
        ("#draft-contribution", "本人完成素材选择和排版"),
    )
    for selector, value in fields:
        page.locator(selector).fill(value)
    progress = page.locator("#draft-progress")
    bar = page.locator("#draft-progress-bar")
    require("3 / 7" in progress.inner_text(),
            f"{kind} 3/7 fields did not update immediately")
    require(bar.evaluate("(el) => el.style.width") == "43%",
            f"{kind} bar should be 43% at 3/7, got {bar.get_attribute('style')}")
    page.locator("#draft-generate").click()
    require(page.locator("#draft-preview").inner_text().strip(),
            f"{kind} draft generation yielded no preview")
    require(page.locator("#draft-copy").is_enabled(),
            f"{kind} draft copy not available after generation")
    page.locator("#draft-clear").click()
    require(all(page.locator(selector).input_value() == "" for selector, _ in fields),
            f"{kind} draft clear did not erase input")
    require("0 / 7" in progress.inner_text(), f"{kind} completion did not reset")
    require(bar.evaluate("(el) => el.style.width") == "0%",
            f"{kind} bar did not reset")


def main():
    if not (DIST / "index.html").is_file() or not (DIST / "discover/index.html").is_file():
        raise SystemExit("Public web/dist not built (first run web/build.py + p412_build_public.py)")
    OUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(SilentStaticHandler, directory=str(DIST))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    try:
        with sync_playwright() as pw:
            launch_args = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
            if executable:
                launch_args["executable_path"] = executable
            browser = pw.chromium.launch(**launch_args)
            for width in VIEWPORTS:
                context = browser.new_context(
                    viewport={"width": width, "height": 844 if width == 390 else 900},
                    device_scale_factor=1, is_mobile=(width == 390),
                    has_touch=(width == 390), reduced_motion="reduce"
                )
                # This is not a collector, nor a test of public auth.
                # Abort every request beyond the local static snapshot.
                context.route("**/*", lambda route: route.continue_()
                              if route.request.url.startswith(base + "/")
                              else route.abort())
                page = context.new_page()
                js_errors = []
                page.on("pageerror", lambda err: js_errors.append(str(err)))
                for route, slug in ROUTES.items():
                    check("snapshot-" + slug,
                          lambda route=route, slug=slug: snapshot(page, base, route, slug, width),
                          viewport=width, page=page)
                check("subpage-mobile-menu-surface-and-toggle",
                      lambda: ui_secondary_mobile_menu(page, base, width),
                      viewport=width, page=page)
                check("founder-3-questions-to-research-plan",
                      lambda: ui_founder_start(page, base),
                      viewport=width, page=page)
                check("home-menu-and-navigation", lambda: ui_home(page, base, width == 390),
                      viewport=width, page=page)
                check("company-to-evidence", lambda: ui_company(page, base),
                      viewport=width, page=page)
                check("discover-search-and-folds", lambda: ui_discover(page, base),
                      viewport=width, page=page)
                check("solutions-filter", lambda: ui_solutions(page, base),
                      viewport=width, page=page)
                check("solution-detail-evidence-and-technical-fold",
                      lambda: ui_solution_detail(page, base),
                      viewport=width, page=page)
                check("marketplace-checklist-to-local-draft",
                      lambda: ui_guides(page, base, "/marketplace/", "/marketplace/brief/"),
                      viewport=width, page=page)
                check("talent-checklist-to-local-draft",
                      lambda: ui_guides(page, base, "/talent/", "/talent/portfolio/"),
                      viewport=width, page=page)
                check("academy-local-practice", lambda: ui_academy(page, base),
                      viewport=width, page=page)
                check("demand-draft-edit-generate-clear",
                      lambda: ui_draft(page, base, "marketplace"),
                      viewport=width, page=page)
                check("portfolio-draft-edit-generate-clear",
                      lambda: ui_draft(page, base, "talent"),
                      viewport=width, page=page)
                check("registration-entry-visible-auth-gated",
                      lambda: ui_account_preview(page, base),
                      viewport=width, page=page)
                check("script-runtime-errors",
                      lambda: require(not js_errors, " | ".join(js_errors[:4])),
                      viewport=width, page=page)
                context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    passed = sum(x["status"] == "PASS" for x in results)
    failed = sum(x["status"] == "FAIL" for x in results)
    summary = {
        "target": "generated audited public web/dist snapshot only",
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "chromium": "real browser; Playwright; local HTTP loopback",
        "viewport_widths": list(VIEWPORTS), "checks": len(results),
        "passed": passed, "failed": failed, "details": results,
        "not_tested": [
            "Production Cloudflare CDN interaction (this script serves local generated HTML)",
            "Real 390px/1440px physical devices",
            "Screen-reader assistive-technology inspection",
            "Real human entrepreneur comprehension or task completion",
            "Production account/payment/CMS/login"
        ],
    }
    (OUT / "browser-smoke.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# 见势｜真实 Chromium 浏览器检查",
        "",
        f"结果：**{passed}/{len(results)} PASS**，失败 **{failed}**",
        "",
        "对象：由仓库源码重建的 web/dist，通过 127.0.0.1 HTTP 加载；非线上 CDN 浏览器。",
        "分别采用 390px 模拟手机视口和 1440px 桌面视口，含真实 Chromium 截图、点击、输入、筛选、展开、练习勾选及本地草稿生成。",
        "",
        "| 宽度 | 检查 | 结果 |",
        "|---|---|---|",
    ]
    for item in results:
        lines.append(f"| {item['viewport']}px | {item['check']} | {item['status']} |")
    lines += [
        "", "## 未测试（不可冒充已通过）", "",
        "- 生产 CDN 的实际点击与渲染（此次离线重建模拟真实浏览器）。",
        "- 真实手机硬件、屏幕阅读器与至少五名真实创业者任务完成情况。",
        "- 任何账户、付费、生产数据写入或供需匹配。", "",
        "截图位于同一个 GitHub Actions Artifact 的 390/ 和 1440/ 文件夹。",
    ]
    (OUT / "README_CN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"BROWSER_SMOKE_RESULT: {passed}/{len(results)} PASS; {failed} FAIL", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
