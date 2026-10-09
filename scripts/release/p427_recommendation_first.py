"""P4.27: recommendation-first entrance based only on admitted named evidence.

Company operating evidence supports *research recommendations*. It does not
establish startup reproducibility, costs, acquisition or founder fit. Never
auto-label a company as a proven startup opportunity.
"""
from __future__ import annotations

from html import escape

from p426_evidence_digest import derive_digest

RESEARCH_CHOICES = {
    "carrd": {
        "name": "轻量建站工具",
        "priority": 1,
        "headline": "先研究：为特定人群解决一个建站问题",
        "reason": "公开访谈披露过历史经常性收入，说明这个经营方向有可归属的历史商业案例。",
        "fit": "适合有网页产品能力、愿意持续迭代与推广的人先研究。",
        "risk": "后来者能否拿到首批付费客户、如何避开同质化竞争，都没有得到验证。",
        "next": "先锁定一个更小的客户群，核实真实购买需求，再决定是否开发。",
        "label": "优先研究 01",
    },
    "plausible": {
        "name": "网站统计订阅软件",
        "priority": 2,
        "headline": "第二研究：提供轻量、隐私友好的统计服务",
        "reason": "公司历史披露 ARR 和付费订阅者，支持该企业曾有付费经营的结论。",
        "fit": "适合有软件开发与持续技术维护能力的人研究。",
        "risk": "获客、系统稳定性、合规和产品差异化尚未完成新进入者验证。",
        "next": "调查某个垂直细分客户是否愿意付费更换现有统计工具。",
        "label": "优先研究 02",
    },
    "nerdwallet": {
        "name": "金融内容与产品比较平台",
        "priority": 3,
        "headline": "成熟标杆：建议学习，不建议直接照搬",
        "reason": "存在公司级历史监管财务申报，但不能据此证明个人也能按同样方式获利。",
        "fit": "更适合作为内容、信任与规模化运营的案例研究。",
        "risk": "金融信息合规、获客规模与专业内容制作门槛较高，缺少可复制性证明。",
        "next": "先分析细分受众、合法合规范围和稳定获客渠道，不建议先投入开发。",
        "label": "标杆研究 03",
    },
}

STYLE = """
.recommend-first{max-width:1380px;margin:0 auto;padding:clamp(110px,11vw,165px) calc(var(--pad) + var(--safe-right)) clamp(45px,6vw,85px) calc(var(--pad) + var(--safe-left));background:var(--bg);color:var(--ink)}
.rec-kicker{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.17em;color:var(--accent);margin-bottom:22px}
.recommend-first h1{max-width:950px;font:500 clamp(36px,5.3vw,74px)/1.18 var(--serif);letter-spacing:-.02em;margin:0 0 22px}
.rec-lead{max-width:820px;font-size:clamp(15px,1.6vw,19px);line-height:1.85;color:var(--dim);margin:0 0 26px}
.rec-actions{display:flex;align-items:center;flex-wrap:wrap;gap:11px;margin:20px 0 32px}
.rec-actions a{display:inline-flex;min-height:46px;align-items:center;padding:11px 18px;border:1px solid var(--line);text-decoration:none;color:var(--ink);font-size:14px;font-weight:650}
.rec-actions a:first-child{background:var(--ink);color:var(--bg)}
.rec-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-block:1px solid var(--line);margin:23px 0 40px;padding:20px 0;gap:20px}
.rec-stats strong{display:block;font:500 clamp(25px,3vw,38px)/1.2 var(--serif)}
.rec-stats span{display:block;font-size:12px;color:var(--dim);margin-top:5px}
.rec-head{display:flex;align-items:baseline;justify-content:space-between;gap:15px;flex-wrap:wrap;margin-bottom:20px}
.rec-head h2{font:500 clamp(26px,3.1vw,42px)/1.28 var(--serif);margin:0}
.rec-head p{color:var(--dim);font-size:13px;margin:0;max-width:500px;line-height:1.75}
.rec-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:17px}
.rec-card{min-width:0;background:var(--panel);border:1px solid var(--line);padding:clamp(21px,3vw,33px)}
.rec-card--reference{grid-column:1/-1}
.rec-card__top{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:15px}
.rec-card__order{font-size:12px;font-weight:750;color:var(--accent);letter-spacing:.06em}
.rec-card__tier{font-size:12px;color:var(--dim)}
.rec-card h3{font:500 clamp(22px,2.5vw,31px)/1.32 var(--serif);margin:0 0 12px}
.rec-card__sub{font-size:13px;font-weight:650;color:var(--accent);margin:0 0 16px}
.rec-card dl{display:grid;grid-template-columns:86px minmax(0,1fr);column-gap:12px;row-gap:10px;margin:0}
.rec-card dt{color:var(--dim);font-size:13px}
.rec-card dd{font-size:14px;line-height:1.7;margin:0}
.rec-card__proof{padding:12px 0;border-block:1px solid var(--line);margin:19px 0 16px}
.rec-card__proof b{display:block;font-size:12px;color:var(--accent);margin-bottom:7px}
.rec-card__proof p{font-size:14px;line-height:1.7;margin:0}
.rec-card__period{color:var(--dim);font-size:12px;display:block;margin-top:8px}
.rec-card__link{display:inline-flex;min-height:44px;align-items:center;color:var(--accent);font-size:14px;font-weight:700;text-underline-offset:4px}
.rec-no-promise{margin:24px 0 0;padding:17px 20px;border-left:3px solid var(--accent);background:var(--panel);font-size:13px;line-height:1.8;color:var(--ink)}
.recommend-first a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media(max-width:760px){.recommend-first{padding-top:105px}.rec-cards{grid-template-columns:1fr}.rec-card--reference{grid-column:auto}.rec-stats{gap:10px}.rec-card dl{grid-template-columns:75px 1fr}.rec-card dd{font-size:13px}.rec-card{padding:20px}}
@media(max-width:450px){.rec-stats strong{font-size:25px}.rec-stats span{font-size:11px}.rec-actions a{width:100%;justify-content:center}}
"""

def render_recommendations(cases: list[dict]) -> str:
    """Provide research choices, never fraudulently mark 'proven to start'."""
    by_id = {x["id"]: x for x in cases}
    cards = []
    for slug, info in sorted(RESEARCH_CHOICES.items(), key=lambda x: x[1]["priority"]):
        item = by_id.get(slug)
        if item is None:
            continue
        d = derive_digest(item)
        tier = "L4 · 监管历史财务" if item["evidence_level"] == 4 else "L3 · 历史经营自述"
        badge = escape(info["label"])
        cards.append(
            f'<article class="rec-card{" rec-card--reference" if slug == "nerdwallet" else ""}" data-case="{slug}">'
            '<div class="rec-card__top">'
            f'<span class="rec-card__order">{badge}</span><span class="rec-card__tier">{tier}</span></div>'
            f'<h3>{escape(info["headline"])}</h3>'
            f'<p class="rec-card__sub">已核实经营披露的案例：{escape(item["title"].split("｜",1)[0])}</p>'
            '<dl>'
            f'<dt>为什么看</dt><dd>{escape(info["reason"])}</dd>'
            f'<dt>适合研究</dt><dd>{escape(info["fit"])}</dd>'
            f'<dt>最大疑问</dt><dd>{escape(info["risk"])}</dd>'
            f'<dt>第一步</dt><dd>{escape(info["next"])}</dd>'
            '</dl>'
            '<div class="rec-card__proof"><b>有出处的历史经营证据</b>'
            f'<p>{escape(d.evidence)}</p>'
            f'<span class="rec-card__period">{escape(d.period)} · {escape(d.certainty)} · 不代表当前创业收益</span></div>'
            f'<a class="rec-card__link" href="/projects/{slug}/">'
            '查看完整经营证据与原始来源 ↗</a></article>'
        )
    if not cards:
        raise RuntimeError("No source-backed case available for research recommendations")
    # No case currently proves startup costs, customer acquisition and ability
    # for *new founders* to reproduce outcomes. Never invent one.
    return (
        '<section class="recommend-first" id="recommendations" aria-labelledby="rec-title">'
        '<span class="rec-kicker">JIANSHI PICKS / 先给结论</span>'
        '<h1 id="rec-title">找项目，先看这里。<br>我们帮你筛选。</h1>'
        '<p class="rec-lead">见势只把有真实经营披露的企业作为研究案例。'
        '下面是优先值得研究的商业方向，不是“照着做就能赚钱”的承诺。'
        '真正适不适合你启动，还要核实预算、获客渠道和执行能力。</p>'
        '<div class="rec-actions"><a href="#pick-list">直接看本期推荐研究 ↘</a>'
        '<a href="/projects/">查看全部有证据案例 ↗</a></div>'
        '<div class="rec-stats">'
        f'<div><strong>{len(cases)}</strong><span>具有可归属经营证据的案例</span></div>'
        f'<div><strong>{sum(1 for id in ("carrd","plausible") if id in by_id)}</strong>'
        '<span>建议优先研究的业务方向</span></div>'
        '<div><strong>0</strong><span>已证明适合直接投入创业的项目</span></div></div>'
        '<div class="rec-head" id="pick-list"><h2>本期先研究什么？</h2>'
        '<p>按轻量化研究起点排序，不是盈利能力或成功率排名。</p></div>'
        f'<div class="rec-cards">{"".join(cards)}</div>'
        '<p class="rec-no-promise"><strong>为什么没有“闭眼开干”的项目？</strong> '
        '企业过去赚过钱，只证明该企业的历史经营，不证明新创业者可以复制。'
        '见势会继续验证具体需求、成本与获客，满足落地条件后才给出可启动推荐。'
        '建议中的第一步属于研究计划，尚不是经过验证的落地结果。</p>'
        '</section>'
    )


def recommendation_first_home(public_html: str, cases: list[dict]) -> str:
    if public_html.count('<main id="top">') != 1 or public_html.count("</style>") != 1:
        raise RuntimeError("Main site structure changed: no safe recommendation injection")
    if not cases or any(case.get("evidence_level", 0) < 3 for case in cases):
        raise RuntimeError("Non-admitted project passed into recommendation view")
    public_html = public_html.replace("</style>", STYLE + "</style>", 1)
    public_html = public_html.replace('<main id="top">',
                                      '<main id="top">' + render_recommendations(cases), 1)
    # The old visual interaction remains, but no longer blocks decisions.
    nav = '<a href="/projects/">验证档案</a>'
    if public_html.count(nav) != 1:
        raise RuntimeError("Navigation has changed")
    public_html = public_html.replace(nav, '<a href="#recommendations">给我推荐</a>' + nav, 1)
    return public_html
