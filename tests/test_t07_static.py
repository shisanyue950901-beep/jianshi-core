#!/usr/bin/env python3
"""T07 mechanical content contract: generated HTML must agree with data/projects.json."""
from __future__ import annotations
import html
import json
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "release"))

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"projects.json"
TARGET=ROOT/"web"/"dist"/"projects"

def money(v,c="USD"):
    if v is None or v=="": return "未公开"
    n=float(v)
    out=f"{n:,.2f}" if n!=int(n) else f"{n:,.0f}"
    return ("$" if c=="USD" else c+" ")+out

def check():
    projects=json.loads(DATA.read_text(encoding="utf-8"))
    assert len(projects)==len({p["id"] for p in projects}), "Duplicate IDs"
    actual={p.name for p in TARGET.iterdir() if p.is_dir()}
    expected={p["id"] for p in projects}
    assert actual==expected, f"Project HTML directories mismatch missing={expected-actual} extra={actual-expected}"
    list_html=(TARGET/"index.html").read_text(encoding="utf-8")
    assert "收入信息来自海外收入公示网站 TrustMRR" in list_html
    assert "id=\"category\"" in list_html and "id=\"verdict\"" in list_html and "id=\"evidence_level\"" in list_html and "id=\"sort\"" in list_html
    assert "https://jianshi-bua.pages.dev/projects/" in list_html
    assert "nerdwallet" not in list_html.lower() and "plausible" not in list_html.lower()
    js=(TARGET/"t07.js").read_text(encoding="utf-8")
    assert "URLSearchParams" in js and "history.replaceState" in js and "location.search" in js
    assert "fetch(" not in js and "XMLHttpRequest" not in js
    assert (TARGET/"t07.css").is_file()
    for p in projects:
        rid=p["id"]
        page=(TARGET/rid/"index.html").read_text(encoding="utf-8")
        rev=p["revenue"]
        assert f'href="/projects/{rid}/"' in list_html, f"Card missing: {rid}"
        assert f'data-category="{html.escape(p["category"],quote=True)}"' in list_html
        assert f'data-evidence="{html.escape(p["evidence_level"],quote=True)}"' in list_html
        assert f'data-score="{p["total_score"]}"' in list_html
        for key in ("mrr","last_30d"):
            assert html.escape(money(rev[key],rev["currency"])) in list_html, f"{rid} listing {key}"
        for key in ("mrr","last_30d","all_time"):
            assert html.escape(money(rev[key],rev["currency"])) in page, f"{rid} detail {key}"
        for field in ("name","category","one_liner_cn","business_model","price_point","risks","cn_angle","verdict","risk_public"):
            assert html.escape(public_copy(p[field]),quote=True) in page, f"{rid} {field}"
        from t07_projects import chinese_date, source_display, public_copy
        assert html.escape(str(rev["verified_by"])) in page
        assert chinese_date(rev["as_of"]) in page and chinese_date(p["founded_date"]) in page
        assert (("未公开" if p["customers"] is None else str(p["customers"])) in page)
        for dim, score in p["scores"].items():
            assert f">{score}/5<" in page, f"{rid} {dim}"
            assert html.escape(public_copy(p["score_reasons"][dim]),quote=True) in page, f"{rid} missing score reason {dim}"
        assert html.escape(p["risk_public"],quote=True) in page
        assert html.escape(p["risk_public"],quote=True) in list_html
        for flag in p.get("flags") or []:
            assert html.escape(flag,quote=True) not in page, f"{rid} leaked internal flag"
            assert html.escape(flag,quote=True) not in list_html, f"{rid} leaked internal flag"
        for source in p.get("sources") or []:
            assert html.escape(source["url"],quote=True) in page
            assert html.escape(source_display(source),quote=True) in page
            assert chinese_date(source["checked_at"]) in page
        assert "数据为第三方公开信息，非财务审计，不构成收入承诺。" in page
        assert "见势未逐笔核对" in page
        assert "fetch(" not in page and "XMLHttpRequest" not in page
    # Hark T07 gate: inspect every generated HTML href, including homepage and discover.
    # Any old or newly introduced /projects/<id>/ link must resolve to one of
    # the review-approved JSON ids. 301 redirect rules are NOT a substitute.
    class ProjectHrefAudit(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
        def handle_starttag(self, tag, attrs):
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)

    checked_html = 0
    internal_detail_links = 0
    for page in (ROOT/"web"/"dist").rglob("*.html"):
        parser = ProjectHrefAudit()
        parser.feed(page.read_text(encoding="utf-8"))
        checked_html += 1
        for href in parser.links:
            parsed = urlsplit(href)
            path = unquote(parsed.path)
            if not path.startswith("/projects/") or path == "/projects/":
                continue
            parts = path.removeprefix("/projects/").strip("/").split("/")
            if len(parts) == 1 and path.endswith("/"):
                internal_detail_links += 1
                assert parts[0] in expected, f"Unregistered project href in {page.relative_to(ROOT)}: {href}"
    print(f"PASS T07 all-site link audit: {checked_html} HTML files, {internal_detail_links} detail hrefs, only JSON ids")
    print(f"PASS T07 HTML/JSON parity: {len(projects)} projects, {len(projects)+1} static pages, all public fields, links and risks, zero runtime fetch")

if __name__=="__main__":
    try:
        check()
    except Exception as exc:
        print("FAIL T07:",repr(exc),file=sys.stderr)
        raise
