#!/usr/bin/env python3
from __future__ import annotations
import html, json, os, shutil, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DIST=ROOT/"dist"
STATIC=ROOT/"static"
FIXTURE=ROOT/"fixtures"/"api.json"
API=os.getenv("JIANSHI_API_URL","").strip().rstrip("/")

def esc(v):
    return html.escape("" if v is None else str(v), quote=True)

def num(v, default=0):
    try: return float(v)
    except (TypeError,ValueError): return default

def fmt_score(v):
    return f"{num(v):.1f}"

def fmt_int(v):
    try: return f"{int(v):,}"
    except: return "0"

def fmt_money(v):
    if v in (None,""): return "—"
    try:
        n=float(v)
        if n>=1_000_000: return "$"+f"{n/1_000_000:.2f}M"
        if n>=1_000: return "$"+f"{n/1_000:.1f}K"
        return "$"+f"{n:,.0f}"
    except: return "—"

def api_get(view, **params):
    if not API:
        data=json.loads(FIXTURE.read_text(encoding="utf-8"))
        if view=="home": return data["home"]
        if view=="catalog":
            items=(data["home"].get("opportunities") or [])+(data["home"].get("watchlist") or [])
            return {"items":items,"generated_at":data["home"].get("generated_at")}
        if view=="detail":
            slug=params.get("slug","")
            if slug in data.get("details",{}): return data["details"][slug]
            items=(data["home"].get("opportunities") or [])+(data["home"].get("watchlist") or [])
            item=next((x for x in items if x.get("slug")==slug),None)
            if not item: raise KeyError(slug)
            return {"item":item,"evidence":{"github":[],"marketplace":[]},"score_history":[],
                    "disclosure":"该条目为构建测试数据。"}
        raise ValueError(view)
    query=urllib.parse.urlencode({"view":view,**params})
    req=urllib.request.Request(f"{API}?{query}",headers={"User-Agent":"JianShi-Static-Builder/0.1"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def shell(title, body, description="见势：看见正在发生的生意机会。"):
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow">
<link rel="stylesheet" href="/styles.css"></head><body>
<header><div class="wrap nav"><a class="brand" href="/">见势 <small>JIANSHI</small></a>
<nav><a href="/#opportunities">机会</a><a href="/#watch">观察池</a><a href="/#tech">技术信号</a><a href="/#about">关于</a></nav></div></header>
{body}
<footer id="about"><div class="wrap">见势｜商业机会与趋势情报。数据和评分用于研究与发现，不构成投资、收益或经营承诺。</div></footer>
<script src="/search.js" defer></script></body></html>"""

def score_row(item):
    pairs=[("热度",item.get("heat_score")),("内容",item.get("content_score")),
           ("可做",item.get("build_score")),("商业",item.get("business_score"))]
    return '<div class="score-row">'+''.join(
        f'<div class="score"><b>{fmt_score(v)}</b><span>{esc(k)}</span></div>' for k,v in pairs
    )+'</div>'

def card(item, watch=False):
    slug=esc(item.get("slug"))
    label="单源观察" if watch else "多源机会"
    cls="watch" if watch else "good"
    return f"""<a class="card" data-card href="/opportunity/{slug}/">
<span class="badge {cls}">{label}</span><h3>{esc(item.get("title"))}</h3>
<p>{esc(item.get("thesis") or "")}</p>{score_row(item)}
<div class="meta">{fmt_int(item.get("evidence_count"))} 条证据 · {fmt_int(item.get("source_count"))} 类数据源 · 综合 {fmt_score(item.get("overall_score"))}</div></a>"""

def build_home(data):
    stats=data.get("stats") or {}
    opps=data.get("opportunities") or []
    watch=data.get("watchlist") or []
    tech=data.get("tech_signals") or []
    stats_html="".join([
      f'<div class="stat"><b>{fmt_int(stats.get("marketplace_listings"))}</b><span>商业挂牌样本</span></div>',
      f'<div class="stat"><b>{fmt_int(stats.get("github_repositories"))}</b><span>GitHub 趋势仓库</span></div>',
      f'<div class="stat"><b>{fmt_int(stats.get("signals"))}</b><span>已识别信号</span></div>',
      f'<div class="stat"><b>{fmt_int(stats.get("validated_opportunities"))}</b><span>多源验证机会</span></div>',
      f'<div class="stat"><b>{fmt_int(stats.get("watch_opportunities"))}</b><span>单源观察</span></div>'
    ])
    opp_html=''.join(card(x,False) for x in opps) or '<div class="panel">当前没有通过多源 Gate 的机会。</div>'
    watch_html=''.join(card(x,True) for x in watch)
    tech_html=''.join(
      f'<a class="tech-row" href="{esc(x.get("html_url"))}" target="_blank" rel="noopener"><div><b>{esc(x.get("full_name"))}</b><br><small>{esc(x.get("description") or "")}</small></div><div>{esc(x.get("language") or "—")}</div><div>{fmt_int(x.get("stars"))} ★</div><div>{fmt_score(x.get("rank_score"))}</div></a>'
      for x in tech
    )
    body=f"""<main class="wrap">
<section class="hero"><div class="eyebrow">BUSINESS SIGNAL INTELLIGENCE</div><h1>看见正在发生的<br>生意机会。</h1>
<p>追踪全球产品、开源项目与真实商业市场。<strong>见势不会把“热”直接等同于“值得做”</strong>，只有通过多源共振 Gate 的条目才进入机会榜。</p></section>
<section class="stats">{stats_html}</section>
<section class="section" id="opportunities"><div class="section-head"><div><div class="eyebrow">VALIDATED</div><h2>已通过多源验证</h2></div><div class="section-note">技术供给 × 商业证据</div></div><div class="grid">{opp_html}</div></section>
<section class="section" id="watch"><div class="section-head"><div><div class="eyebrow">WATCHLIST</div><h2>值得继续盯</h2></div><div class="section-note">热度高，但仍缺第二类独立证据</div></div>
<div class="searchbox"><input data-search placeholder="搜索赛道、机会、关键词…" aria-label="搜索机会"></div><div class="grid">{watch_html}</div></section>
<section class="section" id="tech"><div class="section-head"><div><div class="eyebrow">TECH SIGNALS</div><h2>技术侧正在变热</h2></div><div class="section-note">仅作为早期供给信号，不等于商业机会</div></div><div class="tech-list">{tech_html}</div></section></main>"""
    return shell("见势｜看见正在发生的生意机会",body)

def evidence_github(rows):
    if not rows: return '<div class="evidence-row"><small>暂无 GitHub 证据。</small></div>'
    return ''.join(f'<a class="evidence-row" href="{esc(x.get("html_url"))}" target="_blank" rel="noopener"><b>{esc(x.get("full_name"))}</b><small>{esc(x.get("language") or "—")} · {fmt_int(x.get("stars"))} Stars · 技术排名 {fmt_score(x.get("rank_score"))}</small></a>' for x in rows)

def evidence_market(rows):
    if not rows: return '<div class="evidence-row"><small>暂无交易市场证据。</small></div>'
    return ''.join(f'<div class="evidence-row"><b>#{esc(x.get("listing_number"))} {esc(x.get("public_title") or "")}</b><small class="money">售价 {fmt_money(x.get("listing_price"))} · 月利润 {fmt_money(x.get("average_monthly_net_profit"))} · 利润率 {fmt_score(x.get("profit_margin"))}% · 每周 {fmt_score(x.get("hours_worked_per_week"))}h</small></div>' for x in rows)

def build_detail(data):
    x=data["item"]; is_ready=bool(x.get("public_ready"))
    badge=f'<span class="badge {"good" if is_ready else "watch"}>{"多源机会" if is_ready else "单源观察"}</span>'
    body=f"""<main class="wrap"><section class="detail-hero">{badge}<h1>{esc(x.get("title"))}</h1><p class="lead">{esc(x.get("thesis") or "")}</p></section>
<div class="detail-grid"><div>
<section class="panel"><h2>机会判断</h2>{score_row(x)}<div class="kv">
<div>要解决的问题</div><div>{esc(x.get("problem") or "—")}</div><div>目标用户</div><div>{esc(x.get("target_customer") or "—")}</div>
<div>商业模式</div><div>{esc(x.get("business_model") or "—")}</div><div>中国化适配</div><div>{fmt_score(x.get("china_fit"))}/100</div>
<div>一人公司适配</div><div>{fmt_score(x.get("solo_founder_fit"))}/100</div></div></section>
<section class="panel"><h2>GitHub 技术证据</h2>{evidence_github((data.get("evidence") or {}).get("github") or [])}</section>
<section class="panel"><h2>真实商业市场证据</h2>{evidence_market((data.get("evidence") or {}).get("marketplace") or [])}</section></div>
<aside><section class="panel"><h3>证据强度</h3><div class="kv"><div>数据源</div><div>{fmt_int(x.get("source_count"))}</div>
<div>有效证据</div><div>{fmt_int(x.get("evidence_count"))}</div><div>GitHub</div><div>{fmt_int(x.get("github_repo_count"))}</div>
<div>商业挂牌</div><div>{fmt_int(x.get("market_listing_count"))}</div><div>综合分</div><div>{fmt_score(x.get("overall_score"))}</div></div></section>
<div class="disclosure">{esc(data.get("disclosure") or "")}</div></aside></div></main>"""
    return shell(f'{esc(x.get("title"))}｜见势',body,x.get("thesis") or "见势机会研究")

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copy2(STATIC/"styles.css",DIST/"styles.css")
    shutil.copy2(STATIC/"search.js",DIST/"search.js")
    home=api_get("home")
    catalog=api_get("catalog").get("items",[])
    (DIST/"index.html").write_text(build_home(home),encoding="utf-8")
    search=[]
    for item in catalog:
        slug=item.get("slug")
        if not slug: continue
        detail=api_get("detail",slug=slug)
        out=DIST/"opportunity"/slug
        out.mkdir(parents=True,exist_ok=True)
        (out/"index.html").write_text(build_detail(detail),encoding="utf-8")
        search.append({"slug":slug,"title":item.get("title"),"category":item.get("category"),"public_ready":item.get("public_ready")})
    (DIST/"search-index.json").write_text(json.dumps(search,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    (DIST/"404.html").write_text(shell("未找到｜见势",'<main class="wrap"><section class="hero"><h1>这里还没有信号。</h1><p><a href="/">返回见势首页 →</a></p></section></main>'),encoding="utf-8")
    print(json.dumps({"status":"PASS","api":"live" if API else "fixture","pages":1+len(search),"opportunities":len(catalog)},ensure_ascii=False))

if __name__=="__main__": main()
