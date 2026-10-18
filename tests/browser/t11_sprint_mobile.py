#!/usr/bin/env python3
"""T11 static 375px mobile screenshot and checklist persistence QA."""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
DIST=ROOT/"web"/"dist"
OUT=ROOT/"t07-evidence"
OUT.mkdir(exist_ok=True)
handler=partial(SimpleHTTPRequestHandler,directory=str(DIST))
server=ThreadingHTTPServer(("127.0.0.1",0),handler)
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
        ctx=browser.new_context(viewport={"width":375,"height":812},device_scale_factor=1)
        page=ctx.new_page()
        url=f"http://127.0.0.1:{server.server_port}/sprint/"
        page.goto(url,wait_until="networkidle")
        assert page.locator("h1").count()==1
        assert page.locator("button[disabled]").inner_text()=="表单即将开放"
        assert page.locator("[data-t11-diagnose]").count()==0
        assert not page.evaluate("document.documentElement.scrollWidth>window.innerWidth")
        boxes=page.locator("[data-t11-check]")
        assert boxes.count()>=12
        boxes.first.check()
        assert page.locator("[data-t11-progress]").inner_text().startswith("已完成 1 / ")
        page.reload(wait_until="networkidle")
        assert boxes.first.is_checked(), "localStorage did not persist on reload"
        boxes.first.uncheck()
        page.screenshot(path=str(OUT/"t11-sprint-mobile-375.png"),full_page=True)
        ctx.close()
        browser.close()
    print("PASS T11 mobile: 375px, no overflow, disabled CTA, localStorage reload, screenshot")
finally:
    server.shutdown()
