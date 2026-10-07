#!/usr/bin/env python3
from __future__ import annotations
import html, json, os, shutil, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO_ROOT=ROOT.parent
DIST=ROOT/"dist"
COMPAT_DIRS=[REPO_ROOT/"dist", REPO_ROOT/"public"]
STATIC=ROOT/"static"
FIXTURE=ROOT/"fixtures"/"api.json"
API=os.getenv("JIANSHI_API_URL","").strip().rstrip("/")
SITE=os.getenv("JIANSHI_SITE_URL","https://jianshi-bua.pages.dev").strip().rstrip("/")
NEWSLETTER_API=os.getenv("JIANSHI_NEWSLETTER_URL","").strip().rstrip("/")
if not NEWSLETTER_API and API.endswith("/public-feed"):
    NEWSLETTER_API=API[:-len("/public-feed")] + "/newsletter-subscribe"

AUTH_REQUESTED=os.getenv("JIANSHI_AUTH_ENABLED","0").strip().lower() in ("1","true","yes","on")
AUTH_ENABLED=False
SUPABASE_URL=os.getenv("JIANSHI_SUPABASE_URL","https://dalfvgehosxfyxkptxwx.supabase.co").strip().rstrip("/")
SUPABASE_PUBLISHABLE_KEY=os.getenv(
    "JIANSHI_SUPABASE_PUBLISHABLE_KEY",
    "sb_publishable_4NfyMm47GUcpBMvQ_W4mqw_rGer-_2h"
).strip()

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
        if view=="daily":
            items=(data["home"].get("opportunities") or [])+(data["home"].get("watchlist") or [])
            rows=[]
            for idx,item in enumerate(items,1):
                x=dict(item)
                x.update({
                    "snapshot_date":"2026-10-06",
                    "history_days":1,
                    "previous_date":None,
                    "seven_day_date":None,
                    "heat_delta_1d":None,
                    "overall_delta_1d":None,
                    "evidence_delta_1d":None,
                    "heat_delta_7d":None,
                    "overall_delta_7d":None,
                    "evidence_delta_7d":None,
                    "change_state":"ACCUMULATING",
                    "change_summary_zh":"历史数据正在积累，明天开始显示与昨日变化。",
                    "rising_rank":idx,
                    "build_rank":idx,
                    "content_rank":idx,
                    "overall_rank":idx,
                })
                rows.append(x)
            return {
                "generated_at":data["home"].get("generated_at"),
                "history_ready":{"one_day":False,"seven_day":False},
                "today":rows,
                "rising":sorted(rows,key=lambda x:num(x.get("heat_score")),reverse=True),
                "build":sorted(rows,key=lambda x:num(x.get("build_score")),reverse=True),
                "content":sorted(rows,key=lambda x:num(x.get("content_score")),reverse=True),
            }
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

def shell(title, body, description="见势：看见正在发生的生意机会。", canonical_path="/", robots="index,follow"):
    canonical=SITE + (canonical_path if canonical_path.startswith("/") else "/"+canonical_path)
    account_nav='<a href="/account/">我的见势</a>' if AUTH_ENABLED else ''
    auth_boot = (
        '<script>window.JIANSHI_AUTH_CONFIG='
        + json.dumps({
            "enabled":AUTH_ENABLED,
            "url":SUPABASE_URL,
            "key":SUPABASE_PUBLISHABLE_KEY,
            "site":SITE,
        },ensure_ascii=False,separators=(",",":"))
        + ';</script><script type="module" src="/account.js"></script>'
        if AUTH_ENABLED else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="{esc(robots)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website"><meta property="og:url" content="{esc(canonical)}">
<link rel="stylesheet" href="/styles.css"></head><body>
<header><div class="wrap nav"><a class="brand" href="/">见势</a>
<nav><a href="/today/">今日机会</a><a href="/rising/">正在起势</a><a href="/build/">值得做</a><a href="/content/">值得讲</a><a href="/#method">我们怎么判断</a>{account_nav}</nav></div></header>
{body}
<footer id="about"><div class="wrap">见势｜商业机会与趋势情报。数据和评分用于研究与发现，不构成投资、收益或经营承诺。 · <a href="/privacy/">隐私说明</a></div></footer>
<script src="/search.js" defer></script>{auth_boot}</body></html>"""

def score_row(item):
    pairs=[("趋势热度",item.get("heat_score")),("内容价值",item.get("content_score")),
           ("可执行性",item.get("build_score")),("商业质量",item.get("business_score"))]
    return '<div class="score-row">'+''.join(
        f'<div class="score"><b>{fmt_score(v)}</b><span>{esc(k)}</span></div>' for k,v in pairs
    )+'</div>'

def verdict(item):
    heat=num(item.get("heat_score"))
    content=num(item.get("content_score"))
    build=num(item.get("build_score"))
    business=num(item.get("business_score"))
    if item.get("public_ready"):
        return "技术趋势和真实商业市场同时出现证据，已经通过多源验证。"
    if business >= 70 and content >= 75:
        return "已有较强赚钱样本，也很适合做内容，但还需要第二类独立趋势证据。"
    if content >= 85:
        return "话题传播潜力很高，适合先做内容测试，再观察是否形成商业共振。"
    if build >= 65:
        return "个人可执行性较高，适合继续研究需求、竞品和最小可行产品。"
    if heat >= 80:
        return "趋势明显升温，但目前更适合观察，不建议仅凭热度直接下结论。"
    return "已有值得关注的信号，但证据还不够完整，继续观察。"

def card(item, watch=False, compact=False):
    slug=esc(item.get("slug"))
    label="持续观察" if watch else "已验证机会"
    cls="watch" if watch else "good"
    compact_cls=" compact" if compact else ""
    return f"""<a class="card{compact_cls}" data-card href="/opportunity/{slug}/">
<div class="card-top"><span class="badge {cls}">{label}</span><span class="card-score">综合 {fmt_score(item.get("overall_score"))}</span></div>
<h3>{esc(item.get("title"))}</h3>
<p class="card-verdict">{esc(verdict(item))}</p>
{score_row(item)}
<div class="meta">{fmt_int(item.get("evidence_count"))} 条证据 · {fmt_int(item.get("source_count"))} 类独立数据源</div></a>"""

def change_label(item):
    if item.get("previous_date") is None:
        return "历史积累中"
    delta=item.get("overall_delta_1d")
    ev=item.get("evidence_delta_1d")
    if item.get("change_state")=="NEWLY_VALIDATED":
        return "今天升级为已验证"
    if ev is not None and num(ev)>0:
        return f"今日新增 {fmt_int(ev)} 条证据"
    if delta is not None and abs(num(delta))>=0.05:
        sign="+" if num(delta)>0 else ""
        return f"较昨日 {sign}{num(delta):.1f}"
    return "较昨日基本稳定"

def rank_card(item, label, metric_key):
    return f"""<a class="rank-card" href="/opportunity/{esc(item.get("slug"))}/">
<span>{esc(label)}</span><strong>{esc(item.get("title"))}</strong>
<b>{fmt_score(item.get(metric_key))}</b><small>{esc(verdict(item))}</small></a>"""

def acceleration_label(item):
    count=int(num(item.get("rising_repo_count")))
    velocity=num(item.get("recent_stars_per_day_sum"))
    if count<=0:
        return ""
    if velocity>=1:
        return f"{count} 个技术项目近期仍在增星 · 合计约 {velocity:.0f} 星/天"
    return f"{count} 个技术项目近期仍在增星"

def daily_row(item, metric_key, metric_label, rank=None):
    rank_html=f'<span class="daily-rank">#{rank}</span>' if rank else ""
    status="已验证" if item.get("public_ready") else "持续观察"
    status_cls="good" if item.get("public_ready") else "watch"
    return f"""<a class="daily-row" href="/opportunity/{esc(item.get("slug"))}/">
<div class="daily-title">{rank_html}<div><div class="daily-name"><strong>{esc(item.get("title"))}</strong><span class="badge {status_cls}">{status}</span></div><small>{esc(item.get("change_summary_zh") or verdict(item))}</small>{f'<small class="acceleration-note">{esc(acceleration_label(item))}</small>' if acceleration_label(item) else ''}</div></div>
<div class="daily-change">{esc(change_label(item))}</div>
<div class="daily-metric"><b>{fmt_score(item.get(metric_key))}</b><span>{esc(metric_label)}</span></div>
<div class="daily-evidence"><b>{fmt_int(item.get("evidence_count"))}</b><span>有效证据</span></div>
</a>"""

def newsletter_block():
    endpoint=esc(NEWSLETTER_API)
    return f"""<section class="newsletter" id="subscribe"><div class="wrap newsletter-inner">
<div class="newsletter-copy"><span class="section-kicker">免费订阅</span><h2>每天把 Top 10 机会发给我</h2>
<p>不需要注册账号。我们会先发送确认邮件；只有完成确认后，才会开始发送每日机会摘要。可随时退订。</p></div>
<form class="newsletter-form" data-newsletter-form data-endpoint="{endpoint}">
<label class="sr-only" for="newsletter-email">邮箱</label>
<input id="newsletter-email" name="email" type="email" autocomplete="email" inputmode="email" maxlength="254" placeholder="你的邮箱，例如 name@example.com" required>
<input class="hp-field" name="company" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">
<button type="submit">订阅每日 Top 10</button>
<p class="newsletter-consent">提交即表示你同意接收见势的订阅确认邮件与每日机会摘要。未确认前不会发送每日邮件。<a href="/privacy/">查看隐私说明</a></p>
<p class="newsletter-status" data-newsletter-status role="status" aria-live="polite"></p>
</form></div></section>"""

def build_privacy_page():
    body="""<main class="wrap daily-page">
<section class="list-hero"><span class="section-kicker">隐私说明</span><h1>我们只收集完成订阅所必需的信息。</h1>
<p>见势当前的轻量订阅不需要创建账号。我们把邮箱只用于订阅确认、每日机会摘要和必要的订阅状态管理。</p></section>
<section class="panel privacy-copy">
<h2>我们收集什么</h2>
<p>当你主动提交订阅时，我们会保存：邮箱地址、订阅状态、授权时间、提交来源页面，以及发送/确认/退订等事件记录。</p>
<h2>我们怎么使用</h2>
<p>这些信息只用于处理见势的邮件订阅，包括确认订阅、发送每日 Top 10 机会、处理退订、退信和投诉状态。</p>
<h2>我们不会做什么</h2>
<p>我们不会把订阅邮箱公开展示，也不会把邮箱作为公开机会数据的一部分。未经授权，不会把邮箱出售给广告商或用于与见势订阅无关的营销。</p>
<h2>邮件服务商</h2>
<p>邮件通道启用后，见势计划使用 Resend 作为邮件发送基础设施。发送邮件所必需的数据会按服务需要传递给邮件服务商。</p>
<h2>确认与退订</h2>
<p>订阅采用双重确认。只有点击确认链接后才进入正式订阅状态。每封正式邮件都会提供退订方式；退订后停止发送每日机会。</p>
<h2>当前阶段</h2>
<p>如果邮件通道尚未启用，你提交的邮箱只会进入 WAITLIST，不会被标记成已确认订阅，也不会虚假记录为邮件已发送。</p>
</section></main>"""
    return shell("隐私说明｜见势",body,
                 "见势轻量订阅隐私说明：说明邮箱的收集、使用、确认和退订方式。",
                 "/privacy/")

def build_daily_page(kind, daily):
    cfg={
      "today":("今日机会","今天最值得先看的机会","综合判断","overall_score","把今天值得关注的方向按综合价值排序，并明确告诉你哪里发生了变化。"),
      "rising":("正在起势","哪些方向正在变热","趋势热度","heat_score","优先看趋势加速、证据增加或刚刚完成多源验证的方向。"),
      "build":("值得做","如果今天要做一个项目","可执行性","build_score","优先考虑个人或小团队更容易落地，同时具备商业证据的方向。"),
      "content":("值得讲","如果今天要做一个内容选题","内容价值","content_score","优先找反差强、故事性高、普通人容易理解并愿意传播的话题。"),
    }
    title,heading,metric_label,metric_key,lead=cfg[kind]
    rows=daily.get(kind) or daily.get("today") or []
    ready=daily.get("history_ready") or {}
    history_note = (
      "已具备昨日与 7 日历史，可查看真实变化。"
      if ready.get("seven_day") else
      "历史正在积累：明天开始显示与昨日变化，累计 7 天后显示 7 日趋势。"
      if not ready.get("one_day") else
      "已开始显示与昨日变化；7 日趋势仍在积累。"
    )
    if kind=="rising" and not ready.get("one_day"):
        history_note="历史尚未形成完整变化序列：当前先按热度展示候选；从明天起优先依据真实变化排序。"
    body=f"""<main class="wrap daily-page">
<section class="list-hero"><span class="section-kicker">{esc(title)}</span><h1>{esc(heading)}</h1><p>{esc(lead)}</p>
<div class="history-note">{esc(history_note)}</div></section>
<section class="daily-list">{"".join(daily_row(x,metric_key,metric_label,i+1) for i,x in enumerate(rows))}</section>
{newsletter_block()}
<section class="daily-explain panel"><h2>怎么看这个榜单？</h2>
<p>见势不会因为某个方向“很火”就把它直接认定为机会。榜单同时参考趋势、内容传播、可执行性、商业质量和证据变化。历史不足时我们会明确写“历史积累中”，不会伪造昨日或 7 日涨幅。</p></section>
</main>"""
    return shell(f"{title}｜见势",body,lead,f"/{kind}/")

def tech_summary(item):
    summary=(item.get("summary_zh") or "").strip()
    if summary:
        return summary
    codes=item.get("matched_queries") or []
    if "ai_agents" in codes and "llm" in codes:
        return "AI Agent 与大模型相关开源项目，聚焦智能体能力、自动化和开发工作流。"
    if "ai_agents" in codes:
        return "AI Agent 相关开源项目，聚焦智能体框架、自动化或工具协作。"
    if "saas" in codes:
        return "SaaS 相关开源项目，聚焦在线软件产品、开发框架或商业化基础设施。"
    return "大模型相关开源项目，聚焦 LLM 应用、开发工具或工作流。"

def build_home(data, daily=None):
    stats=data.get("stats") or {}
    opps=data.get("opportunities") or []
    watch=data.get("watchlist") or []
    tech=data.get("tech_signals") or []
    catalog=opps+watch
    daily=daily or {"today":[],"rising":[],"build":[],"content":[],"history_ready":{}}

    top_validated=max(opps,key=lambda x:num(x.get("overall_score")),default=None)
    rising=(daily.get("rising") or sorted(watch,key=lambda x:num(x.get("heat_score")),reverse=True))[:3]
    build_rank=(daily.get("build") or sorted(catalog,key=lambda x:num(x.get("build_score")),reverse=True))[:3]
    content_rank=(daily.get("content") or sorted(catalog,key=lambda x:num(x.get("content_score")),reverse=True))[:3]

    hero_feature=card(top_validated,False,True) if top_validated else '<div class="empty">今天还没有通过多源验证的机会，我们会继续自动扫描。</div>'

    stats_html="".join([
      f'<div class="stat"><b>{fmt_int(stats.get("marketplace_listings"))}</b><span>真实商业样本</span></div>',
      f'<div class="stat"><b>{fmt_int(stats.get("github_repositories"))}</b><span>技术项目样本</span></div>',
      f'<div class="stat"><b>{fmt_int(stats.get("validated_opportunities"))}</b><span>已验证机会</span></div>',
      f'<div class="stat"><b>{fmt_int(stats.get("watch_opportunities"))}</b><span>持续观察方向</span></div>',
      '<div class="stat"><b>6 小时</b><span>自动更新一次</span></div>'
    ])

    opp_html=''.join(card(x,False) for x in opps) or '<div class="empty">当前没有通过多源验证的机会。</div>'
    watch_html=''.join(card(x,True) for x in watch)
    rising_html=''.join(rank_card(x,f"趋势第 {i+1}","heat_score") for i,x in enumerate(rising))
    build_html=''.join(rank_card(x,f"可执行第 {i+1}","build_score") for i,x in enumerate(build_rank))
    content_html=''.join(rank_card(x,f"内容第 {i+1}","content_score") for i,x in enumerate(content_rank))
    tech_html=''.join(
      f'<a class="tech-row" href="{esc(x.get("html_url"))}" target="_blank" rel="noopener"><div><b>{esc(x.get("full_name"))}</b><br><small>{esc(tech_summary(x))}</small></div><div>{esc(x.get("language") or "—")}</div><div>{fmt_int(x.get("stars"))} 星标</div><div>趋势 {fmt_score(x.get("rank_score"))}</div></a>'
      for x in tech
    )

    body=f"""<main>
<section class="hero wrap">
<div class="hero-copy">
<span class="kicker">互联网商业机会与趋势情报平台</span>
<h1>每天帮你从海量项目里，<br><em>筛出真正值得行动的机会。</em></h1>
<p class="hero-lead">见势自动扫描开源项目和真实商业交易市场，把杂乱的数据整理成三种结论：<strong>什么值得做、什么值得讲、什么值得继续盯。</strong></p>
<div class="hero-actions"><a class="btn primary" href="/build/">我想找项目</a><a class="btn" href="/content/">我想找选题</a><a class="text-link" href="#method">它是怎么判断的？</a></div>
</div>
<div class="hero-explain">
<div class="explain-label">一句话看懂见势</div>
<p><strong>别人告诉你“什么火”，见势告诉你“这个火点有没有真实商业价值，以及你能不能做”。</strong></p>
<div class="mini-flow"><span>发现趋势</span><i>→</i><span>找赚钱证据</span><i>→</i><span>交叉验证</span><i>→</i><span>给行动结论</span></div>
</div>
</section>

<section class="wrap stats">{stats_html}</section>

<section class="wrap usecases">
<div class="usecase"><span>01</span><h3>你想做一个项目</h3><p>看“值得做”，优先找需求明确、个人能落地、商业证据更扎实的方向。</p><a href="/build/">看今天值得做什么 →</a></div>
<div class="usecase"><span>02</span><h3>你想做内容选题</h3><p>看“值得讲”，优先找反差大、故事强、普通人容易理解的话题。</p><a href="/content/">看今天值得讲什么 →</a></div>
<div class="usecase"><span>03</span><h3>你想早点发现趋势</h3><p>看“正在起势”，发现还没完全商业化、但已经出现明显增长信号的方向。</p><a href="/rising/">看哪些方向在升温 →</a></div>
</section>

<section class="wrap spotlight" id="today">
<div class="section-head"><div><span class="section-kicker">今天先看这个</span><h2>已经被技术趋势和真实商业同时验证</h2></div><div class="section-note">不是“热门推荐”，而是证据交叉后的结果</div></div>
{hero_feature}
</section>

<section class="wrap decision-grid">
<div class="decision-block" id="rising"><div class="section-head compact-head"><div><span class="section-kicker">正在起势</span><h2>哪些方向正在变热？</h2></div><a class="section-more" href="/rising/">查看完整榜单 →</a></div>{rising_html}</div>
<div class="decision-block" id="build"><div class="section-head compact-head"><div><span class="section-kicker">值得做</span><h2>如果今天要做项目</h2></div><a class="section-more" href="/build/">查看完整榜单 →</a></div>{build_html}</div>
<div class="decision-block" id="content"><div class="section-head compact-head"><div><span class="section-kicker">值得讲</span><h2>如果今天要做内容</h2></div><a class="section-more" href="/content/">查看完整榜单 →</a></div>{content_html}</div>
</section>

{newsletter_block()}

<section class="wrap section" id="opportunities"><div class="section-head"><div><span class="section-kicker">已验证机会</span><h2>证据比较完整，可以深入研究</h2></div><div class="section-note">技术供给证据与真实商业证据同时支持</div></div><div class="grid">{opp_html}</div></section>

<section class="wrap section" id="watch"><div class="section-head"><div><span class="section-kicker">持续观察</span><h2>有信号，但还不能急着下结论</h2></div><div class="section-note">热度不等于机会，继续等待更多证据</div></div>
<div class="searchbox"><input data-search placeholder="搜索方向、机会或关键词…" aria-label="搜索机会"></div><div class="grid">{watch_html}</div></section>

<section class="method" id="method"><div class="wrap">
<div class="section-head light"><div><span class="section-kicker">我们怎么判断</span><h2>不预测风口，只把证据摆到一起</h2></div></div>
<div class="method-flow">
<div><b>1</b><h3>先看什么正在变热</h3><p>跟踪 GitHub 等公开技术信号，观察项目热度、增长和活跃度。</p></div>
<div><b>2</b><h3>再看有没有人赚钱</h3><p>读取允许使用的真实商业市场数据，看收入、利润、售价和运营强度。</p></div>
<div><b>3</b><h3>必须交叉验证</h3><p>单一来源只能进入“持续观察”；不同类型证据同时出现，才升级为已验证机会。</p></div>
<div><b>4</b><h3>最后给行动分数</h3><p>分别判断趋势热度、内容价值、可执行性和商业质量，不用一个总分掩盖差异。</p></div>
</div></div></section>

<section class="wrap section" id="tech"><div class="section-head"><div><span class="section-kicker">底层趋势证据</span><h2>技术项目里，哪些正在升温</h2></div><div class="section-note">这里只是早期信号，不直接等于商业机会</div></div><div class="tech-list">{tech_html}</div></section>
</main>"""
    return shell("见势｜每天发现值得做、值得讲、值得盯的商业机会",body,
                 "见势每天扫描全球开源项目与真实商业市场，帮你发现值得做的项目、值得讲的内容和正在起势的商业机会。")

def evidence_github(rows):
    if not rows: return '<div class="evidence-row"><small>暂无开源项目证据。</small></div>'
    return ''.join(
        f'<a class="evidence-row" href="{esc(x.get("html_url"))}" target="_blank" rel="noopener">'
        f'<b>{esc(x.get("full_name"))}</b>'
        f'<span class="evidence-summary">{esc(tech_summary(x))}</span>'
        f'<small>{esc(x.get("language") or "—")} · {fmt_int(x.get("stars"))} 星标 · 趋势评分 {fmt_score(x.get("rank_score"))}</small></a>'
        for x in rows
    )

def evidence_market(rows):
    if not rows: return '<div class="evidence-row"><small>暂无交易市场证据。</small></div>'
    return ''.join(
        f'<div class="evidence-row"><b>{esc(x.get("display_title_zh") or ("互联网商业样本 #"+str(x.get("listing_number") or "")))}</b>'
        f'<small class="money">售价 {fmt_money(x.get("listing_price"))} · 月利润 {fmt_money(x.get("average_monthly_net_profit"))} · 月收入 {fmt_money(x.get("average_monthly_gross_revenue"))} · 利润率 {fmt_score(x.get("profit_margin"))}% · 每周运营 {fmt_score(x.get("hours_worked_per_week"))} 小时</small></div>'
        for x in rows
    )

def sold_activity_block(x):
    count=int(num(x.get("sold_status_count")))
    market_count=int(num(x.get("market_listing_count")))
    if count<=0 and market_count<=0:
        return ""
    ready=bool(x.get("sold_sample_ready"))
    if ready:
        body=f"""<div class="exit-metrics">
<div><b>{fmt_int(count)}</b><span>已捕获 Sold 状态样本</span></div>
<div><b>{fmt_score(x.get("median_sold_status_days_on_market"))} 天</b><span>在市天数中位数</span></div>
<div><b>{fmt_money(x.get("median_sold_status_annual_profit"))}</b><span>样本年利润中位数</span></div>
</div>
<p>样本已达到最低门槛，会作为商业质量的弱辅助证据；这部分对商业质量评分最多只影响 +5 分。</p>"""
    else:
        body=f"""<div class="exit-metrics">
<div><b>{fmt_int(count)}</b><span>已捕获 Sold 状态样本</span></div>
</div>
<p>样本还不足 5 个，目前只展示，不进入商业质量评分。</p>"""
    return f"""<section class="panel exit-panel"><span class="section-kicker">退出活跃度 · 辅助证据</span><h2>这个商业模式是否出现过已售状态？</h2>
{body}
<div class="disclosure">Sold 只表示该挂牌在官方市场中的已售状态。见势没有把最后挂牌价当作真实成交价，也不会把 Sold 样本数解释为成交率。</div>
</section>"""

def account_action_block(item):
    if not AUTH_ENABLED:
        return ""
    opportunity_id=esc(item.get("opportunity_id") or "")
    if not opportunity_id:
        return ""
    return f"""<section class="panel account-actions">
<span class="section-kicker">我的见势</span>
<h3>保存这个机会</h3>
<p>登录后可以收藏、加入观察清单，并在证据或评分变化时收到站内提醒。</p>
<div class="account-action-buttons">
<button type="button" data-save-opportunity="{opportunity_id}">收藏机会</button>
<button type="button" class="secondary" data-watch-opportunity="{opportunity_id}">加入观察</button>
</div>
<p class="account-action-status" data-account-action-status></p>
</section>"""

def build_account_page():
    if not AUTH_ENABLED:
        body="""<main class="wrap account-page">
<section class="list-hero"><span class="section-kicker">我的见势</span><h1>账户功能正在完成最后的邮件登录配置。</h1>
<p>收藏、观察清单和站内提醒的数据层已经上线。为了避免让用户遇到无法收到登录邮件的半成品体验，正式登录入口暂时不开闸。</p>
<div class="history-note">当前状态：账户数据层 PASS · RLS PASS · 登录邮件通道待自定义 SMTP。</div></section>
<section class="panel"><h2>开放后你可以做什么？</h2>
<div class="account-feature-grid">
<div><b>收藏机会</b><span>把值得继续研究的方向保存到自己的空间。</span></div>
<div><b>观察清单</b><span>关注首次验证、新增证据和明显分数变化。</span></div>
<div><b>站内提醒</b><span>不依赖邮件，也能看到你关注方向今天发生了什么。</span></div>
</div></section></main>"""
        return shell("我的见势｜账户功能准备中",body,
                     "见势账户功能准备页。登录开放后可收藏机会、建立观察清单和查看变化提醒。",
                     "/account/",robots="noindex,nofollow")

    body="""<main class="wrap account-page">
<section class="list-hero"><span class="section-kicker">我的见势</span><h1>把值得跟踪的机会留在自己的清单里。</h1>
<p>使用邮箱免密码登录。公开榜单始终免费；登录只用于收藏、观察和提醒。</p></section>

<section class="panel auth-login" data-auth-logged-out>
<h2>邮箱登录</h2>
<form class="auth-email-form" data-auth-email-form>
<input type="email" name="email" maxlength="254" autocomplete="email" placeholder="你的邮箱" required>
<button type="submit">发送登录链接</button>
<p class="auth-hint">我们会发送一次性登录链接，不需要设置密码。</p>
<p class="auth-status" data-auth-status role="status" aria-live="polite"></p>
</form>
</section>

<section class="account-dashboard" data-auth-logged-in hidden>
<div class="account-toolbar"><div><span class="section-kicker">当前账号</span><b data-auth-user-email></b></div><button type="button" class="secondary" data-auth-signout>退出登录</button></div>
<div class="account-columns">
<section class="panel"><h2>我的收藏</h2><div data-saved-list><p class="muted">正在读取…</p></div></section>
<section class="panel"><h2>我的观察</h2><div data-watch-list><p class="muted">正在读取…</p></div></section>
<section class="panel"><h2>最新提醒</h2><div data-alert-list><p class="muted">正在读取…</p></div></section>
</div>
<div class="account-settings-grid">
<section class="panel">
<span class="section-kicker">提醒偏好</span><h2>我想收到哪些提醒？</h2>
<form class="account-preferences" data-alert-preferences-form>
<label><input type="checkbox" name="in_app_enabled" checked> 站内提醒</label>
<label><input type="checkbox" name="email_enabled"> 邮件提醒</label>
<label><input type="checkbox" name="daily_digest_enabled"> 每日摘要</label>
<label><input type="checkbox" name="weekly_digest_enabled"> 每周摘要</label>
<button type="submit">保存提醒偏好</button>
<p class="account-action-status" data-preferences-status role="status" aria-live="polite"></p>
</form>
<p class="auth-hint">邮件提醒只有在邮件服务和登录邮箱都完成验证后才会真正发送。</p>
</section>
<section class="panel danger-zone">
<span class="section-kicker">隐私与数据</span><h2>清空我的见势数据</h2>
<p>清空收藏、观察清单和站内提醒，并把提醒偏好恢复为默认值。不会删除你的登录账号。</p>
<button type="button" class="secondary" data-clear-my-data>清空收藏与观察数据</button>
<p class="account-action-status" data-clear-my-data-status role="status" aria-live="polite"></p>
</section>
</div>
</section>
</main>"""
    return shell("我的见势｜收藏与观察",body,
                 "登录见势，收藏机会、建立个人观察清单并查看变化提醒。",
                 "/account/",robots="noindex,nofollow")

def github_acceleration_block(acc):
    count=int(num(acc.get("rising_repo_count")))
    if count<=0:
        return """<section class="panel acceleration-panel"><span class="section-kicker">技术加速度</span><h2>近期还没有足够的增星加速样本。</h2><p>这不会影响机会的商业验证状态，只表示当前 GitHub 动量不足以单独解释“正在起势”。</p></section>"""
    return f"""<section class="panel acceleration-panel"><span class="section-kicker">技术加速度</span><h2>{fmt_int(count)} 个相关技术项目近期仍在增星</h2>
<div class="exit-metrics">
<div><b>{fmt_score(acc.get("recent_stars_per_day_sum"))}</b><span>合计约星标/天</span></div>
<div><b>{fmt_score(acc.get("avg_recent_velocity_score"))}</b><span>平均加速度分</span></div>
<div><b>{fmt_score(acc.get("avg_observation_window_hours"))}h</b><span>平均观察窗口</span></div>
</div>
<p>这组数据来自见势连续 GitHub 快照，只用于解释技术侧是否还在加速，不替代真实商业证据。</p>
</section>"""

def build_detail(data):
    x=data["item"]; is_ready=bool(x.get("public_ready"))
    badge=f'<span class="badge {"good" if is_ready else "watch"}">{"已验证机会" if is_ready else "持续观察"}</span>'
    body=f"""<main class="wrap"><section class="detail-hero">{badge}<h1>{esc(x.get("title"))}</h1><p class="lead">{esc(x.get("thesis") or "")}</p></section>
<div class="detail-grid"><div>
<section class="panel verdict-panel"><span class="section-kicker">一句话结论</span><h2>{esc(verdict(x))}</h2>{score_row(x)}<div class="kv">
<div>要解决的问题</div><div>{esc(x.get("problem") or "—")}</div><div>目标用户</div><div>{esc(x.get("target_customer") or "—")}</div>
<div>商业模式</div><div>{esc(x.get("business_model") or "—")}</div><div>中国化适配</div><div>{fmt_score(x.get("china_fit"))}/100</div>
<div>一人公司适配</div><div>{fmt_score(x.get("solo_founder_fit"))}/100</div></div></section>
<section class="panel"><h2>开源项目证据</h2>{evidence_github((data.get("evidence") or {}).get("github") or [])}</section>
<section class="panel"><h2>真实商业样本</h2>{evidence_market((data.get("evidence") or {}).get("marketplace") or [])}</section>
{sold_activity_block(x)}
{github_acceleration_block(data.get("acceleration") or {})}</div>
<aside><section class="panel"><h3>证据强度</h3><div class="kv"><div>数据源</div><div>{fmt_int(x.get("source_count"))}</div>
<div>有效证据</div><div>{fmt_int(x.get("evidence_count"))}</div><div>GitHub</div><div>{fmt_int(x.get("github_repo_count"))}</div>
<div>商业挂牌</div><div>{fmt_int(x.get("market_listing_count"))}</div><div>综合分</div><div>{fmt_score(x.get("overall_score"))}</div></div></section>
<div class="disclosure">{"该方向已经同时获得技术供给证据与真实商业证据支持。评分只用于研究与发现，不代表收益承诺。" if is_ready else "该方向目前仍在持续观察，还缺少技术供给或真实商业中的关键一类证据，不应视为已经验证的商业机会。"}</div>{account_action_block(x)}</aside></div></main>"""
    slug=str(x.get("slug") or "").strip()
    canonical_path=f"/opportunity/{slug}/" if slug else "/"
    return shell(
        f'{esc(x.get("title"))}｜见势',
        body,
        x.get("thesis") or "见势机会研究",
        canonical_path=canonical_path,
    )

def main():
    global AUTH_ENABLED
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copy2(STATIC/"styles.css",DIST/"styles.css")
    shutil.copy2(STATIC/"search.js",DIST/"search.js")
    shutil.copy2(STATIC/"account.js",DIST/"account.js")
    home=api_get("home")
    remote_auth_enabled=bool((home.get("features") or {}).get("account_auth"))
    # Local fixture builds may exercise the enabled UI with the env flag alone.
    # Real API builds require BOTH env intent and the production DB gate.
    AUTH_ENABLED=AUTH_REQUESTED and (remote_auth_enabled if API else True)
    daily=api_get("daily")
    catalog=api_get("catalog").get("items",[])
    (DIST/"index.html").write_text(build_home(home,daily),encoding="utf-8")

    for kind in ("today","rising","build","content"):
        out=DIST/kind
        out.mkdir(parents=True,exist_ok=True)
        (out/"index.html").write_text(build_daily_page(kind,daily),encoding="utf-8")

    privacy_out=DIST/"privacy"
    privacy_out.mkdir(parents=True,exist_ok=True)
    (privacy_out/"index.html").write_text(build_privacy_page(),encoding="utf-8")

    account_out=DIST/"account"
    account_out.mkdir(parents=True,exist_ok=True)
    (account_out/"index.html").write_text(build_account_page(),encoding="utf-8")
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
    (DIST/"404.html").write_text(shell("未找到｜见势",'<main class="wrap"><section class="hero"><h1>这里还没有信号。</h1><p><a href="/">返回见势首页 →</a></p></section></main>',canonical_path="/404"),encoding="utf-8")

    urls=["/","/today/","/rising/","/build/","/content/","/privacy/"]+[f"/opportunity/{x['slug']}/" for x in search]
    sitemap='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(
        f'<url><loc>{esc(SITE+u)}</loc></url>' for u in urls
    )+'</urlset>'
    (DIST/"sitemap.xml").write_text(sitemap,encoding="utf-8")
    (DIST/"robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n",encoding="utf-8")

    # Cloudflare Pages compatibility mirrors.
    # The canonical artifact remains web/dist. During the build we also mirror
    # to common Pages output directories so a dashboard-side output setting
    # drift cannot produce a successful-but-empty deployment.
    for compat in COMPAT_DIRS:
        if compat.exists():
            shutil.rmtree(compat)
        shutil.copytree(DIST, compat)

    # If a Pages project is configured to publish the repository root, emit
    # only the generated public entrypoints there at build time. These files
    # are not committed; they exist only in the ephemeral build workspace.
    for name in ("index.html","404.html","styles.css","search.js","account.js","search-index.json","sitemap.xml","robots.txt"):
        shutil.copy2(DIST/name, REPO_ROOT/name)
    for dirname in ("opportunity","today","rising","build","content","privacy","account"):
        target=REPO_ROOT/dirname
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(DIST/dirname,target)

    print(json.dumps({
        "status":"PASS",
        "api":"live" if API else "fixture",
        "pages":6+len(search),
        "opportunities":len(catalog),
        "outputs":["web/dist","dist","public","repo-root-runtime"]
    },ensure_ascii=False))

if __name__=="__main__": main()
