#!/usr/bin/env python3
"""P4.29 public editorial source atlas; NO marketplace listing scraping.

Acquire.com and Flippa listings remain blocked without verified written rights.
Curated report/official interview links are context only, not enrolled projects.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "config/p429_market_source_registry.json"
OUT = ROOT / "web/dist/sources/index.html"
SITE = "https://jianshi-bua.pages.dev"
EXPECTED = {"acquire","flippa","microns","indiehackers","hackernews","sec"}
REPORT_TYPES = {"ANONYMIZED_AGGREGATE_REPORT","ATTRIBUTABLE_FOUNDER_EDITORIAL_CASE","AGGREGATE_MARKET_RESEARCH"}
REVIEW_STATUSES = {"WRITTEN_PERMISSION_REQUIRED","TERMS_AND_AUTHORIZATION_PENDING",
                   "NOT_APPLICABLE","PUBLIC_SEARCH_API","PUBLIC_REGULATORY_DOCUMENTS"}
BLOCKED_MARKETPLACES = {"acquire","flippa","microns"}

def safe(url: str, *, host: str | None = None) -> str:
    if not isinstance(url, str) or len(url) > 1200:
        raise RuntimeError("Invalid source URL")
    p = urlsplit(url)
    if (p.scheme != "https" or not p.hostname or p.username or p.password or
            any(ord(c) < 32 for c in url)):
        raise RuntimeError("Only plain HTTPS source URLs are allowed")
    if host and p.hostname not in (host, "www."+host, "blog."+host):
        raise RuntimeError("Source does not belong to declared publisher")
    return url

def load_registry() -> dict:
    d=json.loads(INPUT.read_text(encoding="utf-8"))
    if d.get("version") != "P429_SOURCE_RIGHTS_V1":
        raise RuntimeError("Source registry has not passed editorial gate")
    providers=d.get("providers")
    if not isinstance(providers,list) or {r.get("id") for r in providers}!=EXPECTED or len(providers)!=len(EXPECTED):
        raise RuntimeError("Expected six strictly reviewed source providers")
    by_id={p["id"]:p for p in providers}
    for p in providers:
        safe(p["url"])
        safe(p["legal_source"])
        if p.get("listing_access") not in REVIEW_STATUSES:
            raise RuntimeError("Unknown source license status")
        if p["id"] in BLOCKED_MARKETPLACES:
            if p.get("automatic_listing_collection") is not False or p.get("automatic_listing_republication") is not False:
                raise RuntimeError("Scraping or republication of marketplace listings is prohibited")
            if p["listing_access"] not in {"WRITTEN_PERMISSION_REQUIRED","TERMS_AND_AUTHORIZATION_PENDING"}:
                raise RuntimeError("No verified marketplace data permission")
    reports=d.get("editorial_reports")
    if not isinstance(reports,list) or len(reports)!=4 or len({r["id"] for r in reports})!=4:
        raise RuntimeError("Expected four reviewed editorial references")
    for r in reports:
        if r.get("provider") not in {"acquire","flippa"} or r.get("type") not in REPORT_TYPES:
            raise RuntimeError("Source attribution cannot be confirmed")
        if r.get("publish_as_project") is not False:
            raise RuntimeError("Industry market reports must never auto-admit a project")
        for field in ("title","summary","takeaway","date"):
            if not isinstance(r.get(field),str) or len(r[field])<8:
                raise RuntimeError("Unverified editorial research metadata")
        from datetime import date
        date.fromisoformat(r["date"])
        safe(r["url"],host="acquire.com" if r["provider"]=="acquire" else "flippa.com")
        if "/public/" in urlsplit(r["url"]).path or "/buy/" in urlsplit(r["url"]).path:
            raise RuntimeError("Listing data must not be exported via research atlas")
    return d

def authorized_listing_access(provider_id: str, written_approval_reference: str | None = None) -> bool:
    """Authorization-gated compatibility point for a future approved API/export.

    Still blocked in P4.29 even if caller passes an arbitrary string:
    there is no approved license record in the registry.
    """
    providers={x["id"]:x for x in load_registry()["providers"]}
    if provider_id not in BLOCKED_MARKETPLACES or provider_id not in providers:
        return False
    p=providers[provider_id]
    return bool(p.get("license_granted") is True
                and isinstance(p.get("license_reference"),str)
                and p["license_reference"].strip()
                and written_approval_reference == p["license_reference"]
                and p.get("allowed_fields")
                and p.get("automatic_listing_collection") is True)

def esc(value: object) -> str:
    return html.escape(str(value),quote=True)

CSS="""
:root{color-scheme:light;--bg:#f7f6f1;--panel:#fffefa;--ink:#202823;--muted:#59615a;--line:#c8c9c3;--accent:#286b56}
html[data-theme=dark]{color-scheme:dark;--bg:#080a09;--panel:#151814;--ink:#f4f2ef;--muted:#adb0ab;--line:#51534f;--accent:#86b4a3}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
a{color:var(--accent);text-underline-offset:4px}button{cursor:pointer;color:var(--ink);background:var(--panel);border:1px solid var(--line);padding:8px 12px}
a:focus-visible,button:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
header,main,footer{max-width:1070px;padding-inline:clamp(18px,4vw,48px);margin:auto}
header{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding-block:23px;border-bottom:1px solid var(--line)}
header>a{font:500 27px Georgia,"Songti SC",serif;color:var(--ink);text-decoration:none}
nav{display:flex;gap:15px;align-items:center;flex-wrap:wrap;font-size:13px}
main{padding-block:62px 90px}.kicker{font-size:12px;letter-spacing:.16em;color:var(--accent);font-weight:700}
h1{font:500 clamp(37px,5vw,66px)/1.22 Georgia,"Songti SC",serif;margin:13px 0 22px}
h2{font:500 clamp(25px,3.2vw,37px)/1.3 Georgia,"Songti SC",serif;margin:0}
h3{font-size:19px;font-weight:600;margin:0 0 10px}
.lead{max-width:810px;font-size:17px;color:var(--muted);line-height:1.9}
.note{border-left:3px solid var(--accent);padding:19px 23px;background:var(--panel);font-size:14px;margin:27px 0}
.section-head{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:baseline;border-top:1px solid var(--line);margin:62px 0 23px;padding-top:20px}
.section-head span{font-size:13px;color:var(--muted)}
.items{display:grid;gap:14px}.source{background:var(--panel);border:1px solid var(--line);padding:24px}
.source .eyebrow{color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.05em}
.source p{color:var(--muted);margin:10px 0;font-size:14px}.source strong{font-weight:700}
.source a{display:inline-flex;min-height:44px;align-items:center;font-weight:700;font-size:14px}
.providers{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.provider{padding:19px;border:1px solid var(--line);background:var(--panel)}.provider p{font-size:13px;color:var(--muted);margin:7px 0}.provider a{font-size:13px}
footer{font-size:12px;color:var(--muted);padding-block:25px;border-top:1px solid var(--line)}
@media(max-width:620px){.providers{grid-template-columns:1fr}.lead{font-size:15px}.source{padding:19px}}
"""

def render() -> str:
    d=load_registry()
    reports=[]
    for r in d["editorial_reports"]:
        provider="Acquire.com" if r["provider"]=="acquire" else "Flippa"
        reports.append(
            '<article class="source">'
            f'<span class="eyebrow">{esc(provider)} · {esc(r["date"])} · 原始研究参考</span>'
            f'<h3>{esc(r["title"])}</h3>'
            f'<p><strong>里面有什么：</strong>{esc(r["summary"])}</p>'
            f'<p><strong>对个人创业者的启发：</strong>{esc(r["takeaway"])}</p>'
            f'<a href="{esc(r["url"])}" rel="noopener noreferrer" target="_blank">前往原作者官方文章 ↗</a>'
            '</article>')
    cards=[]
    label={"acquire":"授权后才能批量使用挂牌","flippa":"授权后才能批量使用挂牌",
           "microns":"待确认许可与接口","indiehackers":"当前仅人工核实原文",
           "hackernews":"公开检索已接入，线索不自动上榜","sec":"监管申报已用于独立核实，自动源待接入"}
    for p in d["providers"]:
        cards.append(
            '<article class="provider">'
            f'<h3>{esc(p["name"])}</h3>'
            f'<p><strong>接入状态：</strong>{esc(label[p["id"]])}</p>'
            f'<p>{esc(p["analysis_use"])}</p>'
            f'<p><a href="{esc(p["url"])}" rel="noopener noreferrer" target="_blank">查看来源官网 ↗</a></p>'
            '</article>')
    return f"""<!doctype html><html lang="zh-CN" data-theme="light"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="referrer" content="no-referrer">
<meta name="description" content="见势商业信息来源说明：Acquire.com、Flippa、Microns、独立创始人故事与监管财报，区分行业研究和经过核实的项目。">
<title>商业信息来源与市场研究｜见势 JIANSHI</title>
<link rel="canonical" href="{SITE}/sources/"><style>{CSS}</style></head>
<body><header><a href="/">见势 JIANSHI</a><nav aria-label="导航">
<a href="/">给我推荐</a><a href="/projects/">正式案例</a><a href="/validation/">行业证据</a>
<button type="button" id="themeToggle" aria-pressed="false">深色模式</button></nav></header>
<main><span class="kicker">MARKET INTELLIGENCE / 研究来源</span>
<h1>我们从哪里，<br>找到真正做过生意的人？</h1>
<p class="lead">除了产品官网，见势还研究公开的创业者访谈、数字业务交易市场、经许可的数据和公司监管财报。但行业市场报告、匿名挂牌收入和卖家报价，不能自动证明某家具体企业已盈利。</p>
<div class="note"><strong>正式推荐仍然坚持严格证据门槛。</strong>
当前这页的行业研究与创业者故事是<strong>发现线索和分析背景</strong>，并不是新增已验证项目。Acquire.com、Flippa 挂牌数据尚未获得批量抓取及转载许可，因此目前<strong>未采集、未同步它们的挂牌数据库</strong>。</div>
<div class="section-head"><h2>精选原始研究</h2><span>官方原文链接 · 非经营财务审计</span></div>
<div class="items">{''.join(reports)}</div>
<div class="section-head"><h2>信息源接入状态</h2><span>明确哪些已接入，哪些仍需授权</span></div>
<div class="providers">{''.join(cards)}</div>
<section class="note" aria-label="使用说明"><strong>为什么不把挂牌的月收入直接放进推荐榜？</strong>
即使一条公开挂牌写有营收和利润，也可能是匿名卖家披露的历史数字。首先要确认合法数据使用权、企业真实身份、收入核验方式，以及是否适合一个人小资金从零启动。没有这些证据，见势不会将其标为已验证创业项目。</section>
<p><a href="/projects/">查看真正达到公司级经营证据门槛的正式案例 →</a></p>
</main><footer>见势 JIANSHI · 来源权利优先 · 不转载未授权挂牌资料 · 本页不是购买或投资建议</footer>
<script>(()=>{{const h=document.documentElement,b=document.getElementById('themeToggle');let t='light';try{{if(localStorage.getItem('jianshi-theme')==='dark')t='dark'}}catch(_){{}}
function apply(x,save){{t=x;h.dataset.theme=x;b.textContent=x==='dark'?'浅色模式':'深色模式';b.setAttribute('aria-pressed',String(x==='dark'));if(save)try{{localStorage.setItem('jianshi-theme',x)}}catch(_){{}}}}
apply(t,false);b.addEventListener('click',()=>apply(t==='light'?'dark':'light',true));}})();</script></body></html>"""

def build() -> dict:
    page=render()
    forbidden=("listing_number","source_ref_ids","empireflippers","OPP_V0.2","api_key",
               "app.acquire.com/public/","flippa.com/buy/")
    if any(word.lower() in page.lower() for word in forbidden):
        raise RuntimeError("Marketplace listing/sensitive source disclosure blocked")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(page,encoding="utf-8")
    return {"status":"PASS","sources":len(load_registry()["providers"]),
            "editorial_reports":len(load_registry()["editorial_reports"]),
            "listing_import_enabled":False}

if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False))
