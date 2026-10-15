#!/usr/bin/env python3
"""T07 real Chromium: exact 375px mobile and 1440px desktop, no horizontal overflow.

Generates screenshots inside t07-evidence/. No production data/API requests.
"""
from __future__ import annotations
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"web"/"dist"
EVIDENCE=ROOT/"t07-evidence"
EVIDENCE.mkdir(exist_ok=True)
PROJECTS=json.loads((ROOT/"data"/"projects.json").read_text(encoding="utf-8"))

handler=partial(SimpleHTTPRequestHandler,directory=str(OUT))
server=ThreadingHTTPServer(("127.0.0.1",0),handler)
thread=Thread(target=server.serve_forever,daemon=True)
thread.start()

try:
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
        for width in (375,1440):
            page=browser.new_page(viewport={"width":width,"height":900},device_scale_factor=1)
            for rel,label in (("projects/","list"),("projects/datafast/","datafast"),("projects/readlens/","readlens")):
                url=f"http://127.0.0.1:{server.server_port}/{rel}"
                page.goto(url,wait_until="networkidle")
                page.screenshot(path=str(EVIDENCE/f"{label}-{width}.png"),full_page=True)
                overflow=page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                if overflow:
                    raise AssertionError(f"Horizontal overflow {width}px: {rel}")
                if width==375:
                    actual=page.locator("h1").inner_text()
                    assert actual, f"Missing title: {rel}"
            if width==375:
                page.goto(f"http://127.0.0.1:{server.server_port}/projects/?category=SaaS&sort=mrr")
                page.reload()
                assert page.locator("#category").input_value()=="SaaS"
                assert page.locator("#sort").input_value()=="mrr"
                assert page.locator("article[data-project]:visible").count()==sum(p["category"]=="SaaS" for p in PROJECTS)
                page.locator("#verdict").select_option("可做")
                assert "verdict=%E5%8F%AF%E5%81%9A" in page.url
                page.reload()
                assert page.locator("#verdict").input_value()=="可做"
            page.close()
        browser.close()
    print("PASS T07 real browser: 375px / 1440px no overflow, 6 screenshots, query filters survive reload")
finally:
    server.shutdown()
