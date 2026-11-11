#!/usr/bin/env python3
"""T11b before/after 375px phone screenshots, local static only."""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/"t11b-before"/"web"/"dist"
NEW=ROOT/"web"/"dist"
OUT=ROOT/"t07-evidence"/"t11b-before-after"
OUT.mkdir(parents=True,exist_ok=True)

def serve(path):
    if not (path/"index.html").is_file():
        raise FileNotFoundError(f"Missing before/after static site: {path}")
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(path)))
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    return server

a,b=serve(OLD),serve(NEW)
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
        for name,route in (("projects","/projects/"),("datafast","/projects/datafast/"),("sprint","/sprint/")):
            for version,server in (("before",a),("after",b)):
                page=browser.new_page(viewport={"width":375,"height":812},device_scale_factor=1)
                page.goto(f"http://127.0.0.1:{server.server_port}{route}",wait_until="networkidle")
                assert page.locator("h1").count()==1
                if version=="after":
                    assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"),route
                page.screenshot(path=str(OUT/f"{name}-{version}-375.png"),full_page=True)
                page.close()
        browser.close()
    print("PASS T11b before/after 375px: projects, datafast, sprint; 6 PNG")
finally:
    a.shutdown()
    b.shutdown()
