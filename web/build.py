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
CONCRETE_PROTOTYPES=REPO_ROOT/"config"/"p46a_concrete_opportunity_prototypes.json"
API=os.getenv("JIANSHI_API_URL","").strip().rstrip("/")
SITE=os.getenv("JIANSHI_SITE_URL","https://jianshi-bua.pages.dev").strip().rstrip("/")
NEWSLETTER_API=os.getenv("JIANSHI_NEWSLETTER_URL","").strip().rstrip("/")
if not NEWSLETTER_API and API.endswith("/public-feed"):
    NEWSLETTER_API=API[:-len("/public-feed")] + "/newsletter-subscribe"

ANALYTICS_API=os.getenv("JIANSHI_ANALYTICS_URL","").strip().rstrip("/")
if not ANALYTICS_API and API.endswith("/public-feed"):
    ANALYTICS_API=API[:-len("/public-feed")] + "/behavior-track"

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
    analytics_boot = (
        '<script>window.JIANSHI_ANALYTICS_CONFIG='
        + json.dumps({
            "enabled":bool(ANALYTICS_API),
            "endpoint":ANALYTICS_API,
        },ensure_ascii=False,separators=(",",":"))
        + ';</script><script src="/analytics.js" defer></script>'
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="{esc(robots)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website"><meta property="og:url" content="{esc(canonical)}">
<link rel="stylesheet" href="/styles.css"></head><body>
<header><div class="wrap nav"><a class="brand" href="/">见势</a>
<nav><a href="/opportunities/">发现机会</a><a href="/today/">今日推荐</a><a href="/rising/">正在起势</a><a href="/content/">内容选题</a><a href="/#method">我们怎么判断</a>{account_nav}</nav></div></header>
{body}
<footer id="about"><div class="wrap">见势｜商业机会发现与决策平台。数据和评分用于研究与发现，不构成投资、收益或经营承诺。 · <a href="/privacy/">隐私说明</a></div></footer>
<script src="/search.js" defer></script>{auth_boot}{analytics_boot}</body></html>"""

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


def decision_label(item):
    business=num(item.get("business_score"))
    build=num(item.get("build_score"))
    heat=num(item.get("heat_score"))
    content=num(item.get("content_score"))
    if item.get("public_ready") and business>=70:
        return "值得深入研究", "good"
    if item.get("public_ready"):
        return "值得研究", "good"
    if build>=65 or heat>=75 or content>=85:
        return "值得验证", "validate"
    return "持续观察", "watch"

def card(item, watch=False, compact=False):
    slug=esc(item.get("slug"))
    label,cls=decision_label(item)
    state="validated" if item.get("public_ready") else "watch"
    state_text="多源已验证" if item.get("public_ready") else "证据未完整"
    compact_cls=" compact" if compact else ""
    return f"""<a class="card{compact_cls}" data-card data-state="{state}" href="/opportunity/{slug}/">
<div class="card-top"><span class="badge {cls}">{esc(label)}</span><span class="card-score">{state_text} · 综合 {fmt_score(item.get("overall_score"))}</span></div>
<h3>{esc(item.get("title"))}</h3>
<p class="card-verdict">{esc(verdict(item))}</p>
{score_row(item)}
<div class="meta">{fmt_int(item.get("evidence_count"))} 条有效证据 · {fmt_int(item.get("source_count"))} 类独立数据源</div></a>"""

def prototype_card(item, compact=False):
    evidence=item.get("overseas_validation") or {}
    screening=item.get("china_screening") or {}
    slug=esc(item.get("slug"))
    compact_cls=" compact" if compact else ""
    solo_fit=str(screening.get("solo_fit") or "—").split("。",1)[0]
    return f"""<a class="research-card{compact_cls}" data-card data-state="validated" href="/opportunity/{slug}/">
<div class="research-card-top"><span class="badge validate">{esc(item.get("status") or "值得研究")}</span><span>海外已验证项目</span></div>
<h3>{esc(item.get("title"))}</h3>
<p>{esc(item.get("one_liner") or "")}</p>
<div class="research-card-meta"><span><b>{fmt_int(evidence.get("direct_samples"))}</b>直接商业样本</span><span><b>{fmt_int(evidence.get("commercial_source_diversity"))}</b>商业来源种类</span></div>
<div class="research-card-fit">一人公司适配：{esc(solo_fit)}</div>
<span class="research-card-link">查看完整研究 →</span>
</a>"""

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
<section class="list-hero"><span class="section-kicker">隐私说明</span><h1>只收集提供服务和验证产品所必需的数据。</h1>
<p>见势当前把订阅信息与匿名产品使用分析分开处理。我们不会把匿名浏览分析用于广告画像，也不会在行为分析中保存姓名、邮箱、IP 地址、完整 User-Agent 或完整搜索词。</p></section>
<section class="panel privacy-copy">
<h2>匿名使用分析</h2>
<p>为了判断见势是否真的对用户有价值，我们会使用第一方随机浏览器标识记录页面访问、机会详情浏览、第二个机会浏览、机会库筛选、来源跳转、30 秒阅读和滚动深度等事件。</p>
<p>随机浏览器标识最多使用 90 天后轮换；原始行为事件默认保留 90 天。搜索只记录输入长度和结果数量，不保存你输入的原始搜索文字。来源跳转只记录目标域名。</p>
<p>如果浏览器启用了 Global Privacy Control（GPC）或 Do Not Track（DNT），见势不会发送这些分析事件。你也可以随时主动关闭。</p>
<div class="privacy-actions">
<button type="button" data-analytics-opt-out>关闭匿名使用分析</button>
<button type="button" class="secondary" data-analytics-opt-in>重新开启</button>
</div>
<p class="analytics-privacy-status" data-analytics-status role="status" aria-live="polite"></p>
<h2>邮件订阅收集什么</h2>
<p>邮件订阅方面，我们只收集完成订阅所必需的信息。当你主动提交订阅时，我们会保存邮箱地址、订阅状态、授权时间、提交来源页面，以及发送、确认、退订等必要事件记录。</p>
<h2>邮件信息怎么使用</h2>
<p>邮箱只用于处理见势邮件订阅，包括确认订阅、发送机会摘要、处理退订、退信和投诉状态。邮箱不会进入匿名行为分析表。</p>
<h2>我们不会做什么</h2>
<p>我们不会把订阅邮箱公开展示，也不会出售订阅邮箱。匿名产品分析不接入第三方广告追踪器，不用于跨站广告画像。</p>
<h2>邮件服务商</h2>
<p>邮件通道启用后，见势计划使用 Resend 作为邮件发送基础设施。发送邮件所必需的数据会按服务需要传递给邮件服务商。</p>
<h2>确认与退订</h2>
<p>订阅采用双重确认。只有点击确认链接后才进入正式订阅状态。每封正式邮件都会提供退订方式；退订后停止发送每日机会。</p>
<h2>当前阶段</h2>
<p>如果邮件通道尚未启用，你提交的邮箱只会进入 WAITLIST，不会被标记成已确认订阅，也不会虚假记录为邮件已发送。</p>
</section></main>"""
    return shell("隐私说明｜见势",body,
                 "见势隐私说明：匿名产品使用分析、邮箱订阅、确认和退订。",
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

def build_home(data, daily=None, prototypes=None):
    stats=data.get("stats") or {}
    opps=data.get("opportunities") or []
    watch=data.get("watchlist") or []
    tech=data.get("tech_signals") or []
    catalog=opps+watch
    prototypes=prototypes or []
    daily=daily or {"today":[],"rising":[],"build":[],"content":[],"history_ready":{}}

    top_validated=max(opps,key=lambda x:num(x.get("overall_score")),default=None)
    rising=(daily.get("rising") or sorted(catalog,key=lambda x:num(x.get("heat_score")),reverse=True))[:3]
    build_rank=(daily.get("build") or sorted(catalog,key=lambda x:num(x.get("build_score")),reverse=True))[:3]
    content_rank=(daily.get("content") or sorted(catalog,key=lambda x:num(x.get("content_score")),reverse=True))[:3]

    hero_feature=card(top_validated,False,True) if top_validated else '<div class="empty">今天还没有达到多源验证门槛的趋势方向，我们会继续扫描和核对证据。</div>'
    if prototypes:
        direct_samples=sum(int(num((x.get("overseas_validation") or {}).get("direct_samples"))) for x in prototypes)
        source_diversity=max([int(num((x.get("overseas_validation") or {}).get("commercial_source_diversity"))) for x in prototypes] or [0])
        priority_count=sum(1 for x in prototypes if x.get("status")=="优先研究")
        stats_html="".join([
          f'<div class="stat"><b>{fmt_int(len(prototypes))}</b><span>首批项目研究</span></div>',
          f'<div class="stat"><b>{fmt_int(direct_samples)}</b><span>直接商业样本</span></div>',
          f'<div class="stat"><b>{fmt_int(source_diversity)}</b><span>商业来源种类</span></div>',
          f'<div class="stat"><b>{fmt_int(priority_count)}</b><span>优先研究项目</span></div>',
          '<div class="stat"><b>6 小时</b><span>信号更新周期</span></div>'
        ])
    else:
        stats_html="".join([
          f'<div class="stat"><b>{fmt_int(stats.get("validated_opportunities"))}</b><span>已验证机会</span></div>',
          f'<div class="stat"><b>{fmt_int(stats.get("watch_opportunities"))}</b><span>观察方向</span></div>',
          f'<div class="stat"><b>{fmt_int(stats.get("marketplace_listings"))}</b><span>商业样本</span></div>',
          f'<div class="stat"><b>{fmt_int(stats.get("github_repositories"))}</b><span>技术样本</span></div>',
          '<div class="stat"><b>6 小时</b><span>信号更新周期</span></div>'
        ])

    prototype_html=''.join(prototype_card(x) for x in prototypes[:6]) or '<div class="empty">首批项目研究正在整理。</div>'
    opp_html=''.join(card(x,False) for x in opps[:6]) or '<div class="empty">当前没有通过多源验证的趋势方向。</div>'
    watch_html=''.join(card(x,True) for x in watch[:6]) or '<div class="empty">当前没有新的观察方向。</div>'
    rising_html=''.join(rank_card(x,f"趋势第 {i+1}","heat_score") for i,x in enumerate(rising))
    build_html=''.join(rank_card(x,f"可执行第 {i+1}","build_score") for i,x in enumerate(build_rank))
    content_html=''.join(rank_card(x,f"内容第 {i+1}","content_score") for i,x in enumerate(content_rank))
    tech_html=''.join(
      f'<a class="tech-row" href="{esc(x.get("html_url"))}" target="_blank" rel="noopener"><div><b>{esc(x.get("full_name"))}</b><br><small>{esc(tech_summary(x))}</small></div><div>{esc(x.get("language") or "—")}</div><div>{fmt_int(x.get("stars"))} 星标</div><div>趋势 {fmt_score(x.get("rank_score"))}</div></a>'
      for x in tech[:6]
    )

    body=f"""<main>
<section class="hero wrap">
<div class="hero-copy">
<span class="kicker">海外已验证项目 · 中文筛选</span>
<h1>看懂海外已经跑通的项目，<br><em>找到你值得验证的方向。</em></h1>
<p class="hero-lead">见势先从海外真实商业样本里确认一种项目形态<strong>确实存在</strong>，再替中国用户做筛选、中文解释和第一轮低成本验证路径。不是照抄项目，也不是收益承诺。</p>
<div class="hero-actions"><a class="btn primary" href="/opportunities/#validated-projects">先看首批项目</a><a class="btn" href="/#method">我们怎么判断</a><a class="text-link" href="/opportunities/#trend-directions">趋势观察 →</a></div>
</div>
<div class="hero-explain">
<div class="explain-label">见势解决什么问题？</div>
<p><strong>不是告诉你“什么火”，而是先回答：海外有没有真实项目、为什么值得中国用户看、第一轮应该怎么验证。</strong></p>
<div class="mini-flow"><span>海外项目</span><i>→</i><span>商业证据</span><i>→</i><span>中国适配</span><i>→</i><span>低成本验证</span></div>
</div>
</section>

<section class="wrap stats">{stats_html}</section>

<section class="wrap section" id="validated-projects"><div class="section-head"><div><span class="section-kicker">首批项目研究</span><h2>先看具体项目，再决定值不值得花时间验证</h2></div><a class="section-more" href="/opportunities/#validated-projects">查看全部项目 →</a></div>
<div class="research-grid">{prototype_html}</div>
<p class="section-footnote">这些项目只说明对应商业形态在海外真实存在，并经过见势的中文筛选；当前商业样本仍来自单一商业来源，不能把挂牌信息当成收益承诺。</p></section>

<section class="wrap usecases">
<div class="usecase"><span>01</span><h3>找项目</h3><p>先确认海外确实存在真实商业样本，再看项目结构，而不是只追热门关键词。</p><a href="/opportunities/#validated-projects">进入首批项目 →</a></div>
<div class="usecase"><span>02</span><h3>判断适配</h3><p>直接看更适合谁、不太适合谁，以及哪些部分值得中国个人创业者借鉴。</p><a href="/opportunities/#validated-projects">比较项目 →</a></div>
<div class="usecase"><span>03</span><h3>低成本验证</h3><p>每个项目都给出第一轮验证路径，先验证需求和付费，再决定是否投入开发、库存或团队。</p><a href="/opportunities/#validated-projects">看验证路径 →</a></div>
</section>

<section class="wrap spotlight" id="trend-signals">
<div class="section-head"><div><span class="section-kicker">趋势观察 · 辅助信号</span><h2>宽泛方向可以帮你发现变化，但不等于具体项目推荐</h2></div><a class="section-more" href="/today/">查看趋势榜单 →</a></div>
{hero_feature}
</section>

<section class="wrap section" id="trend-directions"><div class="section-head"><div><span class="section-kicker">已验证趋势方向</span><h2>保留原有四维评分，用来补充观察，不替代具体项目研究</h2></div><a class="section-more" href="/opportunities/#trend-directions">查看全部趋势 →</a></div><div class="grid">{opp_html}</div></section>

<section class="wrap decision-grid">
<div class="decision-block"><div class="section-head compact-head"><div><span class="section-kicker">正在起势</span><h2>哪些方向正在升温</h2></div><a class="section-more" href="/rising/">完整榜单 →</a></div>{rising_html}</div>
<div class="decision-block"><div class="section-head compact-head"><div><span class="section-kicker">更容易落地</span><h2>个人更值得研究什么</h2></div><a class="section-more" href="/build/">完整榜单 →</a></div>{build_html}</div>
<div class="decision-block"><div class="section-head compact-head"><div><span class="section-kicker">内容选题</span><h2>哪些方向值得讲</h2></div><a class="section-more" href="/content/">完整榜单 →</a></div>{content_html}</div>
</section>

<section class="wrap section"><div class="section-head"><div><span class="section-kicker">待验证趋势</span><h2>有信号，但现在还不应该急着做</h2></div><a class="section-more" href="/opportunities/#trend-directions">进入趋势观察 →</a></div><div class="grid">{watch_html}</div></section>

<section class="method" id="method"><div class="wrap">
<div class="section-head light"><div><span class="section-kicker">我们怎么判断</span><h2>先确认项目真实存在，再讨论是否适合你</h2></div></div>
<div class="method-flow">
<div><b>1</b><h3>找到海外真实项目</h3><p>先从允许使用的公开商业市场和产品信号里确认：这种项目形态不是想象出来的。</p></div>
<div><b>2</b><h3>锁定商业证据</h3><p>样本数量和来源数量分开计算；公开挂牌价不当成真实成交价，也不把技术热度当成赚钱证据。</p></div>
<div><b>3</b><h3>做中国用户筛选</h3><p>再判断适合谁、不适合谁、哪些结构值得借鉴。一人公司适配属于编辑判断，不伪装成来源事实。</p></div>
<div><b>4</b><h3>给出第一轮验证</h3><p>优先设计低成本验证动作，让用户先验证需求、付费或渠道，再决定是否继续投入。</p></div>
</div></div></section>

<section class="wrap section" id="tech"><div class="section-head"><div><span class="section-kicker">证据库一角</span><h2>这些技术项目正在形成供给信号</h2></div><div class="section-note">技术热度只是辅助证据，不等于商业机会</div></div><div class="tech-list">{tech_html}</div></section>

{newsletter_block()}
</main>"""
    return shell("见势｜海外已验证项目中文筛选",body,
                 "见势从海外真实商业样本中寻找已经存在的项目形态，替中国用户做筛选、中文解释和第一轮低成本验证。")

def build_opportunities_page(catalog, prototypes=None):
    prototypes=prototypes or []
    items=sorted(catalog,key=lambda x:(not bool(x.get("public_ready")),-num(x.get("overall_score"))))
    validated=sum(1 for x in items if x.get("public_ready"))
    watching=max(0,len(items)-validated)
    project_cards=''.join(prototype_card(x) for x in prototypes) or '<div class="empty">首批项目研究正在整理。</div>'
    cards=''.join(card(x,not bool(x.get("public_ready"))) for x in items) or '<div class="empty">趋势方向正在扩充。</div>'
    direct_samples=sum(int(num((x.get("overseas_validation") or {}).get("direct_samples"))) for x in prototypes)
    priority_count=sum(1 for x in prototypes if x.get("status")=="优先研究")
    body=f"""<main class="wrap catalog-page">
<section class="list-hero catalog-hero"><span class="section-kicker">发现项目</span><h1>先看海外已经真实存在的项目，再决定你要验证什么。</h1>
<p>见势先把海外商业样本整理成具体项目研究，再补充趋势评分。样本证明项目形态存在，不代表复制后一定获得相同结果。</p>
<div class="catalog-summary"><span><b>{fmt_int(len(prototypes))}</b> 首批项目研究</span><span><b>{fmt_int(priority_count)}</b> 优先研究</span><span><b>{fmt_int(direct_samples)}</b> 直接商业样本</span><span><b>{fmt_int(len(items))}</b> 趋势方向</span></div></section>

<section class="section" id="validated-projects"><div class="section-head"><div><span class="section-kicker">首批项目研究</span><h2>每个项目都回答六个最重要的问题</h2></div><div class="section-note">项目是什么 · 海外验证 · 中国参考价值 · 适合谁 · 怎么验证 · 风险未知</div></div>
<div class="research-grid">{project_cards}</div>
<div class="panel project-library-note"><strong>当前证据边界：</strong>首批项目的商业样本来自 1 类商业来源。样本数量不等于来源数量，挂牌价不等于真实成交价；“一人公司适配”是见势的编辑筛选，不是来源事实。</div></section>

<section class="section" id="trend-directions"><div class="section-head"><div><span class="section-kicker">趋势方向 · 辅助观察</span><h2>四维评分保留，但不再冒充具体创业项目</h2></div><div class="section-note">{fmt_int(validated)} 个已验证趋势 · {fmt_int(watching)} 个待验证趋势</div></div>
<section class="catalog-toolbar">
<input data-catalog-search placeholder="搜索趋势方向、类别或关键词…" aria-label="搜索趋势方向">
<div class="catalog-filters" role="group" aria-label="趋势方向筛选">
<button type="button" class="active" data-catalog-filter="all">全部</button>
<button type="button" data-catalog-filter="validated">已验证</button>
<button type="button" data-catalog-filter="watch">待验证</button>
</div></section>
<section class="grid catalog-grid" data-catalog-grid>{cards}</section>
<section class="panel catalog-help"><h2>怎么使用这两层信息？</h2><p>先用上面的“首批项目研究”判断一个具体项目值不值得继续验证；下面的趋势方向只用于补充观察技术供给、内容价值和市场变化。趋势高，不等于你应该直接做。</p></section></section>
</main>"""
    return shell("发现项目｜见势",body,
                 "浏览见势首批海外已验证项目研究，并用趋势方向作为辅助观察。",
                 "/opportunities/")

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
    # The visual preview never collects an email or pretends signup is live.
    # Actual email/password and optional Magic Link are emitted ONLY behind
    # the same double-gated AUTH_ENABLED flag. Production remains closed.
    if not AUTH_ENABLED:
        body="""<main class="wrap account-page">
<div class="account-entry-shell">
<aside class="account-story">
<a class="account-story-brand" href="/" aria-label="返回见势首页">见势 <span>JIANSHI</span></a>
<div class="account-story-main">
<span class="account-story-kicker">YOUR RESEARCH SPACE / 研究空间</span>
<h1>好机会，<br><em>值得持续跟踪。</em></h1>
<p>从发现方向，到核查证据，再到记录自己的判断。你的研究应该有迹可循。</p>
<div class="account-story-journey" aria-label="研究的三个步骤">
<span><b>01</b> 发现方向</span><span><b>02</b> 收藏研究</span><span><b>03</b> 持续观察</span>
</div></div>
<p class="account-story-foot">见势 JIANSHI 2.0 · 商业机会发现与决策</p>
</aside>
<section class="account-access" aria-labelledby="account-entry-title">
<div class="account-availability"><span class="account-availability-dot" aria-hidden="true"></span>账户注册／登录尚未开放</div>
<span class="account-access-eyebrow">CREATE YOUR SPACE</span>
<h2 id="account-entry-title">创建你的<br>研究空间</h2>
<p class="account-access-lead">账户功能正在完成最后的邮件登录配置。现在你仍然可以免费浏览全部公开研究内容。</p>
<div class="account-form-preview" aria-label="注册界面预览，尚不能输入或提交邮箱">
<span class="account-input-label">邮箱地址</span>
<div class="account-input-example" aria-hidden="true">name@example.com <span>✉</span></div>
<button type="button" disabled>邮箱注册／登录 · 即将开放 <span aria-hidden="true">→</span></button>
<p class="account-form-help">开放后使用邮箱一次性链接，无需密码；首次使用即可注册。</p>
</div>
<p class="account-gate-note">当前不收集注册邮箱，不发送验证码，也不会为你创建账户。正式开放前需要完成邮件送达与账户安全验收。</p>
<a class="account-back-link" href="/discover/">暂不注册，先去发现项目 <span aria-hidden="true">↗</span></a>
</section>
</div>
<section class="account-feature-section" aria-label="账户开放后的功能">
<div class="account-feature-heading"><span>COMING SOON</span><h2>未来，你可以在这里做什么？</h2></div>
<div class="account-feature-grid">
<div><span class="account-feature-icon" aria-hidden="true">✧</span><b>收藏机会</b><span>把值得继续研究的方向保存到自己的空间。</span></div>
<div><span class="account-feature-icon" aria-hidden="true">◈</span><b>观察清单</b><span>记录关注的项目和重要证据变化。</span></div>
<div><span class="account-feature-icon" aria-hidden="true">◎</span><b>站内提醒</b><span>上线后查看你关心的研究内容有何变化。</span></div>
</div></section></main>"""
        return shell("我的见势｜账户功能准备中",body,
                     "见势账户功能准备页。登录开放后可收藏机会、建立观察清单和查看变化提醒。",
                     "/account/",robots="noindex,nofollow")

    body="""<main class="wrap account-page">
<div class="account-entry-shell" data-auth-logged-out>
<aside class="account-story">
<a class="account-story-brand" href="/" aria-label="返回见势首页">见势 <span>JIANSHI</span></a>
<div class="account-story-main">
<span class="account-story-kicker">YOUR RESEARCH SPACE / 研究空间</span>
<h1>好机会，<br><em>值得持续跟踪。</em></h1>
<p>发现方向、收藏证据、关注变化。首次邮箱登录会创建你的账户。</p>
<div class="account-story-journey" aria-label="研究的三个步骤">
<span><b>01</b> 发现方向</span><span><b>02</b> 收藏研究</span><span><b>03</b> 持续观察</span>
</div></div>
<p class="account-story-foot">见势 JIANSHI 2.0 · 商业机会发现与决策</p>
</aside>
<section class="account-access auth-login" aria-labelledby="account-entry-title">
<div class="account-availability account-availability--ready"><span class="account-availability-dot" aria-hidden="true"></span>账户注册／登录</div>
<span class="account-access-eyebrow">WELCOME TO JIANSHI</span>
<h2 id="account-entry-title">开启你的<br>研究空间</h2>
<p class="account-access-lead">用邮箱和密码注册，验证邮箱后即可登录。已有账户可直接登录。</p>
<div class="account-auth-tabs" aria-label="选择账户操作">
<button type="button" data-auth-switch="register" aria-pressed="true">注册</button>
<button type="button" data-auth-switch="login" aria-pressed="false">登录</button>
</div>
<form class="auth-email-form account-live-form" data-auth-register-form data-auth-panel="register">
<label class="account-input-label" for="register-email">邮箱地址</label>
<input id="register-email" type="email" name="email" maxlength="254" autocomplete="email" placeholder="name@example.com" required>
<label class="account-input-label" for="register-password">设置密码（至少 8 位）</label>
<input id="register-password" type="password" name="password" minlength="8" maxlength="128" autocomplete="new-password" required>
<label class="account-input-label" for="register-confirm">再次输入密码</label>
<input id="register-confirm" type="password" name="confirm_password" minlength="8" maxlength="128" autocomplete="new-password" required>
<button type="submit">注册账户 <span aria-hidden="true">→</span></button>
<p class="auth-hint">注册后请先完成邮箱验证；密码仅用于登录，不会记录在网页中。</p>
<p class="auth-status" data-auth-register-status role="status" aria-live="polite"></p>
</form>
<form class="auth-email-form account-live-form" data-auth-login-form data-auth-panel="login" hidden>
<label class="account-input-label" for="login-email">邮箱地址</label>
<input id="login-email" type="email" name="email" maxlength="254" autocomplete="username" required>
<label class="account-input-label" for="login-password">密码</label>
<input id="login-password" type="password" name="password" autocomplete="current-password" required>
<button type="submit">登录我的见势 <span aria-hidden="true">→</span></button>
<button type="button" class="account-text-button" data-auth-forgot>忘记密码？</button>
<p class="auth-status" data-auth-login-status role="status" aria-live="polite"></p>
</form>
<form class="auth-email-form account-live-form" data-auth-reset-form data-auth-panel="reset" hidden>
<h3>找回密码</h3>
<p class="auth-hint">输入注册邮箱，收到邮件后可以设置新密码。</p>
<label class="account-input-label" for="reset-email">邮箱地址</label>
<input id="reset-email" type="email" name="email" maxlength="254" autocomplete="email" required>
<button type="submit">发送重置密码邮件 <span aria-hidden="true">→</span></button>
<button type="button" class="account-text-button" data-auth-back>返回登录</button>
<p class="auth-status" data-auth-reset-status role="status" aria-live="polite"></p>
</form>
<details class="account-magic-alt">
<summary>也可以使用邮箱免密码登录</summary>
<form class="auth-email-form account-live-form" data-auth-email-form>
<label class="account-input-label" for="account-email">邮箱地址</label>
<input id="account-email" type="email" name="email" maxlength="254" autocomplete="email" placeholder="name@example.com" required>
<button type="submit">发送登录链接 <span aria-hidden="true">→</span></button>
<p class="auth-hint">只发送一次性登录链接；不会要求提供邮箱密码。</p>
<p class="auth-status" data-auth-status role="status" aria-live="polite"></p>
</form>
</details>
<a class="account-back-link" href="/discover/">先不登录，去发现项目 <span aria-hidden="true">↗</span></a>
</section>
</div>

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
<section class="panel account-change-password">
<span class="section-kicker">账户安全</span><h2>修改登录密码</h2>
<p class="auth-hint">忘记密码邮件验证完成后，可以在这里设置新密码。</p>
<form class="auth-email-form account-live-form" data-auth-change-form>
<label for="change-password">新密码（至少 8 位）</label>
<input id="change-password" type="password" name="password" minlength="8" maxlength="128" autocomplete="new-password" required>
<label for="change-confirm">再次输入新密码</label>
<input id="change-confirm" type="password" name="confirm_password" minlength="8" maxlength="128" autocomplete="new-password" required>
<button type="submit">保存新密码</button>
<p class="auth-status" data-auth-change-status role="status" aria-live="polite"></p>
</form></section>
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

def bullet_list(items):
    values=[x for x in (items or []) if x]
    if not values:
        return '<p class="unknown-note">当前没有足够信息。</p>'
    return '<ul class="research-list">'+''.join(f'<li>{esc(x)}</li>' for x in values)+'</ul>'

def build_concrete_prototype(x, global_disclaimer, all_prototypes=None):
    evidence=x.get("overseas_validation") or {}
    screening=x.get("china_screening") or {}
    direct=evidence.get("direct_samples")
    source_div=evidence.get("commercial_source_diversity")
    observed=evidence.get("observed_niches") or []
    niche_bits=[]
    if evidence.get("observed_niche_count") is not None:
        niche_bits.append(f'{fmt_int(evidence.get("observed_niche_count"))} 个公开细分类目')
    if observed:
        niche_bits.append("样本涉及："+ "、".join(str(v) for v in observed[:9]))
    niche_note="；".join(niche_bits) if niche_bits else "当前样本覆盖多个公开分类。"
    slug=str(x.get("slug") or "").strip()
    related=[p for p in (all_prototypes or []) if str(p.get("slug") or "")!=slug]
    related=sorted(related,key=lambda p:(p.get("status")!="优先研究",str(p.get("title") or "")))[:3]
    related_html=''.join(prototype_card(p,True) for p in related)
    related_section=f"""<section class="section related-research">
<div class="section-head"><div><span class="section-kicker">继续比较</span><h2>再看 1–2 个项目，比较后再决定方向</h2></div><a class="section-more" href="/opportunities/#validated-projects">查看全部项目 →</a></div>
<div class="research-grid related-grid">{related_html}</div>
</section>""" if related_html else ""

    body=f"""<main class="wrap">
<section class="detail-hero concrete-hero">
<span class="badge validate">{esc(x.get("status") or "值得研究")}</span>
<span class="detail-status">海外已验证项目 · 中文筛选</span>
<h1>{esc(x.get("title"))}</h1>
<p class="lead">{esc(x.get("one_liner") or "")}</p>
</section>

<div class="detail-grid"><div>
<section class="panel verdict-panel">
<span class="section-kicker">01 · 见势推荐</span>
<h2>{esc(x.get("editorial_judgement") or "")}</h2>
<p>{esc(global_disclaimer)}</p>
</section>

<section class="panel">
<span class="section-kicker">02 · 这个项目是什么</span>
<h2>先看生意模型，再决定要不要继续研究。</h2>
<p>{esc(x.get("what_it_is") or "")}</p>
<div class="kv">
<div>项目类型</div><div>{esc(x.get("project_type") or "—")}</div>
<div>当前状态</div><div>{esc(x.get("status") or "值得研究")}</div>
</div>
</section>

<section class="panel">
<span class="section-kicker">03 · 海外真实验证</span>
<h2>先确认这种项目在海外真实存在。</h2>
<div class="evidence-facts">
<div><b>{fmt_int(direct)}</b><span>直接商业样本</span></div>
<div><b>{fmt_int(source_div)}</b><span>商业来源种类</span></div>
<div><b>{esc(evidence.get("as_of") or "—")}</b><span>证据快照日期</span></div>
</div>
<p><strong>证据口径：</strong>{esc(evidence.get("evidence_scope") or "—")}</p>
<p><strong>能证明什么：</strong>{esc(evidence.get("conclusion") or "—")}</p>
<p>{esc(niche_note)}</p>
<div class="disclosure">{esc(evidence.get("caveat") or "")}</div>
</section>

<section class="panel">
<span class="section-kicker">04 · 对中国用户有没有参考价值</span>
<h2>不是照搬项目，而是判断什么值得复制。</h2>
<p>{esc(screening.get("why_relevant") or "")}</p>
<div class="kv">
<div>更适合谁</div><div>{esc("、".join(screening.get("suitable_for") or []) or "—")}</div>
<div>不太适合谁</div><div>{esc("、".join(screening.get("not_ideal_for") or []) or "—")}</div>
<div>一人公司适配</div><div>{esc(screening.get("solo_fit") or "—")}</div>
<div>可以复制什么</div><div>{esc(screening.get("copy_path") or "—")}</div>
<div>为什么推荐</div><div>{esc(screening.get("recommendation_reason") or "—")}</div>
</div>
</section>

<section class="panel">
<span class="section-kicker">05 · 第一轮怎么验证</span>
<h2>不要先重投入，先验证最关键的假设。</h2>
{bullet_list(x.get("first_validation") or [])}
</section>

<section class="panel">
<span class="section-kicker">06 · 风险与未知</span>
<h2>哪些事情现在还不能替你下结论？</h2>
<h3>主要风险</h3>
{bullet_list(x.get("risks") or [])}
<h3>当前未知</h3>
{bullet_list(x.get("unknowns") or [])}
</section>
</div>

<aside>
<section class="panel concrete-aside">
<h3>这页解决什么问题？</h3>
<div class="kv">
<div>我们找什么</div><div>海外真实项目</div>
<div>我们做什么</div><div>筛选、中文解释、推荐</div>
<div>目标用户</div><div>寻找项目方向的中国用户</div>
<div>当前结论</div><div>{esc(x.get("status") or "值得研究")}</div>
</div>
<a class="text-link aside-link" href="/opportunities/#validated-projects">返回首批项目 →</a>
</section>
<div class="disclosure">见势不会把海外案例直接包装成“中国也一定能做”。我们只把已验证的项目结构、证据和可复制部分整理出来，供你继续判断。</div>
</aside></div>
{related_section}
</main>"""
    return shell(
        f'{esc(x.get("title"))}｜见势项目研究',
        body,
        x.get("one_liner") or "见势海外项目中文筛选",
        canonical_path=f"/opportunity/{slug}/",
        robots="noindex,nofollow",
    )

def build_detail(data):
    x=data["item"]; is_ready=bool(x.get("public_ready"))
    label,cls=decision_label(x)
    badge=f'<span class="badge {cls}">{esc(label)}</span>'
    validation="多源已验证" if is_ready else "证据仍未完整"
    body=f"""<main class="wrap">
<section class="detail-hero">{badge}<span class="detail-status">{validation}</span><h1>{esc(x.get("title"))}</h1><p class="lead">{esc(x.get("thesis") or "")}</p></section>
<div class="detail-grid"><div>
<section class="panel verdict-panel"><span class="section-kicker">01 · 决策摘要</span><h2>{esc(verdict(x))}</h2>{score_row(x)}
<div class="decision-note">见势结论用于决定“是否值得继续研究”，不是收益预测或投资建议。</div></section>

<section class="panel"><span class="section-kicker">02 · 机会说明</span><h2>它解决谁的什么问题？</h2><div class="kv">
<div>要解决的问题</div><div>{esc(x.get("problem") or "—")}</div>
<div>目标用户</div><div>{esc(x.get("target_customer") or "—")}</div>
<div>商业模式</div><div>{esc(x.get("business_model") or "—")}</div></div></section>

<section class="panel"><span class="section-kicker">03 · 商业验证</span><h2>有没有真实商业样本？</h2>{evidence_market((data.get("evidence") or {}).get("marketplace") or [])}
<div class="disclosure">挂牌价格、公开收入或利润字段只按来源允许的口径展示；asking price 不等于真实成交价。</div></section>
{sold_activity_block(x)}

<section class="panel"><span class="section-kicker">04 · 执行判断</span><h2>对个人创业者意味着什么？</h2><div class="kv">
<div>中国化适配</div><div>{fmt_score(x.get("china_fit"))}/100</div>
<div>一人公司适配</div><div>{fmt_score(x.get("solo_founder_fit"))}/100</div>
<div>MVP 难度</div><div>尚未完成编辑审查</div>
<div>资金强度</div><div>尚未完成编辑审查</div>
<div>获客难度</div><div>尚未完成编辑审查</div></div>
<p class="unknown-note">我们宁愿明确写“未知”，也不会为了让报告看起来完整而编造成本、周期或收入。</p></section>

<section class="panel"><span class="section-kicker">05 · 内容机会</span><h2>这个方向适不适合做选题？</h2>
<p>当前内容价值评分为 <strong>{fmt_score(x.get("content_score"))}/100</strong>。高分表示这个方向更容易形成可理解、可传播的商业内容；具体选题角度仍需要结合下面的真实证据，不自动生成夸大结论。</p></section>

<section class="panel"><span class="section-kicker">06 · 证据与来源</span><h2>技术供给证据</h2>{evidence_github((data.get("evidence") or {}).get("github") or [])}</section>
{github_acceleration_block(data.get("acceleration") or {})}
</div>
<aside>
<section class="panel"><h3>证据强度</h3><div class="kv">
<div>验证状态</div><div>{validation}</div>
<div>数据源</div><div>{fmt_int(x.get("source_count"))}</div>
<div>有效证据</div><div>{fmt_int(x.get("evidence_count"))}</div>
<div>技术证据</div><div>{fmt_int(x.get("technical_evidence_count") or x.get("github_repo_count"))}</div>
<div>商业证据</div><div>{fmt_int(x.get("commercial_evidence_count") or x.get("market_listing_count"))}</div>
<div>综合参考分</div><div>{fmt_score(x.get("overall_score"))}</div></div></section>
<div class="disclosure">{"该方向已经同时获得技术供给证据与真实商业证据支持。" if is_ready else "该方向仍缺少技术供给或真实商业中的关键一类证据，因此只能作为验证候选。"}</div>
{account_action_block(x)}
</aside></div></main>"""
    slug=str(x.get("slug") or "").strip()
    canonical_path=f"/opportunity/{slug}/" if slug else "/"
    return shell(
        f'{esc(x.get("title"))}｜见势',
        body,
        x.get("thesis") or "见势机会研究",
        canonical_path=canonical_path,
    )

# P4.9 evidence-first public research UI.
# User-facing research pages deliberately exclude editorial suitability, replication,
# recommendation and execution advice unless backed by explicit source evidence.
_RESEARCH_CACHE={}

def _research_fallback(item):
    evidence=item.get("overseas_validation") or {}
    return {
        "slug":item.get("slug"),
        "title":item.get("title"),
        "sample_definition":"按项目所属业务类型整理并去重，原始数据渠道不对外披露。",
        "evidence_source":{},
        "active_sample_count":evidence.get("direct_samples"),
        "priced_sample_count":None,
        "metrics":{
            "median_asking_price":None,
            "median_monthly_gross_revenue":None,
            "median_monthly_net_profit":None,
            "median_profit_margin_pct":None,
            "median_hours_worked_per_week":None,
        },
        "niche_distribution":[],
        "samples":[],
        "evidence_boundary":[
            "该页面当前仅提供已整理的数据摘要；详细记录保存在内部核验系统。",
            "挂牌报价不等于最终成交价。",
            "公开页面不披露具体渠道与原始项目标识。",
            "这些样本不能用于证明团队规模、中国市场适配性、可复制性或未来收益。",
        ],
    }

def research_for(item):
    slug=str(item.get("slug") or "").strip()
    if not slug:
        return _research_fallback(item)
    if slug in _RESEARCH_CACHE:
        return _RESEARCH_CACHE[slug]
    data=None
    if API:
        try:
            data=api_get("research",slug=slug)
        except Exception:
            data=None
    if not isinstance(data,dict) or not data.get("slug"):
        data=_research_fallback(item)
    _RESEARCH_CACHE[slug]=data
    return data

def _source_method(value):
    return {
        "OFFICIAL_API":"官方 API",
        "PUBLIC_API":"公开 API",
        "PUBLIC_WEB":"公开网页",
    }.get(str(value or "").upper(),str(value or "—"))

def _fmt_research_time(value):
    if not value:
        return "—"
    s=str(value).replace("T"," ")
    return s[:16]+" UTC" if len(s)>=16 else s

def fmt_zh_currency(value):
    if value in (None, ""): return "—"
    try:
        n=float(value)
        if n>=10000:
            return f"{n/10000:.2f}万美元"
        return f"{n:,.0f}美元"
    except (ValueError, TypeError):
        return "—"

def _metric(value, kind="number"):
    if value in (None,""):
        return "—"
    if kind=="money":
        return fmt_zh_currency(value)
    if kind=="pct":
        try:return f"{float(value):.1f}%"
        except:return "—"
    if kind=="hours":
        try:return f"{float(value):.1f} 小时"
        except:return "—"
    return fmt_int(value)

def shell(title, body, description="见势：基于公开商业市场数据的项目研究。", canonical_path="/", robots="index,follow"):
    canonical=SITE + (canonical_path if canonical_path.startswith("/") else "/"+canonical_path)
    account_nav='<a href="/account/">账户</a>' if AUTH_ENABLED else ''
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
    analytics_boot = (
        '<script>window.JIANSHI_ANALYTICS_CONFIG='
        + json.dumps({
            "enabled":bool(ANALYTICS_API),
            "endpoint":ANALYTICS_API,
        },ensure_ascii=False,separators=(",",":"))
        + ';</script><script src="/analytics.js" defer></script>'
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="{esc(robots)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website"><meta property="og:url" content="{esc(canonical)}">
<link rel="stylesheet" href="/styles.css"></head><body>
<header class="site-header"><div class="wrap nav-v2"><a class="brand-v2" href="/"><strong>见势</strong><span>JIANSHI</span></a>
<nav><a href="/opportunities/">项目研究库</a><a href="/today/">趋势信号</a><a href="/#method">数据口径</a><a href="/privacy/">隐私</a>{account_nav}</nav></div></header>
{body}
<footer><div class="wrap footer-v2"><div><strong>见势 JIANSHI</strong><span>公开商业数据研究工具</span></div><p>数据用于研究与信息整理，不构成投资、经营或收益承诺。</p></div></footer>
<script src="/search.js" defer></script>{auth_boot}{analytics_boot}</body></html>"""

def _published_niches(research, limit=3):
    """Only use the evidence-backed, publishable research distribution."""
    names=[]
    for row in research.get("niche_distribution") or []:
        if not isinstance(row, dict):
            continue
        name=str(row.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
        if len(names)>=limit:
            break
    return names

def _research_comparison_rows(prototypes, records):
    """Render a descriptive comparison, never a profitability ranking."""
    out=[]
    for item, research in zip(prototypes, records):
        metrics=research.get("metrics") or {}
        slug=esc(item.get("slug") or "")
        title=esc(research.get("title") or item.get("title") or "研究分类")
        total=fmt_int(research.get("active_sample_count"))
        priced=research.get("priced_sample_count")
        priced_text=fmt_int(priced) if priced is not None else "—"
        shown=fmt_int(min(len(research.get("samples") or []),6))
        out.append(
            f'<tr><th scope="row"><a href="/opportunity/{slug}/">{title} <span aria-hidden="true">↗</span></a></th>'
            f'<td>{total}</td><td>{priced_text}</td>'
            f'<td>{_metric(metrics.get("median_monthly_gross_revenue"),"money")}</td>'
            f'<td>{_metric(metrics.get("median_monthly_net_profit"),"money")}</td>'
            f'<td>{_metric(metrics.get("median_hours_worked_per_week"),"hours")}</td>'
            f'<td>{shown}</td></tr>'
        )
    return "".join(out) or '<tr><td colspan="7">当前尚无可公开的分类对照数据。</td></tr>'


def _public_niche_bars(research, limit=8):
    """Use only the public aggregated niche distribution; no source records."""
    sample_total=int(num(research.get("active_sample_count")))
    rows=[]
    invalid_counts=0
    for niche in (research.get("niche_distribution") or [])[:12]:
        if not isinstance(niche,dict):
            continue
        name=str(niche.get("name") or "").strip()
        try: count=int(niche.get("count") or 0)
        except (ValueError,TypeError,OverflowError): continue
        if not name or count<=0:
            continue
        if sample_total<=0:
            continue
        if count>sample_total:
            invalid_counts+=1
            continue
        percent=100.0*count/sample_total
        safe_name=esc(name)
        rows.append(
            f'<div class="niche-bar-v2">'
            f'<div class="niche-bar-v2-caption"><strong>{safe_name}</strong><span>{fmt_int(count)} 个样本</span></div>'
            f'<div class="niche-bar-v2-track" role="img" aria-label="{safe_name}，覆盖 {fmt_int(count)} 个分类样本">'
            f'<span style="width:{percent:.1f}%"></span></div></div>'
        )
        if len(rows)>=limit:
            break
    anomaly_note=(
        '<p class="niche-data-warning-v2">部分领域统计数量超过该分类样本总数，已暂停展示异常项目，等待数据核验。</p>'
        if invalid_counts else ''
    )
    if not rows:
        return '<p class="taxonomy-empty">当前没有足够的公开分类计数，无法绘制领域分布。</p>'+anomaly_note
    return '<div class="niche-chart-v2">'+''.join(rows)+'</div>'+anomaly_note


def _public_case_completeness(research):
    """Describe missing fields in up to six already-anonymized preview rows."""
    cases=(research.get("samples") or [])[:6]
    if not cases:
        return '<p class="case-coverage-v2">当前没有可公开的匿名案例预览；不将缺失数据计算为零。</p>'
    specs=[
        ("月营收", "monthly_revenue_band"),
        ("月净利润", "monthly_profit_band"),
        ("挂牌报价", "asking_price_band"),
    ]
    stats=[]
    for label,key in specs:
        missing=sum(1 for row in cases if not isinstance(row,dict) or str(row.get(key) or "").strip() in ("","未披露"))
        stats.append(f'<span>{esc(label)}未披露 <strong>{fmt_int(missing)}</strong> 条</span>')
    return (
        f'<div class="case-coverage-v2"><p>下列缺失数量只统计本页展示的 '
        f'<strong>{fmt_int(len(cases))}</strong> 条匿名摘要，不代表全分类缺失率。</p>'
        f'<div class="case-coverage-stats-v2">{"".join(stats)}</div></div>'
    )


def prototype_card(item, compact=False):
    research=research_for(item)
    niches=_published_niches(research)
    niche_html=('<div class="research-card-v2-niches"><span>样本涉及领域</span><p>'+esc(' · '.join(niches))+'</p></div>') if niches else ''
    slug=esc(item.get("slug"))
    source=research.get("evidence_source") or {}
    metrics=research.get("metrics") or {}
    compact_cls=" compact" if compact else ""
    return f"""<a class="research-card-v2{compact_cls}" data-card data-state="research" href="/opportunity/{slug}/">
<div class="research-card-v2-head"><span>海外项目分类</span><span>见势研究</span></div>
<h3>{esc(research.get("title") or item.get("title"))}</h3>
<div class="research-card-v2-grid">
<div><span>项目案例</span><b>{fmt_int(research.get("active_sample_count"))}</b></div>
<div><span>月营收中位数</span><b>{_metric(metrics.get("median_monthly_gross_revenue"),"money")}</b></div>
<div><span>月净利润中位数</span><b>{_metric(metrics.get("median_monthly_net_profit"),"money")}</b></div>
<div><span>周工时中位数</span><b>{_metric(metrics.get("median_hours_worked_per_week"),"hours")}</b></div>
</div>
{niche_html}
<div class="research-card-v2-foot"><span>第三方公开数据整理</span><span>查看证据档案 →</span></div>
</a>"""

def build_home(data, daily=None, prototypes=None):
    prototypes=prototypes or []
    research=[research_for(x) for x in prototypes]
    total_samples=sum(int(num(x.get("active_sample_count"))) for x in research)
    source_names=sorted({str((x.get("evidence_source") or {}).get("name") or "") for x in research if (x.get("evidence_source") or {}).get("name")})
    latest=max([str((x.get("evidence_source") or {}).get("last_success_at") or "") for x in research] or [""])
    cards=''.join(prototype_card(x) for x in prototypes)
    body=f"""<main>
<section class="hero-v2 wrap">
<div class="eyebrow">海外商业项目研究</div>
<h1>先看证据，<br>再判断项目。</h1>
<p>把海外商业项目的公开资料整理为中文研究档案。展示经过归类的案例、统计指标与数据边界，不公开底层数据渠道和原始项目标识。</p>
<div class="hero-actions-v2"><a class="primary-link" href="/opportunities/">进入项目研究库</a><a href="/#method">查看数据口径</a></div>
</section>

<section class="wrap terminal-strip">
<div><span>研究分类</span><b>{fmt_int(len(prototypes))}</b></div>
<div><span>已整理项目案例</span><b>{fmt_int(total_samples)}</b></div>
<div><span>内容呈现</span><b>中文分类 · 脱敏统计</b></div>
</section>

<section class="wrap reading-path-v2" aria-labelledby="reading-path-heading">
<div class="reading-path-v2-intro">
<span class="eyebrow">阅读路线</span>
<h2 id="reading-path-heading">三步读懂一份项目研究档案。</h2>
<p>项目研究库展示公开挂牌样本；趋势信号展示系统研究指标。两类信息需要分别阅读，不能相互替代。</p>
</div>
<div class="reading-path-v2-grid">
<a href="/opportunities/"><span>01 · 找到分类</span><strong>先看业务类型与样本数量</strong><small>了解当前纳入了哪些公开挂牌项目。</small><em>查看研究分类 →</em></a>
<a href="/opportunities/#reading-metrics"><span>02 · 理解数字</span><strong>读懂中位数和匿名摘要</strong><small>区别统计中位数、披露值和逐条区间。</small><em>阅读指标说明 →</em></a>
<a href="/opportunities/#category-comparison"><span>03 · 横向对照</span><strong>把六类统计放在一起看</strong><small>只比较已公开字段，不按收益潜力排序。</small><em>查看分类对照 →</em></a>
</div>
</section>

<section class="wrap research-section" id="research-categories">
<div class="section-title-v2"><div><span>研究范围</span><h2>首批研究分类</h2></div><p>所有卡片均来自公开商业挂牌数据，不使用编辑推荐分数排序。</p></div>
<div class="research-grid-v2">{cards}</div>
</section>

<section class="method-v2" id="method"><div class="wrap">
<div class="section-title-v2 light"><div><span>统计说明</span><h2>公开页面只陈述可被证据支持的内容</h2></div></div>
<div class="method-grid-v2">
<div><b>01</b><h3>样本存在</h3><p>确认某一商业资产类型在公开市场中存在真实在售挂牌。</p></div>
<div><b>02</b><h3>数据口径</h3><p>按业务类别对案例去重统计，后台保留原始记录用于核查。</p></div>
<div><b>03</b><h3>统计指标</h3><p>分类页展示统计中位数；案例页只展示金额区间，避免暴露可反查的原始记录。</p></div>
<div><b>04</b><h3>证据边界</h3><p>第三方财务数据未独立审计，报价不等于成交价，也不能证明未来收益。</p></div>
</div></div></section>

<section class="wrap signal-link-section">
<div><div class="eyebrow">研究指标</div><h2>趋势信号与商业样本分开看</h2><p>技术热度、内容传播和系统评分保留在独立模块，不与商业资产证据混成一个结论。</p></div>
<a href="/today/">查看趋势信号 →</a>
</section>
{newsletter_block()}
</main>"""
    return shell(
        "见势｜海外商业项目研究",
        body,
        "基于公开商业市场数据的项目研究。展示样本、挂牌披露与证据边界，不替用户推断收益或可复制性。",
    )

def build_opportunities_page(catalog, prototypes=None):
    prototypes=prototypes or []
    cards=''.join(prototype_card(x) for x in prototypes)
    research=[research_for(x) for x in prototypes]
    total_samples=sum(int(num(x.get("active_sample_count"))) for x in research)
    comparison_rows=_research_comparison_rows(prototypes,research)
    body=f"""<main class="wrap catalog-v2">
<section class="catalog-hero-v2">
<div class="eyebrow">海外商业项目档案</div>
<h1>项目研究库</h1>
<p>浏览经过中文整理的海外项目类别及统计摘要。原始渠道、项目标识与逐条精确数据仅限内部核查。</p>
<div class="catalog-meta-v2"><span>{fmt_int(len(prototypes))} 个研究分类</span><span>{fmt_int(total_samples)} 个项目案例</span><span>中文整理 · 脱敏呈现</span></div>
</section>
<section class="catalog-guide-v2" id="reading-metrics" aria-labelledby="metric-heading">
<div class="section-title-v2"><div><span>阅读帮助</span><h2 id="metric-heading">这些研究数字应该怎样理解？</h2></div><p>以下是公开统计字段的解释，并非对项目经营表现的保证。</p></div>
<dl class="catalog-glossary-v2">
<div><dt>项目案例数量</dt><dd>当前分类内去重后的公开挂牌样本数，不代表整个市场的项目总量。</dd></div>
<div><dt>营收与利润中位数</dt><dd>对可用挂牌披露字段进行汇总，不能视为独立审计或个人可获得的收入。</dd></div>
<div><dt>细分领域分布</dt><dd>根据来源中的业务分类整理，用于查看样本覆盖范围，不用于推断细分领域盈利水平。</dd></div>
<div><dt>匿名项目摘要</dt><dd>只展示可公开的中文摘要和金额区间；展示数量可能少于分类样本总数。</dd></div>
</dl>
</section>
<section class="catalog-compare-v2" id="category-comparison" aria-labelledby="compare-title">
<div class="section-title-v2">
<div><span>公开统计横向对照</span><h2 id="compare-title">六类商业项目，一张表看清差别</h2></div>
<p>保持原有分类顺序，不按营收、利润或所谓机会价值排序。</p>
</div>
<div class="compare-scroll-v2" role="region" aria-label="商业项目分类公开数据对照表，可横向滚动" tabindex="0">
<table class="compare-table-v2">
<caption class="sr-only">商业项目分类统计，仅代表被观察到的挂牌披露样本</caption>
<thead><tr><th scope="col">研究分类</th><th scope="col">项目案例</th><th scope="col">有报价样本</th><th scope="col">月营收中位数</th><th scope="col">月净利润中位数</th><th scope="col">周工时中位数</th><th scope="col">匿名预览</th></tr></thead>
<tbody>{comparison_rows}</tbody>
</table>
</div>
<p class="compare-disclaimer-v2">同一分类内的样本统计不代表整个市场；各分类样本量和披露完整性不同，中位数不可作为收益潜力排名。“—”表示未提供可公开值，不代表零。匿名预览只统计允许公开的案例数量。</p>
</section>
<section class="research-section" id="catalog-categories">
<div class="section-title-v2"><div><span>项目分类</span><h2>商业资产分类</h2></div><p>卡片中的财务数字均为当前样本的中位数，字段来自挂牌方公开披露。</p></div>
<div class="research-grid-v2">{cards}</div>
</section>
<section class="evidence-policy-v2">
<h2>当前证据边界</h2>
<div class="boundary-grid">
<div><span>数据保护</span><strong>原始渠道不公开</strong><p>保留内部溯源与核验记录。</p></div>
<div><span>价格含义</span><strong>挂牌报价</strong><p>不等于最终成交价。</p></div>
<div><span>财务字段</span><strong>挂牌方披露</strong><p>见势未独立审计。</p></div>
<div><span>不可推断</span><strong>适配 / 可复制 / 未来收益</strong><p>当前证据不支持这些结论。</p></div>
</div>
</section>
<section class="secondary-link-v2"><span>趋势评分是另一层数据。</span><a href="/today/">进入趋势信号 →</a></section>
</main>"""
    return shell(
        "项目研究库｜见势",
        body,
        "见势项目研究库：基于公开商业挂牌样本展示不同商业资产类型的样本数量、财务披露和证据边界。",
        "/opportunities/",
    )

def _sample_rows(research):
    rows=[]
    for i,sample in enumerate((research.get("samples") or [])[:6],1):
        rows.append(f"""<tr>
<td><small class="anonymous-row-index-v2">匿名案例 {i:02d}</small><strong>{esc(sample.get("display_name") or "未分类项目")}</strong></td>
<td>{esc(sample.get("monthly_revenue_band") or "未披露")}</td>
<td>{esc(sample.get("monthly_profit_band") or "未披露")}</td>
<td>{esc(sample.get("asking_price_band") or "未披露")}</td>
</tr>""")
    return ''.join(rows) or '<tr><td colspan="4" class="table-empty">当前无可公开的匿名案例摘要。</td></tr>'

def build_concrete_prototype(x, global_disclaimer, all_prototypes=None):
    research=research_for(x)
    metrics=research.get("metrics") or {}
    source=research.get("evidence_source") or {}
    boundaries=research.get("evidence_boundary") or []
    niches=research.get("niche_distribution") or []
    slug=str(x.get("slug") or "").strip()
    sample_count=int(num(research.get("active_sample_count")))
    price_count=research.get("priced_sample_count")
    price_summary=(f"其中 {fmt_int(price_count)} 个包含挂牌报价信息" if price_count is not None else "报价样本数量尚未提供")
    related=[p for p in (all_prototypes or []) if str(p.get("slug") or "")!=slug][:3]
    related_html=''.join(prototype_card(p,True) for p in related)
    niche_html=_public_niche_bars(research)
    case_coverage=_public_case_completeness(research)
    boundary_html=''.join(f'<li>{esc(v)}</li>' for v in boundaries)
    body=f"""<main class="wrap research-detail-v2">
<section class="research-hero-v2">
<a class="breadcrumb-v2" href="/opportunities/">项目研究库 / 返回</a>
<div class="eyebrow">项目研究档案</div>
<h1>{esc(research.get("title") or x.get("title"))}</h1>
<div class="source-line-v2"><span>中文整理</span><span>已对渠道信息与原始记录进行脱敏</span></div>
<p class="research-summary-v2">当前分类包含 {fmt_int(sample_count)} 个去重项目案例；{esc(price_summary)}。本页展示分类统计与匿名摘要，不代表市场总体情况。</p>
</section>
<nav class="research-anchor-nav-v2" aria-label="本页阅读导航">
<a href="#sample-scope">样本规则</a>
<a href="#sample-metrics">统计与分布</a>
<a href="#sample-examples">匿名案例</a>
<a href="#sample-boundary">证据边界</a>
</nav>

<section class="research-kpis-v2">
<div><span>项目案例数量</span><b>{fmt_int(research.get("active_sample_count"))}</b></div>
<div><span>有报价案例</span><b>{fmt_int(research.get("priced_sample_count")) if research.get("priced_sample_count") is not None else "—"}</b></div>
<div><span>月营收中位数</span><b>{_metric(metrics.get("median_monthly_gross_revenue"),"money")}</b><small>挂牌披露</small></div>
<div><span>月净利润中位数</span><b>{_metric(metrics.get("median_monthly_net_profit"),"money")}</b><small>挂牌披露</small></div>
<div><span>利润率中位数</span><b>{_metric(metrics.get("median_profit_margin_pct"),"pct")}</b><small>挂牌披露</small></div>
<div><span>周工时中位数</span><b>{_metric(metrics.get("median_hours_worked_per_week"),"hours")}</b><small>挂牌披露</small></div>
</section>

<section class="detail-section-v2" id="sample-scope">
<div class="section-title-v2"><div><span>统计口径</span><h2>样本纳入规则</h2></div></div>
<div class="scope-box-v2"><p>{esc(research.get("sample_definition") or "—")}</p><dl><dt>统计对象</dt><dd>海外商业项目</dd><dt>统计方式</dt><dd>同一项目去重</dd><dt>公开方式</dt><dd>中文化与脱敏</dd></dl></div>
</section>

<section class="detail-section-v2" id="sample-metrics">
<div class="section-title-v2"><div><span>数据摘要</span><h2>挂牌样本摘要</h2></div><p>中位数用于降低极端样本对观察结果的影响。</p></div>
<div class="distribution-grid-v2">
<div><span>挂牌报价中位数</span><b>{_metric(metrics.get("median_asking_price"),"money")}</b></div>
<div><span>月营收中位数</span><b>{_metric(metrics.get("median_monthly_gross_revenue"),"money")}</b></div>
<div><span>月净利润中位数</span><b>{_metric(metrics.get("median_monthly_net_profit"),"money")}</b></div>
<div><span>利润率中位数</span><b>{_metric(metrics.get("median_profit_margin_pct"),"pct")}</b></div>
<div><span>周工时中位数</span><b>{_metric(metrics.get("median_hours_worked_per_week"),"hours")}</b></div>
</div>
<div class="taxonomy-v2"><div class="taxonomy-label"><strong>业务领域分布</strong><small>分类中的前 8 项公开标签</small></div><div>{niche_html}<p class="niche-disclaimer-v2">覆盖数量以当前分类的去重样本数为基准；同一项目可能涉及多个领域，因此各项数量不可相加，也不代表市场规模或盈利能力。</p></div></div>
<p class="data-freshness-v2">数据时效：此页面是站点构建时读取的公开研究数据快照；当前公开研究接口未提供可展示的来源更新时间，因此不把构建时间视为资料更新日期。缺失指标以“—”表示，不按零处理。</p>
</section>

<section class="detail-section-v2" id="sample-examples">
<div class="section-title-v2"><div><span>中文案例</span><h2>项目案例摘要</h2></div><p>展示 {fmt_int(len(research.get("samples") or []))} 个匿名案例 / 共整理 {fmt_int(research.get("active_sample_count"))} 个；逐条金额以区间呈现。</p></div>
{case_coverage}
<div class="evidence-table-wrap-v2" role="region" aria-label="匿名项目金额区间表，可横向滚动" tabindex="0"><table class="evidence-table-v2">
<thead><tr><th>中文项目案例</th><th>月营收区间</th><th>月净利润区间</th><th>报价区间</th></tr></thead>
<tbody>{_sample_rows(research)}</tbody>
</table></div>
<p class="sample-reading-note-v2"><strong>阅读提示</strong> 匿名案例仅用于展示当前允许公开的样本结构。逐条金额为区间展示；与上方分类中位数口径不同，也不代表实际成交价或经审计财务。</p>
</section>

<section class="evidence-boundary-v2" id="sample-boundary">
<div><span>数据边界</span><h2>证据边界</h2></div>
<ul>{boundary_html}</ul>
</section>

<section class="detail-section-v2 related-v2">
<div class="section-title-v2"><div><span>关联研究</span><h2>其他研究分类</h2></div><a href="/opportunities/">查看全部 →</a></div>
<div class="research-grid-v2 compact-grid">{related_html}</div>
</section>
</main>"""
    return shell(
        f'{esc(research.get("title") or x.get("title"))}｜见势项目研究',
        body,
        f'基于公开商业挂牌数据的{research.get("title") or x.get("title")}研究档案。',
        canonical_path=f"/opportunity/{slug}/",
        robots="noindex,nofollow",
    )


def verdict(item):
    return (
        "当前满足系统设定的多源证据门槛。"
        if item.get("public_ready")
        else "当前尚未满足系统设定的多源证据门槛。"
    )

def decision_label(item):
    return (
        ("多源门槛满足","good")
        if item.get("public_ready")
        else ("证据观察中","watch")
    )

def _signal_row(item, metric_key, metric_label, rank=None):
    rank_html=f'<span class="daily-rank">#{rank}</span>' if rank else ""
    gate="多源门槛满足" if item.get("public_ready") else "证据观察中"
    gate_cls="good" if item.get("public_ready") else "watch"
    return f"""<a class="daily-row" href="/opportunity/{esc(item.get("slug"))}/">
<div class="daily-title">{rank_html}<div><div class="daily-name"><strong>{esc(item.get("title"))}</strong><span class="badge {gate_cls}">{gate}</span></div><small>{fmt_int(item.get("source_count"))} 类来源 · {fmt_int(item.get("evidence_count"))} 条证据</small></div></div>
<div class="daily-change">{esc(change_label(item))}</div>
<div class="daily-metric"><b>{fmt_score(item.get(metric_key))}</b><span>{esc(metric_label)}</span></div>
<div class="daily-evidence"><b>{fmt_int(item.get("evidence_count"))}</b><span>证据记录</span></div>
</a>"""

def build_daily_page(kind, daily):
    cfg={
      "today":("综合信号","综合指标快照","综合指标","overall_score","按当前 OPP_V0.2 指标展示研究对象，不构成项目推荐。"),
      "rising":("热度变化","近期信号变化","趋势热度","heat_score","用于观察信号强弱变化；热度不等于商业价值。"),
      "build":("可执行性指标","执行条件信号","可执行性","build_score","系统内部可执行性指标，仅用于研究比较，不代表实际落地难度。"),
      "content":("传播指标","内容传播信号","内容价值","content_score","系统内部内容传播指标，不代表商业成立或用户应采取行动。"),
    }
    title,heading,metric_label,metric_key,lead=cfg[kind]
    rows=daily.get(kind) or daily.get("today") or []
    ready=daily.get("history_ready") or {}
    history_note = (
      "已形成 7 日历史序列。"
      if ready.get("seven_day") else
      "历史序列仍在积累。"
    )
    body=f"""<main class="wrap daily-page">
<section class="list-hero"><span class="section-kicker">趋势信号</span><h1>{esc(heading)}</h1><p>{esc(lead)}</p>
<div class="history-note">{esc(history_note)}</div></section>
<section class="daily-list">{"".join(_signal_row(x,metric_key,metric_label,i+1) for i,x in enumerate(rows))}</section>
<section class="panel daily-explain"><h2>指标口径</h2>
<p>本页展示的是系统研究指标，不是商业事实本身，也不构成行动建议。商业证据请以公开挂牌样本和来源字段为准。</p></section>
</main>"""
    return shell(f"{title}｜见势",body,lead,f"/{kind}/")

def _legacy_market_table(rows):
    return '<div class="scope-box-v2"><p>商业原始记录保留在内部核验系统，公开页面不展示数据渠道或项目标识。</p></div>'

def _legacy_github_table(rows):
    return '<div class="scope-box-v2"><p>技术项目原始记录保留在内部核验系统，公开页面仅展示汇总研究指标。</p></div>'

def build_detail(data):
    x=data["item"]
    gate="多源证据门槛：满足" if x.get("public_ready") else "多源证据门槛：未满足"
    market=(data.get("evidence") or {}).get("marketplace") or []
    github=(data.get("evidence") or {}).get("github") or []
    slug=str(x.get("slug") or "").strip()
    body=f"""<main class="wrap research-detail-v2">
<section class="research-hero-v2">
<a class="breadcrumb-v2" href="/today/">趋势信号 / 返回</a>
<div class="eyebrow">趋势指标档案</div>
<h1>{esc(x.get("title"))}</h1>
<div class="source-line-v2"><span>{esc(gate)}</span><span>指标版本：OPP_V0.2</span><span>{fmt_int(x.get("source_count"))} 类来源 · {fmt_int(x.get("evidence_count"))} 条证据</span></div>
</section>

<section class="research-kpis-v2 signal-kpis">
<div><span>趋势热度</span><b>{fmt_score(x.get("heat_score"))}</b></div>
<div><span>内容指标</span><b>{fmt_score(x.get("content_score"))}</b></div>
<div><span>可执行性指标</span><b>{fmt_score(x.get("build_score"))}</b></div>
<div><span>商业质量指标</span><b>{fmt_score(x.get("business_score"))}</b></div>
<div><span>综合指标</span><b>{fmt_score(x.get("overall_score"))}</b></div>
<div><span>证据记录</span><b>{fmt_int(x.get("evidence_count"))}</b></div>
</section>

<section class="detail-section-v2">
<div class="section-title-v2"><div><span>商业数据</span><h2>商业样本</h2></div><p>原始项目标识、技术仓库与渠道信息不对外公开。</p></div>
{_legacy_market_table(market)}
</section>

<section class="detail-section-v2">
<div class="section-title-v2"><div><span>技术指标</span><h2>技术样本</h2></div><p>技术热度只代表观察信号，不直接证明商业成立。</p></div>
{_legacy_github_table(github)}
</section>

<section class="evidence-boundary-v2">
<div><span>解释边界</span><h2>解释边界</h2></div>
<ul>
<li>OPP_V0.2 为见势内部研究指标，不是外部来源事实。</li>
<li>系统分数不能替代商业尽调，也不能推导收益。</li>
<li>公开商业字段以来源披露为准；挂牌报价不等于成交价。</li>
<li>技术样本与商业样本分别呈现，不用技术热度替代商业证据。</li>
</ul>
</section>
{account_action_block(x)}
</main>"""
    return shell(
        f'{esc(x.get("title"))}｜见势趋势信号',
        body,
        "见势趋势信号档案：展示系统指标及其技术、商业证据记录。",
        canonical_path=f"/opportunity/{slug}/" if slug else "/",
    )


def newsletter_block():
    endpoint=esc(NEWSLETTER_API)
    return f"""<section class="newsletter research-newsletter"><div class="wrap newsletter-inner">
<div class="newsletter-copy"><span class="section-kicker">研究更新</span><h2>订阅见势研究更新</h2>
<p>无需注册。提交邮箱后需完成确认；只有确认成功后才会发送更新，可随时退订。</p></div>
<form class="newsletter-form" data-newsletter-form data-endpoint="{endpoint}">
<label class="sr-only" for="newsletter-email">邮箱</label>
<input id="newsletter-email" name="email" type="email" autocomplete="email" inputmode="email" maxlength="254" placeholder="name@example.com" required>
<input class="hp-field" name="company" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">
<button type="submit">订阅研究更新</button>
<p class="newsletter-consent">提交后将先发送确认邮件；未确认前不会进入正式发送名单。<a href="/privacy/">隐私说明</a></p>
<p class="newsletter-status" data-newsletter-status role="status" aria-live="polite"></p>
</form></div></section>"""


# Cloudflare Pages runs a second build of the same GitHub revision. Unlike
# GitHub's trusted scheduled/static workflow it may not have JIANSHI_API_URL.
# Avoid replacing the audited, checked-in PUBLIC snapshot with offline fixtures.
# This is purely a local artifact reuse step; never calls a new data source.
PUBLISHED_RESEARCH_SLUGS=(
    "vertical-industry-saas","amazon-fba-niche-brand","digital-product-business",
    "affiliate-content-site","amazon-kdp-publishing","agency-business",
)

def _preserve_cloudflare_public_snapshot():
    if API or os.getenv("CF_PAGES")!="1" or os.getenv("CF_PAGES_BRANCH","main")!="main":
        return False
    import re
    root=REPO_ROOT
    released=DIST
    source=root/"dist"
    files=[
        released/"index.html",
        released/"_headers",
        released/"_redirects",
        released/"research"/"index.html",
        source/"opportunities"/"index.html",
    ]
    for slug in PUBLISHED_RESEARCH_SLUGS:
        files.extend((
            released/"research"/slug/"index.html",
            source/"opportunity"/slug/"index.html",
        ))
    missing=[str(path.relative_to(root)) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError("Missing audited committed Pages snapshot: "+", ".join(missing))
    home=(released/"index.html").read_text(encoding="utf-8")
    index=(released/"research"/"index.html").read_text(encoding="utf-8")
    src_index=(source/"opportunities"/"index.html").read_text(encoding="utf-8")
    # P4.47: Cloudflare Pages uses the committed, audited static snapshot.
    # The former 3D ring was intentionally removed from the single JIANSHI2
    # homepage in P4.45. Requiring it here blocked every later Pages deploy.
    # Fail closed on the NEW public contract instead of resurrecting old UI.
    required_home = ('id="j2"', 'id="j2-opportunities"',
                     'id="j2-solutions"', 'id="j2-marketplace"',
                     'id="j2-talent"', 'id="j2-academy"',
                     'href="/research/"', 'href="/projects/"')
    banned_legacy = ('id="ring"', 'id="lb"', 'id="archive"',
                     'id="recommendations"', 'id="splash"')
    if (any(marker not in home for marker in required_home)
            or any(marker in home for marker in banned_legacy)
            or home.count("data:image/webp;base64,") != 1):
        raise RuntimeError("Committed single JIANSHI2 homepage contract missing")
    if ('id="category-comparison"' not in index
            or 'id="category-comparison"' not in src_index
            or 'noindex,follow' not in index):
        raise RuntimeError("Committed public comparison contract missing")
    if "Cache-Control: no-store" not in (released/"_headers").read_text(encoding="utf-8"):
        raise RuntimeError("Committed public cache policy missing")
    if "/config/*" not in (released/"_redirects").read_text(encoding="utf-8"):
        raise RuntimeError("Committed public path protections missing")
    count_re=re.compile(r"当前分类包含\s*([\d,]+)\s*个去重项目案例")
    for slug in PUBLISHED_RESEARCH_SLUGS:
        page=(released/"research"/slug/"index.html").read_text(encoding="utf-8")
        mirror=(source/"opportunity"/slug/"index.html").read_text(encoding="utf-8")
        n=count_re.search(page)
        m=count_re.search(mirror)
        if (not n or not m or n.group(1)!=m.group(1)
                or "noindex,nofollow" not in page
                or 'id="sample-metrics"' not in page):
            raise RuntimeError("Published research snapshot mismatch: "+slug)
    print(json.dumps({
        "status":"PASS",
        "api":"audited_committed_public_snapshot",
        "pages":len(PUBLISHED_RESEARCH_SLUGS),
        "outputs":["web/dist","dist","public","repo-root-runtime"],
        "no_new_data_requests":True,
    },ensure_ascii=False))
    return True


def main():
    global AUTH_ENABLED
    if _preserve_cloudflare_public_snapshot():
        return
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copy2(STATIC/"styles.css",DIST/"styles.css")
    shutil.copy2(STATIC/"search.js",DIST/"search.js")
    shutil.copy2(STATIC/"account.js",DIST/"account.js")
    shutil.copy2(STATIC/"analytics.js",DIST/"analytics.js")
    shutil.copy2(STATIC/"_headers",DIST/"_headers")
    shutil.copy2(STATIC/"_redirects",DIST/"_redirects")
    prototype_data={}
    prototypes=[]
    prototype_disclaimer=""
    if CONCRETE_PROTOTYPES.exists():
        prototype_data=json.loads(CONCRETE_PROTOTYPES.read_text(encoding="utf-8"))
        prototypes=prototype_data.get("opportunities") or []
        prototype_disclaimer=prototype_data.get("disclaimer") or ""

    home=api_get("home")
    remote_auth_enabled=bool((home.get("features") or {}).get("account_auth"))
    # Local fixture builds may exercise the enabled UI with the env flag alone.
    # Real API builds require BOTH env intent and the production DB gate.
    AUTH_ENABLED=AUTH_REQUESTED and (remote_auth_enabled if API else True)
    daily=api_get("daily")
    catalog=api_get("catalog").get("items",[])
    (DIST/"index.html").write_text(build_home(home,daily,prototypes),encoding="utf-8")

    opportunities_out=DIST/"opportunities"
    opportunities_out.mkdir(parents=True,exist_ok=True)
    (opportunities_out/"index.html").write_text(build_opportunities_page(catalog,prototypes),encoding="utf-8")

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

    prototype_count=0
    for prototype in prototypes:
        prototype_slug=str(prototype.get("slug") or "").strip()
        if not prototype_slug:
            continue
        prototype_out=DIST/"opportunity"/prototype_slug
        prototype_out.mkdir(parents=True,exist_ok=True)
        (prototype_out/"index.html").write_text(
            build_concrete_prototype(prototype,prototype_disclaimer,prototypes),
            encoding="utf-8",
        )
        prototype_count+=1

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

    urls=["/","/opportunities/","/today/","/rising/","/build/","/content/","/privacy/"]+[f"/opportunity/{x['slug']}/" for x in search]
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
    for name in ("index.html","404.html","styles.css","search.js","account.js","analytics.js","search-index.json","sitemap.xml","robots.txt","_headers","_redirects"):
        shutil.copy2(DIST/name, REPO_ROOT/name)
    for dirname in ("opportunity","opportunities","today","rising","build","content","privacy","account"):
        target=REPO_ROOT/dirname
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(DIST/dirname,target)

    print(json.dumps({
        "status":"PASS",
        "api":"live" if API else "fixture",
        "pages":7+len(search)+prototype_count,
        "opportunities":len(catalog),
        "prototype_opportunities":prototype_count,
        "outputs":["web/dist","dist","public","repo-root-runtime"]
    },ensure_ascii=False))

if __name__=="__main__": main()
