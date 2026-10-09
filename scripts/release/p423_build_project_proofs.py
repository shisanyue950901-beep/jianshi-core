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
RESEARCH = ROOT / "config/p424_project_research_evidence.json"
DEST = ROOT / "web/dist/projects"
SITE = "https://jianshi-bua.pages.dev"
LEVELS = {"regulatory_filing":4,"founder_historical":3,"platform_attribution":2,"first_party_offer":1}
LABELS = {4:"监管历史财务披露",3:"创始人／企业历史自述",2:"第三方平台旁证",1:"官网产品与收费依据"}

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
.directory a strong{font-size:19px;display:block}.directory a small{color:var(--accent);font-weight:700;font-size:12px;display:block;margin-bottom:5px}.sort-controls{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0 8px}.sort-controls button{padding:11px 15px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:13px}.sort-controls button[aria-pressed=true]{border:2px solid var(--accent);background:color-mix(in srgb,var(--accent) 11%,var(--bg));font-weight:700}.directory a span{font-size:13px;color:var(--muted);display:block;margin-top:5px}
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
    evidence=json.loads(RESEARCH.read_text(encoding="utf-8"))
    if evidence.get("version")!="P4.24_RESEARCH_EVIDENCE_V1":
        raise RuntimeError("Unreviewed external evidence version")
    ids=set()
    for record in evidence["additional_evidence"]:
        case_id=record.get("id")
        if case_id in ids or case_id not in {c["id"] for c in cases}:
            raise RuntimeError("Duplicate or unknown named-company evidence")
        ids.add(case_id)
        if record.get("tier") not in LEVELS or record["tier"]=="first_party_offer":
            raise RuntimeError("Incorrect external attribution tier")
        safe_url(record["source_url"])
        for key in ("source_type","claim","period","financial_status","next_research"):
            if not isinstance(record.get(key),str) or len(record[key])<7:
                raise RuntimeError("Insufficient provenance for external finding")
        if record.get("published_on") is not None:
            import datetime
            datetime.date.fromisoformat(record["published_on"])
        match=next(x for x in cases if x["id"]==case_id)
        match["research_evidence"]=record
    for x in cases:
        record=x.get("research_evidence")
        x["evidence_level"]=LEVELS[record["tier"]] if record else 1
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
    audit = case.get("research_evidence")
    if audit:
        tier = case["evidence_level"]
        published = audit.get("published_on") or audit["period"]
        source = txt(safe_url(audit["source_url"]))
        audited_section = (
            '<section class="section"><h2>新增项目级经营依据</h2>'
            f'<p><b>证据等级：</b>L{tier} · {txt(LABELS[tier])}。'
            f'<b>来源时点：</b>{txt(published)}（不代表当期实时数据）</p>'
            f'<p>{txt(audit["claim"])}</p>'
            f'<p><a href="{source}" target="_blank" rel="noopener noreferrer">查看可归属的原始经营证据 ↗</a></p>'
            f'<p><b>下一步主动核查：</b>{txt(audit["next_research"])}</p></section>'
        )
    else:
        audited_section = (
            '<section class="section"><h2>当前补证进度</h2><p>'
            '已整理项目官网及公开产品／收费说明，尚未取得可明确归属于该公司的'
            '监管申报、创始人经营披露或独立平台经营旁证。继续主动核实，'
            '暂不推断客户量和利润。</p></section>'
        )
    if audit and audit["tier"] == "regulatory_filing":
        finance_tile='<div class="status"><b>历史公司级财务：有监管披露</b><small>2025 年 SEC 10-K 合并报告；不能证明当前季度和各产品利润</small></div>'
        findings_intro="存在可归属的历史监管申报财务，但不代表最新经营表现、单一产品利润或获客成本。"
        finance_boundary="可核实 2025 年公司合并财报的历史财务；当前业绩、业务线及可复制性仍需研究。"
    elif audit and audit["tier"] == "founder_historical":
        finance_tile='<div class="status pending"><b>历史收入：创始人／企业公开自述</b><small>历史披露未经独立审计，不代表本期收入</small></div>'
        findings_intro="找到可归属的创始人或企业历史经营自述，但尚未独立财务审计，不能当成当前净利润。"
        finance_boundary="有历史公开收入自述，但未独立审计，不能计算当前净利润或投资回报。"
    else:
        finance_tile='<div class="status pending"><b>利润／经营成果：待独立核实</b><small>没有能够独立确认当前净利润与成本的记录</small></div>'
        findings_intro="项目公开展示产品／服务及收费说明，但交易、净利与获客表现仍缺独立核验。"
        finance_boundary="仍未取得该企业自身可独立核实的财务经营数据。"
    body = f"""<span class="kicker">PROJECT EVIDENCE / 项目证据档案</span>
<h1>{txt(name)}</h1><p class="lead">{txt(case["desc"])}</p>
<p><b>编辑归类：</b>{txt(MODEL_LABELS[case["model"]])}　<b>资料记录：</b>{txt(case["verifiedOn"])}（非实时经营审计）</p>
<div class="notice"><b>证据阶段：</b>{txt(findings_intro)} 即使行业方向达标，也不能算作某家企业的经营证明；不使用行业匿名挂牌推断它的收入。</div>
<div class="statusgrid" aria-label="项目商业验证状态">
<div class="status"><b>产品／服务：有官方依据</b><small>可进入对应官网或产品页核对公开供应</small></div>
<div class="status"><b>收费机制：有公开说明</b><small>标价或收费方案不代表已成交、已收到款项</small></div>
<div class="status pending"><b>真实交易／客户：待独立核实</b><small>没有可证明实际销量、续费率或成交规模的项目级证据</small></div>
{finance_tile}
</div>
<section class="section"><h2>01｜这个项目卖什么</h2><p>{txt(case["offer"])}</p>
<h3>谁可能购买？</h3><p>{txt(case["buyer"])}</p>
<h3>公开描述的收费方式</h3><p>{txt(case["revenue"])}</p></section>
<section class="section"><h2>02｜可以核对哪些事实？</h2>{paragraphs(case["facts"])}
<div class="links"><a href="{txt(safe_url(case["officialHomeUrl"]))}" target="_blank" rel="noopener noreferrer">打开项目官方网站 ↗</a>
<a href="{txt(safe_url(case["sourceUrl"]))}" target="_blank" rel="noopener noreferrer">打开产品／收费核对依据 ↗</a>{more}</div>
{f'<p>{txt(case["additionalEvidenceNote"])}</p>' if more else ''}
<p>依据类别：项目自身官网/公开说明；第三方平台资料如有则单独标注。证据页面只支持它明确展示的事实，不证明营业额。</p></section>
{audited_section}
<section class="section"><h2>03｜经营环节与可能成本</h2>
<h3>需要做什么</h3><p>{txt(case["process"])}</p>
<h3>可能发生哪些成本</h3><p>{txt(case["cost"])}</p>
<p>以上属于编辑性经营拆解，不代表已获得该企业内部成本表。</p></section>
<section class="section"><h2>04｜还不能得出哪些结论？</h2>{paragraphs(case["unknowns"])}
<p><b>独立客户需求：</b>尚无该项目可计入的需求实证；不能将行业级技术或商业证据视为这家企业的客户证据。</p>
<p><b>项目自身销售／利润：</b>{txt(finance_boundary)} 本站的排序仅代表资料层级，不是赚钱排名。</p></section>
<section class="section"><h2>05｜下一步研究</h2><p>{txt(case.get("learning") or "进一步独立核查真实购买需求、履约成本与客户留存。")}</p>
<p><a href="/validation/">了解同类行业方向的研究边界 →</a> · <a href="/projects/">返回 20 个具名项目档案 →</a></p></section>"""
    return shell(name, str(case["desc"]), body, f"/projects/{slug}/")

def index_page(cases: list[dict]) -> str:
    cases = sorted(cases,key=lambda x:(-x["evidence_level"],x["id"]))
    count = Counter(x["model"] for x in cases)
    tiles = []
    for rank, item in enumerate(cases, 1):
        classification = MODEL_LABELS[item["model"]]
        level = item["evidence_level"]
        snippet = f"{classification} · L{level} {LABELS[level]} · 编辑资料记录 {item['verifiedOn']}"
        tiles.append(f'<a href="/projects/{txt(item["id"])}/" data-level="{level}" data-id="{txt(item["id"])}">'
                     f'<small>#{rank:02d} · {txt(LABELS[level])}</small>'
                     f'<strong>{txt(item["title"])}</strong><span>{txt(snippet)}</span>'
                     f'<span>{txt(item["desc"])}</span></a>')
    counts = " · ".join(f"{MODEL_LABELS[k]} {v}" for k,v in sorted(count.items()))
    body = f"""<span class="kicker">VERIFIABLE RESEARCH / 具名项目档案</span>
<h1>20 个项目，<br>按真实证据分层排序。</h1>
<p class="lead">先确认项目实际公开了什么，再区分“产品存在”“收费方案”“实际成交”“独立核实的利润”。我们不会把同一行业的挂牌利润填到某个具名公司名下。</p>
<div class="notice"><b>排名解释：</b>默认为资料证据的可核查层级（L4 监管申报历史财务、L3 企业历史自述、L2 平台第三方旁证、L1 官网产品及收费）。同等级按项目 ID 确定性排序，绝不按销售额、利润或创业成功率排名。少数项目已找到历史经营披露，但大多数企业的当前销量与获客成本尚无独立证据。</div>
<p class="muted">分类：{txt(counts)}</p><div class="sort-controls" role="group" aria-label="项目证据排序"><button type="button" data-sort="depth" aria-pressed="true">证据层级优先</button><button type="button" data-sort="gaps" aria-pressed="false">待补证据优先</button></div><p class="muted" id="sortHelp" aria-live="polite">优先展示具有监管申报、历史经营自述或平台旁证的项目。排名不会代表投资价值。</p><label for="projectSearch">搜索项目名称或简介</label>
<p><input type="search" id="projectSearch" aria-label="搜索具名项目" placeholder="例如 Carrd、图书出版、设计服务…" autocomplete="off"></p>
<p id="resultCount" aria-live="polite">{len(cases)} 个可查看的具名项目</p>
<div class="directory" id="directory">{''.join(tiles)}</div>
<section class="section"><h2>这些项目通过商业验证了吗？</h2>
<p>20 个项目均有公开产品或收费依据。NerdWallet 有历史 SEC 申报的公司级财务记录；Carrd、Plausible 有历史创始人／企业经营自述。<b>其余多数项目仍无独立财务资料，这不等于没有经营活动。</b>行业方向的匿名挂牌数据不能自动证明任何具名企业盈利。</p>
<a href="/validation/">查看行业商业证据与验证缺口 →</a></section>
<script>
(()=>{{const input=document.getElementById('projectSearch'),directory=document.getElementById('directory'),tiles=[...directory.querySelectorAll('a[data-level]')],count=document.getElementById('resultCount');
const buttons=[...document.querySelectorAll('[data-sort]')],help=document.getElementById('sortHelp');
function filter(){{const q=input.value.trim().toLocaleLowerCase('zh-CN');let n=0;for(const tile of tiles){{const show=!q||tile.textContent.toLocaleLowerCase('zh-CN').includes(q);tile.hidden=!show;if(show)n++}}count.textContent=n+' 个匹配的具名项目'}}
buttons.forEach(btn=>btn.addEventListener('click',()=>{{const invert=btn.dataset.sort==='gaps';tiles.sort((a,b)=>(invert?Number(a.dataset.level)-Number(b.dataset.level):Number(b.dataset.level)-Number(a.dataset.level))||a.dataset.id.localeCompare(b.dataset.id));tiles.forEach((tile,i)=>{{tile.querySelector('small').textContent='#'+String(i+1).padStart(2,'0')+' · '+tile.querySelector('small').textContent.split(' · ').at(-1);directory.append(tile)}});buttons.forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));help.textContent=invert?'优先安排公开证据较少的项目开展后续核验；不是商业潜力排名。':'依据已归属的证据层级排序；同层稳定排列，不是盈利或成功率排名。';filter()}}));
input.addEventListener('input',filter) }})();
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
