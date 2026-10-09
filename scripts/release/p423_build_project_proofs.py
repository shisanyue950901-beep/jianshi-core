#!/usr/bin/env python3
"""Publish independently sourced *project-level* evidence, not industry inference.

Use vetted first-party editorial case JSON and the two original concept covers.
Never map private marketplace disclosures to named companies.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "web/prototypes/p412e/index.html"
P413 = ROOT / "config/p413_public_project_library.json"
P415 = ROOT / "config/p415_public_case_growth.json"
DEST = ROOT / "web/dist/projects"
SITE = "https://jianshi-bua.pages.dev"

ORIGINAL_SOURCES = {
    "easlo": (
        "https://www.easlo.co/",
        "https://www.easlo.co/templates",
        "https://www.notion.com/templates/creators/easlo",
        "Notion 官方创作者页面可交叉核对模板与创作者关联；不证明销量。"),
    "louise": (
        "https://www.authorlouiselennox.com/",
        "https://www.authorlouiselennox.com/books",
        "https://www.aboutamazon.com/news/books-and-authors/how-these-authors-found-success-with-amazon-kindle-direct-publishing",
        "亚马逊早期作者专题可佐证 Kindle 直接出版经历；不能推断当前版税。"),
}
MODEL_LABELS = {
    "saas": "订阅软件", "digital": "数字产品", "content": "内容与推荐",
    "kdp": "图书出版", "fba": "实体产品", "agency": "专业服务",
}
CSS = """
:root{color-scheme:light;--bg:#f7f6f1;--ink:#202823;--muted:#59615a;--line:#c8c9c3;--panel:#fffefa;--accent:#286b56}
html[data-theme=dark]{color-scheme:dark;--bg:#080a09;--ink:#f4f2ef;--muted:#adb0ab;--line:#51534f;--panel:#151814;--accent:#86b4a3}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.8 Inter,-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
a{color:var(--accent);text-underline-offset:4px}a:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
header,main,footer{max-width:1050px;margin:auto;padding-inline:clamp(18px,4vw,52px)}
header{display:flex;align-items:center;justify-content:space-between;gap:15px;padding-block:23px;border-bottom:1px solid var(--line)}
.logo{font:500 27px Georgia,"Songti SC",serif;color:var(--ink);text-decoration:none}
header nav{display:flex;gap:16px;font-size:13px;align-items:center}header button{background:var(--panel);color:var(--ink);border:1px solid var(--line);font:inherit;padding:8px 12px;min-height:42px}main{padding-block:65px 90px}
.kicker{font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-size:12px}
h1,h2,h3{font-weight:500}h1{font:500 clamp(39px,5vw,68px)/1.18 Georgia,"Songti SC",serif;letter-spacing:-.03em;margin:16px 0 25px}
h2{font-size:25px;line-height:1.4}h3{font-size:17px;margin:0 0 7px}
.lead{font-size:17px;line-height:1.9;color:var(--muted);max-width:760px}
.notice{border-left:4px solid var(--accent);background:var(--panel);padding:15px 20px;margin:30px 0;font-size:14px}
.statusgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:35px 0}
.status{border:1px solid var(--line);background:var(--panel);padding:18px}.status b{display:block;font-size:16px;color:var(--ink)}.status small{display:block;color:var(--muted);margin-top:6px;font-size:12px}
.status.pending b{color:var(--muted)}
.section{border-top:1px solid var(--line);margin-top:45px;padding-top:23px}
.section p,.section li{font-size:15px}.section p{color:var(--muted)}.section ul{padding-left:23px}
.links{display:flex;flex-wrap:wrap;gap:12px}.links a{border:1px solid var(--line);background:var(--panel);padding:12px 16px;font-weight:600;font-size:13px}
.directory{display:grid;gap:12px;margin:24px 0}.directory a{display:block;color:var(--ink);background:var(--panel);border:1px solid var(--line);padding:18px 20px;text-decoration:none}
.directory a:hover,.directory a:focus-visible{border-color:var(--accent)}
.directory a strong{font-size:19px;display:block}.directory a span{font-size:13px;color:var(--muted);display:block;margin-top:5px}
input[type=search]{width:100%;border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:14px;font:16px sans-serif;max-width:600px}
footer{padding-block:26px 45px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
@media(max-width:590px){.statusgrid{grid-template-columns:1fr}header nav{gap:8px}.lead{font-size:15px}.links{display:grid}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
"""

def txt(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)

def safe_url(url: object) -> str:
    if not isinstance(url, str) or any(ord(c) < 32 for c in url):
        raise ValueError("Unapproved public URL")
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise ValueError("Only HTTPS first-party URLs are allowed")
    return url

def parse_cases() -> list[dict]:
    # Cover items are editorial fields in original public HTML, not private data.
    source = SOURCE.read_text(encoding="utf-8")
    found = re.search(r"const ITEMS=(\[.*?\]);\s*ITEMS\.forEach", source, re.S)
    if not found:
        raise RuntimeError("Original cover registry changed")
    originals = json.loads(found.group(1))[:2]
    if {x.get("id") for x in originals} != set(ORIGINAL_SOURCES):
        raise RuntimeError("Unexpected original cover profiles")
    cases = []
    for item in originals:
        home, evidence, extra, note = ORIGINAL_SOURCES[item["id"]]
        if f"officialHomeUrl:'{home}',sourceUrl:'{evidence}'" not in source:
            raise RuntimeError("Public homepage source mismatches approved registry")
        cases.append({
            **{k: v for k, v in item.items() if k != "image"},
            "officialHomeUrl": home, "sourceUrl": evidence,
            "additionalEvidenceUrl": extra, "additionalEvidenceNote": note,
            "verifiedOn": "2026-10-08",
        })
    for path in [P413, P415]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("public_policy", {}).get("no_unverified_profit"):
            raise RuntimeError("Case batch cannot pass publication policy")
        cases.extend({**x, "verifiedOn": data["verified_on"]} for x in data["cases"])
    if len(cases) != 20 or len({x["id"] for x in cases}) != 20:
        raise RuntimeError("Expected exactly 20 distinct named research profiles")
    for x in cases:
        if not re.fullmatch(r"[a-z0-9-]{2,60}", x["id"]):
            raise RuntimeError("Unsafe project slug")
        if x.get("kind") != "case" or x.get("model") not in MODEL_LABELS:
            # First two are explicitly associated to models after page data.
            if x["id"] == "easlo":
                x["model"] = "digital"
            elif x["id"] == "louise":
                x["model"] = "kdp"
            else:
                raise RuntimeError("Unknown editorial classification")
        for key in ["officialHomeUrl", "sourceUrl"]:
            safe_url(x[key])
        if x.get("additionalEvidenceUrl"):
            safe_url(x["additionalEvidenceUrl"])
        for key in ["offer", "buyer", "revenue", "facts", "unknowns"]:
            if not x.get(key):
                raise RuntimeError("Missing required first-party or unknown evidence")
    return cases

THEME_JS = """<script>(()=>{'use strict';const html=document.documentElement,button=document.getElementById('themeToggle');let current='light';try{if(localStorage.getItem('jianshi-theme')==='dark')current='dark'}catch(_){}function apply(next,persist){current=next;html.dataset.theme=next;button.textContent=next==='light'?'深色模式':'浅色模式';button.setAttribute('aria-pressed',String(next==='dark'));if(persist)try{localStorage.setItem('jianshi-theme',next)}catch(_){}}apply(current,false);button.addEventListener('click',()=>apply(current==='light'?'dark':'light',true));})();</script>"""

def shell(title: str, desc: str, body: str, canonical: str) -> str:
    return f"""<!doctype html><html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="referrer" content="no-referrer"><meta name="description" content="{txt(desc)}">
<title>{txt(title)}｜见势 JIANSHI</title><link rel="canonical" href="{txt(SITE+canonical)}">
<style>{CSS}</style></head><body><header><a class="logo" href="/">见势 JIANSHI</a>
<nav aria-label="页面导航"><a href="/validation/">方向证据</a><a href="/projects/">具名项目</a><a href="/">首页</a><button id="themeToggle" type="button" aria-pressed="false">深色模式</button></nav></header>
<main>{body}</main><footer>见势 · 商业研究信息，不构成财务审计、投资建议或收益承诺。<a href="/privacy/">隐私说明</a></footer>{THEME_JS}</body></html>"""

def paragraphs(items: list[str]) -> str:
    return "<ul>"+"".join(f"<li>{txt(x)}</li>" for x in items)+"</ul>"

def project_page(case: dict) -> str:
    slug, name = case["id"], case["title"]
    more = ""
    if case.get("additionalEvidenceUrl"):
        more = f'<a href="{txt(safe_url(case["additionalEvidenceUrl"]))}" target="_blank" rel="noopener noreferrer">官方第三方交叉依据 ↗</a>'
    body = f"""<span class="kicker">PROJECT EVIDENCE / 项目证据档案</span>
<h1>{txt(name)}</h1><p class="lead">{txt(case["desc"])}</p>
<p><b>编辑归类：</b>{txt(MODEL_LABELS[case["model"]])}　<b>资料记录：</b>{txt(case["verifiedOn"])}（非实时经营审计）</p>
<div class="notice"><b>判定结论：</b>项目官方页面公开展示了产品／服务及收费说明；目前没有足够独立证据验证实际成交、客户规模、净利润或可复制性。该结论仅针对本项目的第一方资料，不使用行业匿名挂牌推断它的收入。</div>
<div class="statusgrid" aria-label="项目商业验证状态">
<div class="status"><b>产品／服务：有官方依据</b><small>可进入对应官网或产品页核对公开供应</small></div>
<div class="status"><b>收费机制：有公开说明</b><small>标价或收费方案不代表已成交、已收到款项</small></div>
<div class="status pending"><b>真实交易／客户：待独立核实</b><small>没有可证明实际销量、续费率或成交规模的项目级证据</small></div>
<div class="status pending"><b>利润／经营成果：待独立核实</b><small>没有能够独立确认当前净利润与成本的记录</small></div>
</div>
<section class="section"><h2>01｜这个项目卖什么</h2><p>{txt(case["offer"])}</p>
<h3>谁可能购买？</h3><p>{txt(case["buyer"])}</p>
<h3>公开描述的收费方式</h3><p>{txt(case["revenue"])}</p></section>
<section class="section"><h2>02｜可以核对哪些事实？</h2>{paragraphs(case["facts"])}
<div class="links"><a href="{txt(safe_url(case["officialHomeUrl"]))}" target="_blank" rel="noopener noreferrer">打开项目官方网站 ↗</a>
<a href="{txt(safe_url(case["sourceUrl"]))}" target="_blank" rel="noopener noreferrer">打开产品／收费核对依据 ↗</a>{more}</div>
{f'<p>{txt(case["additionalEvidenceNote"])}</p>' if more else ''}
<p>依据类别：项目自身官网/公开说明；第三方平台资料如有则单独标注。证据页面只支持它明确展示的事实，不证明营业额。</p></section>
<section class="section"><h2>03｜经营环节与可能成本</h2>
<h3>需要做什么</h3><p>{txt(case["process"])}</p>
<h3>可能发生哪些成本</h3><p>{txt(case["cost"])}</p>
<p>以上属于编辑性经营拆解，不代表已获得该企业内部成本表。</p></section>
<section class="section"><h2>04｜还不能得出哪些结论？</h2>{paragraphs(case["unknowns"])}
<p><b>独立客户需求：</b>尚无该项目可计入的需求实证；不能将行业级技术或商业证据视为这家企业的客户证据。</p>
<p><b>项目自身销售／利润：</b>未经核实，不提供数字和赚钱排序。</p></section>
<section class="section"><h2>05｜下一步研究</h2><p>{txt(case.get("learning") or "进一步独立核查真实购买需求、履约成本与客户留存。")}</p>
<p><a href="/validation/">了解同类行业方向的研究边界 →</a> · <a href="/projects/">返回 20 个具名项目档案 →</a></p></section>"""
    return shell(name, str(case["desc"]), body, f"/projects/{slug}/")

def index_page(cases: list[dict]) -> str:
    count = Counter(x["model"] for x in cases)
    tiles = []
    for item in cases:
        classification = MODEL_LABELS[item["model"]]
        snippet = f"{classification} · 记录于 {item['verifiedOn']} · 经营结果待独立核实"
        tiles.append(f'<a href="/projects/{txt(item["id"])}/"><strong>{txt(item["title"])}</strong><span>{txt(snippet)}</span><span>{txt(item["desc"])}</span></a>')
    counts = " · ".join(f"{MODEL_LABELS[k]} {v}" for k,v in sorted(count.items()))
    body = f"""<span class="kicker">VERIFIABLE RESEARCH / 具名项目档案</span>
<h1>20 个项目，<br>逐项说明证据和缺口。</h1>
<p class="lead">先确认项目实际公开了什么，再区分“产品存在”“收费方案”“实际成交”“独立核实的利润”。我们不会把同一行业的挂牌利润填到某个具名公司名下。</p>
<div class="notice"><b>当前核验边界：</b>20 项均有第一方公开产品或服务的资料入口；实际销量、净利润、客户数、获客成本与真实需求仍需要进一步核实。资料日期是编辑记录时间，不代表本日重新联网验证。</div>
<p class="muted">分类：{txt(counts)}</p><label for="projectSearch">搜索项目名称或简介</label>
<p><input type="search" id="projectSearch" aria-label="搜索具名项目" placeholder="例如 Carrd、图书出版、设计服务…" autocomplete="off"></p>
<p id="resultCount" aria-live="polite">{len(cases)} 个可查看的具名项目</p>
<div class="directory" id="directory">{''.join(tiles)}</div>
<section class="section"><h2>这些项目通过商业验证了吗？</h2>
<p>现阶段只核对了公开的产品／服务及收费方式，<b>没有完成项目级独立成交与财务审计</b>。上一页的六类行业方向证据是另一层研究数据，不能自动用于证明这里任意企业已经盈利。</p>
<a href="/validation/">查看行业商业证据与验证缺口 →</a></section>
<script>
(()=>{{const input=document.getElementById('projectSearch'),tiles=[...document.querySelectorAll('#directory a')],count=document.getElementById('resultCount');
input.addEventListener('input',()=>{{const q=input.value.trim().toLocaleLowerCase('zh-CN');let n=0;for(const tile of tiles){{const show=!q||tile.textContent.toLocaleLowerCase('zh-CN').includes(q);tile.hidden=!show;if(show)n++}}count.textContent=n+' 个匹配的具名项目'}})}})();
</script>"""
    return shell("20 个具名项目证据档案", "项目的公开产品、收费依据、独立验证缺口及原始官方页面", body, "/projects/")

def build() -> dict:
    cases = parse_cases()
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST/"index.html").write_text(index_page(cases), encoding="utf-8")
    for item in cases:
        out=DEST/item["id"]/"index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(project_page(item), encoding="utf-8")
    paths = [p for p in DEST.rglob("index.html")]
    if len(paths) != 21:
        raise RuntimeError("Expected one listing and 20 individual dossiers")
    for path in paths:
        page=path.read_text(encoding="utf-8")
        for forbidden in ["Empire Flippers","listing_number","public_title","source_url","OPP_V0.2"]:
            if forbidden.lower() in page.lower():
                raise RuntimeError("Protected source term in dossier: "+str(path))
    return {"status":"PASS","cases":len(cases),"public_pages":len(paths)}

if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False))
