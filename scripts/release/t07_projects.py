#!/usr/bin/env python3
"""T07: deterministic, offline, public-only static project pages.

The ONLY project data input is data/projects.json. No runtime API/fetch or third-party
script is emitted. Invoke this after the existing P4.12 release has generated its
legacy pages; T07 replaces only web/dist/projects.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
from t08_project_selection import projects as reviewed_or_preview_projects

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "projects.json"
SITE = "https://jianshi-bua.pages.dev"
SCORE_LABELS = {
    "build_difficulty": "开发难度（越易越高）",
    "channel_reach_cn": "中国开发者获客可达性",
    "payment_compliance": "支付与平台合规",
    "competition": "竞争空间",
    "time_to_mvp": "30天最小产品可行性",
}
DISCLAIMER = "数据为第三方公开信息，非财务审计，不构成收入承诺。"
AUDIT_NOTE = "收入来自海外收入公示网站 TrustMRR 的支付记录，见势未逐笔核对；安装量和评价数不能证明付费人数。"


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def fmt_money(value: object, currency: str = "USD") -> str:
    if value is None or value == "":
        return "未公开"
    amount = float(value)
    digits = f"{amount:,.2f}" if amount != int(amount) else f"{amount:,.0f}"
    symbol = "$" if currency == "USD" else f"{currency} "
    return symbol + digits


def value_or_unknown(value: object, suffix: str = "") -> str:
    if value is None or value == "":
        return "未公开"
    return str(value) + suffix


def date_age(iso_date: str) -> int:
    return (date.today() - date.fromisoformat(iso_date)).days


def chinese_date(value: object) -> str:
    try:
        raw = str(value)
        if "T" in raw:
            dt = datetime.fromisoformat(raw.replace("Z","+00:00"))
            if dt.tzinfo:
                dt = dt.astimezone(timezone(timedelta(hours=8)))
                return f"{dt.year}年{dt.month}月{dt.day}日 {dt:%H:%M}（北京时间）"
            return f"{dt.year}年{dt.month}月{dt.day}日"
        d = date.fromisoformat(raw)
        return f"{d.year}年{d.month}月{d.day}日"
    except (ValueError,TypeError):
        return "未公开"


def source_display(source: dict) -> str:
    """Labels are public; never display private audit or source-review notes."""
    u = urlparse(str(source.get("url","")))
    host = u.hostname or ""
    if "trustmrr.com" in host:
        return ("海外收入公示网站 TrustMRR：同一网站的收入明细（不是独立第二份证明）"
                if u.path.endswith(".md") else "海外收入公示网站 TrustMRR：收入资料")
    if "indiepage" in host:
        return "IndiePage：收入资料（经营有关联，不是独立付款证明）"
    if "producthunt.com" in host: return "Product Hunt：产品评价和关注"
    if "trustpilot.com" in host: return "Trustpilot：用户评价（不等于付费人数）"
    if "chromewebstore.google.com" in host: return "Chrome 应用商店：安装量（不等于付费人数）"
    if "apps.apple.com" in host: return "苹果应用商店：用户评分（不等于付费人数）"
    if "play.google.com" in host: return "Google Play：下载量区间（不等于付费人数）"
    if "github.com" in host: return "GitHub：代码仓库关注数（不等于付费人数）"
    return "查看公开资料（可能来自项目方自述，未独立确认）"

SIGNALS={"ahrefs_domain_rating":"网站搜索评分估算",
"product_hunt_review_count":"产品评价条数","product_hunt_followers":"关注者人数",
"trustpilot_review_count":"用户评价条数","github_stars":"代码仓库关注数",
"github_related_repo_stars":"关联代码库关注数（不是付费人数）",
"app_store_rating_count":"应用商店评分数","chrome_users":"商店显示用户数",
"chrome_users_lower_bound":"商店用户数下限",
"google_play_downloads_lower_bound":"应用下载量下限"}
def signal_display(value: object) -> str:
    return SIGNALS.get(str(value), "公开用户增长信号（不等于付费人数）")


def public_copy(value: object) -> str:
    """Show readable Chinese without changing stored product/source facts."""
    output = "" if value is None else str(value)
    for old,new in (
        ("Codex","编程助手"),("MRR","每月订阅收入"),
        ("KYC","实名或企业认证"),("API","接口"),
        ("OAuth","授权登录"),("OCR","图片文字识别"),
        ("TTS","文字转语音"),("CLI","命令行工具"),
        ("SEO","搜索排名"),("MVP","最简可用产品"),
        ("demo","演示版"),("SaaS","在线订阅软件"),
    ):
        output = re.sub(r"(?<![a-zA-Z])" + re.escape(old) + r"(?![a-zA-Z])",new,output)
    return output


def load_projects() -> list[dict]:
    projects = reviewed_or_preview_projects()
    if not isinstance(projects, list) or not projects:
        raise ValueError("data/projects.json must be a non-empty list")
    ids = set()
    for project in projects:
        pid = project.get("id")
        if not isinstance(pid, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", pid):
            raise ValueError(f"Invalid project id: {pid!r}")
        if pid in ids:
            raise ValueError(f"Duplicate project id: {pid}")
        ids.add(pid)
        revenue = project["revenue"]
        for key in ("mrr", "last_30d", "all_time", "currency", "as_of", "verified_by"):
            if key not in revenue:
                raise ValueError(f"Missing revenue.{key}: {pid}")
        for key in ("founded_date", "growth_30d", "customers", "flags", "one_liner_cn", "category",
                    "team_size", "evidence_level", "total_score", "verdict", "sources",
                    "business_model", "price_point", "acquisition_channels", "cn_angle", "risks", "risk_public"):
            if key not in project:
                raise ValueError(f"Missing {key}: {pid}")
        public_risk = project["risk_public"]
        if not isinstance(public_risk,str) or not public_risk.strip() or len(public_risk)>40:
            raise ValueError(f"Invalid public risk for {pid}")
        if set(project.get("scores", {})) != set(SCORE_LABELS) or set(project.get("score_reasons", {})) != set(SCORE_LABELS):
            raise ValueError(f"Invalid five score dimensions: {pid}")
        if sum(project["scores"].values()) != project["total_score"]:
            raise ValueError(f"Incorrect total score: {pid}")
        for source in project["sources"]:
            parsed = urlparse(str(source.get("url", "")))
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError(f"Invalid public source URL: {pid}")
    return projects


CSS = """
:root{color-scheme:light;--page:#f6f7fb;--surface:#fff;--ink:#17243a;--muted:#64748b;--line:#dfe6ee;--accent:#3856a5;--deep:#1b3376;--mint:#087b63;--amber:#98621b}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font:15px/1.7 system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:var(--ink);background:var(--page);overflow-wrap:anywhere}
a{color:var(--accent)}a:hover{text-decoration-color:var(--deep)}
a:focus-visible,select:focus-visible{outline:3px solid #7095e8;outline-offset:3px}
.wrap{max-width:1160px;margin:auto;padding-inline:clamp(18px,4vw,46px)}
.site-head{background:var(--surface);border-bottom:1px solid var(--line)}
.site-head .wrap{display:flex;justify-content:space-between;align-items:center;gap:18px;min-height:76px}
.logo{text-decoration:none;font-size:23px;font-weight:850;letter-spacing:-.08em;color:var(--ink);white-space:nowrap}
.logo small{font-size:10px;font-weight:700;letter-spacing:.16em;display:block;color:var(--muted);line-height:1}
nav{display:flex;align-items:center;gap:clamp(9px,2vw,23px);flex-wrap:wrap;font-size:13px}
nav a{text-decoration:none;color:var(--muted);font-weight:650}
nav a[aria-current=page],nav a:hover{color:var(--deep)}
.hero{padding-block:clamp(36px,6vw,76px) 30px}
.kicker{font-size:12px;font-weight:800;color:var(--accent);letter-spacing:.13em}
h1{font-size:clamp(31px,4.1vw,55px);line-height:1.2;letter-spacing:-.045em;margin:12px 0 16px;font-weight:790}
h2{font-size:clamp(21px,2.6vw,28px);letter-spacing:-.03em;line-height:1.35;margin:0 0 14px}
h3{font-size:18px;line-height:1.35;margin:0 0 6px}
p{margin:0 0 12px}.lead{font-size:clamp(15px,1.6vw,18px);color:#4b5871;max-width:760px}
.meta-line{color:var(--muted);font-size:13px}
.controls{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;align-items:end;margin:16px 0 16px;padding:18px;border:1px solid var(--line);border-radius:17px;background:var(--surface)}
.control{display:grid;gap:5px;min-width:0}.control label{font-size:12px;font-weight:750;color:var(--muted)}
select{appearance:auto;width:100%;padding:10px 11px;min-height:43px;background:#fff;color:var(--ink);border:1px solid #cbd5e1;border-radius:9px;font-size:14px}
.resultcount{font-size:13px;color:var(--muted);margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;padding-bottom:64px}
.project{min-width:0;display:flex;flex-direction:column;border:1px solid var(--line);border-radius:18px;background:var(--surface);padding:clamp(17px,2.5vw,25px);box-shadow:0 6px 21px rgba(25,44,82,.035)}
.project:hover{border-color:#abbcdb;box-shadow:0 9px 26px rgba(25,44,82,.08)}
.phead{display:flex;justify-content:space-between;gap:12px;align-items:start;margin-bottom:13px}
.phead h2{font-size:22px;margin:0}.phead a{color:var(--ink);text-decoration:none}.phead a:hover{color:var(--accent)}
.category{display:inline-block;color:#526785;font-size:12px;font-weight:750;margin-bottom:8px}
.pintro{color:#52627c;line-height:1.65;min-height:48px}
.tags{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin:9px 0}
.tag{font-size:11px;line-height:1.5;border-radius:7px;padding:4px 7px;background:#eef2ff;color:#344d85;font-weight:750}
.tag.verdict-good{color:#08694f;background:#ddf8eb}.tag.verdict-bad{color:#9b3447;background:#ffebef}
.tag.flag{background:#fff3df;color:#8b571b;border:1px solid #f6d49f}
.metrics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:17px 0;margin-top:auto}
.metric small,.fact small{color:var(--muted);display:block;font-size:12px;margin-bottom:3px}
.metric strong{display:block;font-size:clamp(21px,2.35vw,27px);line-height:1.3;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.cardfoot{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:center;padding-top:13px;font-size:12px;color:var(--muted)}
.cardfoot strong{color:var(--accent)}.cardfoot a{font-weight:800;text-decoration:none}
.panel{border:1px solid var(--line);border-radius:16px;padding:clamp(18px,3vw,30px);background:#fff;margin:18px 0}
.back{font-size:13px;font-weight:750;text-decoration:none}
.detail-lead{max-width:800px}
.money-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.money-box{background:#f4f7fc;border:1px solid #e5ebf6;border-radius:12px;padding:18px;min-width:0}
.money-box small{display:block;color:var(--muted);font-size:12px;font-weight:650}
.money-box strong{display:block;margin-top:7px;font-size:clamp(22px,3vw,33px);line-height:1.2;letter-spacing:-.035em;font-variant-numeric:tabular-nums}
.facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}
.fact{padding:12px 0;border-bottom:1px solid var(--line);min-width:0}.fact b{font-size:15px}
.body-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(0,1fr);gap:18px;align-items:start}
.scores{display:grid;gap:0}.scoreline{padding:14px 0;border-top:1px solid var(--line)}
.scoreline:first-child{border-top:0}.scorehead{display:flex;justify-content:space-between;align-items:center;gap:10px}
.scorehead b{font-size:15px}.scorehead strong{color:var(--accent);font-variant-numeric:tabular-nums}
.bar{height:7px;border-radius:999px;background:#e8edf6;overflow:hidden;margin:8px 0}.bar i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#6480ce,#3856a5)}
.reason{color:#58677d;font-size:13px;margin:0}
.textlist{margin:0;padding-left:19px}.textlist li{margin:8px 0}
.sources{display:grid;gap:12px}
.source{padding:15px;border:1px solid var(--line);border-radius:10px;min-width:0}
.source a{font-weight:750;overflow-wrap:anywhere}
.source small{display:block;color:var(--muted);font-size:12px;margin-top:4px}
.traction{list-style:none;padding:0;margin:0}.traction li{padding:10px 0;border-bottom:1px solid var(--line)}
.traction b{font-variant-numeric:tabular-nums}
.disclaimer{background:#eef1f8;padding:16px 0;color:#52617a;font-size:12px;line-height:1.75;margin-top:30px}
.disclaimer p{margin:0}
.hero-cta{display:inline-flex;align-items:center;min-height:44px;margin:7px 0 14px;padding:10px 19px;border-radius:11px;background:#3153a1;color:white;text-decoration:none;font-size:14px;font-weight:800}
.hero-cta:hover{background:#273c7c;color:white}
.p-risk{color:#805122;font-size:13px;line-height:1.6;margin:10px 0}
.empty{padding:28px;background:#fff;border-radius:12px;color:var(--muted)}
[hidden]{display:none!important}
@media(max-width:800px){.controls{grid-template-columns:repeat(2,minmax(0,1fr))}.body-grid{grid-template-columns:1fr}.money-grid{grid-template-columns:1fr 1fr}}
@media(max-width:540px){.site-head .wrap{padding-block:14px;align-items:start;flex-direction:column;gap:12px}.site-head nav{gap:12px}.hero{padding-block:36px 22px}.controls{padding:13px;gap:9px}.cards{grid-template-columns:1fr}.pintro{min-height:0}.money-grid{grid-template-columns:1fr}.facts{grid-template-columns:repeat(2,minmax(0,1fr))}.metric strong{font-size:23px}.panel{margin:13px 0}.scorehead b{font-size:14px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

LIST_JS = """
(() => {
  'use strict';
  const selects = Object.fromEntries(['category','verdict','evidence_level','sort'].map(k => [k,document.getElementById(k)]));
  const holder = document.getElementById('project-list');
  const cards = Array.from(holder.querySelectorAll('[data-project]'));
  const params = new URLSearchParams(location.search);
  const allowedSort = ['total_score','mrr','last_30d'];
  for (const k of ['category','verdict','evidence_level']) {
    if (Array.from(selects[k].options).some(opt => opt.value === params.get(k))) selects[k].value = params.get(k);
  }
  if (allowedSort.includes(params.get('sort'))) selects.sort.value = params.get('sort');
  const display = () => {
    const [category,verdict,evidence,sort] = ['category','verdict','evidence_level','sort'].map(k=>selects[k].value);
    const qs = new URLSearchParams();
    if (category) qs.set('category',category);
    if (verdict) qs.set('verdict',verdict);
    if (evidence) qs.set('evidence_level',evidence);
    if (sort !== 'total_score') qs.set('sort',sort);
    history.replaceState(null,'',location.pathname + (qs.size ? '?' + qs.toString() : ''));
    const field = ({total_score:'score',mrr:'mrr',last_30d:'last30'})[sort];
    cards.sort((a,b) => {
      const av = a.dataset[field] === '' ? -Infinity : Number(a.dataset[field]);
      const bv = b.dataset[field] === '' ? -Infinity : Number(b.dataset[field]);
      return bv-av || a.dataset.name.localeCompare(b.dataset.name,'zh-CN');
    });
    let visible=0;
    for (const el of cards) {
      const pass = (!category || el.dataset.category===category)
        && (!verdict || el.dataset.verdict===verdict)
        && (!evidence || el.dataset.evidence===evidence);
      el.hidden = !pass;
      if (pass) visible++;
      holder.appendChild(el);
    }
    document.getElementById('result-count').textContent = '当前显示 '+visible+' / '+cards.length+' 个项目';
    document.getElementById('empty-message').hidden = visible !== 0;
  };
  Object.values(selects).forEach(el => el.addEventListener('change',display));
  window.addEventListener('popstate', () => { location.reload(); });
  display();
})();
"""


def shell(title: str, description: str, path: str, body: str, *, listing=False) -> str:
    nav = ('<a href="/">首页</a><a aria-current="page" href="/projects/">项目库</a>'
           '<a href="/sources/">数据来源</a><a href="/#subscribe">加入候选名单</a>')
    js = '<script src="/projects/t07.js" defer></script>' if listing else ""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="canonical" href="{SITE}{esc(path)}">
<title>{esc(title)}｜见势</title>
<link rel="stylesheet" href="/projects/t07.css">
</head><body>
<header class="site-head"><div class="wrap"><a class="logo" href="/">见势</a><nav aria-label="主导航">{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer class="disclaimer"><div class="wrap"><p>{AUDIT_NOTE} {DISCLAIMER}</p></div></footer>
{js}</body></html>
"""


def badge(text: object, extra: str = "") -> str:
    return f'<span class="tag {esc(extra)}">{esc(text)}</span>'


def tags(project: dict) -> str:
    parts = [badge(project["verdict"], "verdict-good" if project["verdict"] == "推荐" else "verdict-bad" if project["verdict"] == "不推荐" else "")]
    parts.append(badge("提醒："+project["risk_public"], "flag"))
    return '<div class="tags">' + "".join(parts) + "</div>"


def project_card(project: dict) -> str:
    revenue = project["revenue"]
    pid = esc(project["id"])
    mrr = "" if revenue["mrr"] is None else str(revenue["mrr"])
    return f"""<article class="project" data-project data-name="{esc(project['name'])}" data-category="{esc(project['category'])}"
data-verdict="{esc(project['verdict'])}" data-evidence="{esc(project['evidence_level'])}"
data-score="{esc(project['total_score'])}" data-mrr="{esc(mrr)}" data-last30="{esc(revenue['last_30d'])}">
<div class="category">{esc(public_copy(project['category']))}</div>
<div class="phead"><h2><a href="/projects/{pid}/">{esc(project['name'])}</a></h2>{badge(str(project['total_score'])+'/25')}</div>
<p class="pintro">{esc(public_copy(project['one_liner_cn']))}</p>
<p class="p-risk">要留意：{esc(project["risk_public"])}</p>
<div class="metrics"><div class="metric"><small>近 30 天收入</small><strong>{esc(fmt_money(revenue['last_30d'],revenue['currency']))}</strong></div>
<div class="metric"><small>每月订阅收入</small><strong>{esc(fmt_money(revenue['mrr'],revenue['currency']))}</strong></div></div>
<div class="cardfoot"><span>{esc(value_or_unknown(project['team_size'], ' 人'))}团队 · 收入有公开资料</span>
<a href="/projects/{pid}/">查看项目详情 →</a></div></article>"""


def build_list(projects: list[dict]) -> str:
    categories = sorted({p["category"] for p in projects})
    verdicts = sorted({p["verdict"] for p in projects}, key=lambda v: ["推荐","可做","不推荐"].index(v) if v in ["推荐","可做","不推荐"] else 99)
    levels = sorted({p["evidence_level"] for p in projects})
    def sel(key, label, options):
        return (f'<div class="control"><label for="{key}">{esc(label)}</label><select id="{key}" name="{key}">'
                + '<option value="">全部</option>'
                + "".join(f'<option value="{esc(v)}">{esc({"A":"高","A-":"中高","B":"中","T":"参考"}.get(v,v) if key=="evidence_level" else public_copy(v))}</option>' for v in options)
                + "</select></div>")
    controls = (sel("category", "类别", categories)
                + sel("verdict", "结论", verdicts)
                + sel("evidence_level", "证据等级", levels)
                + '<div class="control"><label for="sort">排序方式</label><select id="sort" name="sort">'
                + '<option value="total_score">总分优先</option><option value="mrr">每月订阅收入优先</option>'
                + '<option value="last_30d">近30天收入优先</option></select></div>')
    as_of = max(p["revenue"]["as_of"] for p in projects)
    body = f"""<section class="hero"><div class="kicker">项目库 · 真实商业案例</div>
<h1>项目库 · 看见真实收入，找到可做方向。</h1>
<p class="lead">收入信息来自海外收入公示网站 TrustMRR，见势没有逐笔核对，也无法确认独立付费客户数。点开项目能查看来源、打分理由与风险。</p>
<a class="hero-cta" href="#project-list">看推荐项目 →</a><p class="meta-line">数据核对日期：<time datetime="{esc(as_of)}">{esc(chinese_date(as_of))}</time> · {len(projects)} 个公开项目 · 评分为研究参考，不是收益承诺</p></section>
<section aria-label="项目筛选和排序"><div class="controls">{controls}</div>
<p id="result-count" class="resultcount" role="status" aria-live="polite">{len(projects)} 个项目</p></section>
<section id="project-list" class="cards" aria-label="项目列表">{"".join(project_card(p) for p in projects)}</section>
<p id="empty-message" class="empty" hidden>没有符合筛选条件的项目，请调整筛选项。</p>"""
    return shell("项目库", f"{len(projects)}条个公开商业项目，含项目收入、评分与来源", "/projects/", body, listing=True)


def text_field(label: str, value: object) -> str:
    return f'<div class="fact"><small>{esc(label)}</small><b>{esc(value_or_unknown(value))}</b></div>'


def detail(project: dict) -> str:
    rev = project["revenue"]
    currency = rev["currency"]
    money = lambda key: fmt_money(rev.get(key), currency)
    income = "".join(f'<div class="money-box"><small>{name}</small><strong>{esc(money(key))}</strong></div>'
                     for key,name in (("mrr","每月订阅收入"),("last_30d","近30天收入"),("all_time","历史累计收入")))
    grown = project["growth_30d"]
    grown_txt = "未公开" if grown is None else f"{grown:+g}%"
    income_facts = (text_field("币种",currency) + text_field("数据日期",chinese_date(rev["as_of"]))
                    + text_field("支付平台验证方",rev["verified_by"])
                    + text_field("成立日期",chinese_date(project["founded_date"]))
                    + text_field("近30天增长率",grown_txt)
                    + text_field("付费客户数",project.get("customers"))
                    + text_field("团队规模",value_or_unknown(project["team_size"]," 人"))
                    + text_field("来源可信度",{"A":"高","A-":"中高","B":"中","T":"参考"}.get(project["evidence_level"],"未公开"))
                    + text_field("评分总计",str(project["total_score"])+"/25"))
    scores = []
    for key, name in SCORE_LABELS.items():
        value = project["scores"][key]
        reason = project["score_reasons"][key]
        scores.append(f'<div class="scoreline"><div class="scorehead"><b>{esc(name)}</b><strong>{esc(value)}/5</strong></div>'
                      f'<div class="bar" aria-hidden="true"><i style="width:{int(value)*20}%"></i></div>'
                      f'<p class="reason">{esc(public_copy(value_or_unknown(reason)))}</p></div>')
    ch = project.get("acquisition_channels")
    channels = "、".join(map(str,ch)) if isinstance(ch,list) else value_or_unknown(ch)
    signals = project.get("traction") or []
    traction = '<ul class="traction">' + "".join(
        f'<li>{esc(signal_display(t.get("type")))}：<b>{esc(value_or_unknown(t.get("value")))}</b>'
        + (f' · <a rel="noopener noreferrer" href="{esc(t["url"])}" target="_blank">查看来源 ↗</a>' if t.get("url") else "")+"</li>"
        for t in signals) + "</ul>" if signals else "<p>未公开</p>"
    source_list = '<div class="sources">' + "".join(
        f'<div class="source">{badge("收入来源" if s.get("level") in ("A","A-") else "其他线索")} '
        f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(source_display(s))} ↗</a>'
        f'<small>核对日期：{esc(chinese_date(s.get("checked_at")))}</small></div>'
        for s in project["sources"]) + "</div>"
    sale = project.get("for_sale") or {}
    sale_text = ("是 · 要价："+fmt_money(sale.get("asking_price"),currency)
                 +" · 倍数："+value_or_unknown(sale.get("multiple"))) if sale.get("listed") else "未公开在售"
    body = f"""<section class="hero"><a class="back" href="/projects/">← 返回项目库</a>
<div class="kicker" style="margin-top:18px">{esc(public_copy(project["category"]))} · 公开项目档案</div>
<h1>{esc(project["name"])}</h1>
<p class="lead detail-lead">{esc(project["one_liner_cn"])}</p>
{tags(project)}<p><a class="hero-cta" href="{esc(project["url"])}" rel="noopener noreferrer" target="_blank">打开官网 ↗</a></p></section>
<section class="panel" aria-labelledby="income-heading"><h2 id="income-heading">收入数据</h2>
<div class="money-grid">{income}</div><div class="facts">{income_facts}</div>
<p class="meta-line" style="margin-top:16px">收入记录日期：{esc(chinese_date(rev.get("source_last_synced")))}</p>
<p class="meta-line">{AUDIT_NOTE}</p></section>
<div class="body-grid"><div>
<section class="panel" aria-labelledby="score-heading"><h2 id="score-heading">五维评分 · {esc(project["total_score"])}/25</h2>
<div class="scores">{"".join(scores)}</div></section>
<section class="panel"><h2>面向中国开发者的切入建议</h2><p>{badge("推测")} {esc(public_copy(project["cn_angle"]))}</p>
<h3>已知风险与注意事项</h3><p>{esc(public_copy(value_or_unknown(project.get("risks"))))}</p>
<p class="p-risk">{esc(project["risk_public"])}</p></section>
<section class="panel"><h2>全部公开来源与证据等级</h2>{source_list}</section>
</div><aside>
<section class="panel"><h2>商业模式</h2>
<div class="facts" style="grid-template-columns:1fr">{text_field("收费模式",public_copy(project.get("business_model")))}
{text_field("价格与套餐",public_copy(project.get("price_point")))}
{text_field("营销与获客渠道",public_copy(channels))}
{text_field("是否在售、要价、倍数",sale_text)}</div></section>
<section class="panel"><h2>公开用户增长信号</h2>{traction}
<p class="meta-line">用户增长数据不等于付费人数，也不能单独证明收入。</p></section>
</aside></div>"""
    return shell(str(project["name"]),"公开收入、评分理由及来源："+str(project["one_liner_cn"]),f"/projects/{project['id']}/",body)


def build(dest: Path | None = None) -> dict:
    projects = load_projects()
    outdir = (dest if dest is not None else ROOT / "web" / "dist") / "projects"
    # This is a generated subtree: remove all old P4.23 case pages (e.g.
    # carrd/nerdwallet/plausible) rather than co-mingle two data standards.
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "t07.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (outdir / "t07.js").write_text(LIST_JS.strip() + "\n", encoding="utf-8")
    (outdir / "index.html").write_text(build_list(projects), encoding="utf-8")
    for project in projects:
        path = outdir / project["id"]
        path.mkdir()
        (path / "index.html").write_text(detail(project), encoding="utf-8")
    result = {"projects":len(projects),"pages":len(projects)+1,"output":str(outdir),"source":"data/projects.json"}
    print(json.dumps({"t07":result},ensure_ascii=False))
    return result


if __name__ == "__main__":
    build()
