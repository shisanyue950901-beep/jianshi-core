"""P4.27: recommendation-first entrance based only on admitted named evidence.

Company operating evidence supports *research recommendations*. It does not
establish startup reproducibility, costs, acquisition or founder fit. Never
auto-label a company as a proven startup opportunity.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

from p426_evidence_digest import derive_digest
from p438_public_ux_contract import entry_contract, public_metrics

PROFILE_FILE = Path(__file__).resolve().parents[2] / "config/p428_solo_startup_profile.json"
VALID_FIT = {"TEST_IDEA_ONLY", "SKILL_GATED", "NOT_SOLO_STARTUP"}

def load_solo_profile() -> dict:
    data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    if data.get("version") != "P428_SOLO_LOW_CAPITAL_ZERO_START_V1":
        raise RuntimeError("未经审核的一人低资金推荐规则")
    audience = data.get("default_audience") or {}
    if audience.get("team_size") != 1 or audience.get("starting_stage") != "从零启动":
        raise RuntimeError("默认目标用户条件发生漂移")
    entries = data.get("case_assessments", [])
    if not isinstance(entries, list) or not entries:
        raise RuntimeError("未配置创业适配门槛")
    indexed = {}
    for item in entries:
        slug = item.get("id")
        if not isinstance(slug, str) or slug in indexed or item.get("status") not in VALID_FIT:
            raise RuntimeError("创业适配对象重复或状态非法")
        if item.get("ready_for_launch") is not False:
            raise RuntimeError("缺少实际付费／获客验证，不能宣称已具备直接创业资格")
        for key in ("tag", "prototype", "solo_logic", "capital_logic", "first_step", "blocker", "skills"):
            min_len = 8 if key in ("prototype", "tag") else 12
            if not isinstance(item.get(key), str) or len(item[key].strip()) < min_len:
                raise RuntimeError("创业适配评价缺少必要证据边界：" + key)
        if not isinstance(item.get("order"), int) or item["order"] < 1:
            raise RuntimeError("无效的评估排序")
        indexed[slug] = item
    return {"audience": audience, "cases": indexed}

RESEARCH_CHOICES = {
    "carrd": {
        "name": "轻量建站工具",
        "priority": 1,
        "headline": "从零测试：给一个细分群体做单页网站",
        "reason": "Carrd 的创始人曾披露历史经常性收入；但这只能证明原公司经营过，不能证明你的建站服务能卖出去。",
        "fit": "可以先用现成建站工具做样板、手工服务客户，不必先开发 SaaS；仍需要基本排版和沟通能力。",
        "risk": "这个细分服务是否有人付费、获客成本及交付时间都未得到项目级验证。",
        "next": "先锁定一个更小的客户群，核实真实购买需求，再决定是否开发。",
        "label": "优先研究 01",
    },
    "plausible": {
        "name": "网站统计订阅软件",
        "priority": 2,
        "headline": "技术备选：网站统计订阅软件",
        "reason": "公司历史披露 ARR 和付费订阅者，支持该企业曾有付费经营的结论。",
        "fit": "需要开发、运维和持续技术维护；不是新手从零、低预算的默认选择。",
        "risk": "获客、系统稳定性、合规和产品差异化尚未完成新进入者验证。",
        "next": "调查某个垂直细分客户是否愿意付费更换现有统计工具。",
        "label": "技术门槛 · 暂不优先",
    },
    "nerdwallet": {
        "name": "金融内容与产品比较平台",
        "priority": 3,
        "headline": "成熟标杆：不建议一人低资金直接照搬",
        "reason": "存在公司级历史监管财务申报，但不能据此证明个人也能按同样方式获利。",
        "fit": "更适合作为内容、信任与规模化运营的案例研究。",
        "risk": "金融信息合规、获客规模与专业内容制作门槛较高，缺少可复制性证明。",
        "next": "先分析细分受众、合法合规范围和稳定获客渠道，不建议先投入开发。",
        "label": "成熟标杆 · 不推荐照搬",
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
.rec-card--primary{grid-column:1/-1;border-left:4px solid var(--accent)}
.rec-card--reference{grid-column:auto}
.rec-profile{display:flex;flex-wrap:wrap;gap:9px;margin:0 0 18px}
.rec-profile span{border:1px solid var(--line);font-size:12px;padding:7px 12px;border-radius:2px;color:var(--ink);background:var(--panel)}
.rec-card__gate{font-size:13px;font-weight:700;color:var(--accent);padding:9px 0;border-bottom:1px solid var(--line);margin:0 0 14px}
.rec-card__business-idea{margin:0 0 13px;color:var(--ink);font-size:15px;line-height:1.7}
.rec-card__business-idea b{color:var(--accent)}
.rec-card__solo{margin-top:17px;padding:13px 15px;background:color-mix(in srgb,var(--accent) 9%,var(--panel));font-size:13px;line-height:1.8}
.rec-card__solo b{display:block;color:var(--accent);margin-bottom:5px}
.rec-card__capital{color:var(--dim);margin-top:11px;font-size:12px;line-height:1.7}
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
@media(max-width:760px){.recommend-first{padding-top:105px}.rec-cards{grid-template-columns:1fr}.rec-card--reference{grid-column:auto}.rec-card--primary{grid-column:auto}.rec-stats{gap:10px}.rec-card dl{grid-template-columns:75px 1fr}.rec-card dd{font-size:13px}.rec-card{padding:20px}}
@media(max-width:450px){.rec-stats strong{font-size:25px}.rec-stats span{font-size:11px}.rec-actions a{width:100%;justify-content:center}}

/* P4.39: goal first, three honest metrics, lightweight intent routes. */
.recommend-first{scroll-margin-top:70px}
.rec-kicker{margin-bottom:15px}
.recommend-first h1{max-width:880px;line-height:1.14}
.rec-lead{max-width:690px;margin-bottom:18px}
.rec-actions{margin:20px 0 25px}
.rec-actions a:nth-child(2){border-color:var(--ink)}
.rec-quick{border:1px solid var(--line);padding:18px 20px;margin:24px 0 29px;scroll-margin-top:95px}
.rec-quick h2{font:500 clamp(18px,2.2vw,24px)/1.4 var(--serif);margin:0 0 7px}
.rec-quick>p{color:var(--dim);font-size:13px;line-height:1.7;margin:0 0 13px}
.rec-quick__list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
.rec-quick__list a{display:flex;flex-direction:column;gap:5px;min-height:90px;padding:13px;border:1px solid var(--line);text-decoration:none;color:var(--ink)}
.rec-quick__list a:hover,.rec-quick__list a:focus-visible{border-color:var(--accent);background:var(--panel)}
.rec-quick__list b{font-size:14px;font-weight:650}
.rec-quick__list span{font-size:12px;color:var(--dim);line-height:1.6}
.rec-stats{margin:19px 0 34px;grid-template-columns:repeat(3,minmax(0,1fr))}
.rec-stat b{display:block;font:500 clamp(28px,3.2vw,44px)/1.2 var(--serif)}
.rec-stat span{max-width:22ch}
.rec-profile{margin:16px 0 20px}
#pick-list,.rec-card{scroll-margin-top:95px}
@media(max-width:760px){.recommend-first{padding-top:84px}.rec-quick__list{grid-template-columns:1fr}.rec-quick__list a{min-height:68px}.rec-quick{padding:16px}.rec-stats{gap:9px}}
@media(max-width:450px){.rec-kicker{font-size:10px;letter-spacing:.09em;margin-bottom:11px}.recommend-first h1{font-size:clamp(32px,8.6vw,39px);margin-bottom:13px}.rec-lead{font-size:14px;line-height:1.65;margin-bottom:13px}.rec-actions{gap:8px;margin:16px 0 24px}.rec-actions a{min-height:44px}.rec-stats strong,.rec-stat b{font-size:clamp(24px,7vw,33px)}.rec-stats span{font-size:11px}}
@media(prefers-reduced-motion:reduce){.rec-quick__list a{transition:none}}

"""

def render_recommendations(cases: list[dict]) -> str:
    """Provide research choices, never fraudulently mark 'proven to start'."""
    metrics = public_metrics(cases)
    ux = entry_contract()
    home = ux["public_home"]
    quick = ux["quick_paths"]
    by_id = {x["id"]: x for x in cases}
    profile = load_solo_profile()
    profiles = profile["cases"]
    cards = []
    for slug, info in sorted(RESEARCH_CHOICES.items(), key=lambda x: profiles[x[0]]["order"] if x[0] in profiles else 999):
        item = by_id.get(slug)
        if item is None or slug not in profiles:
            continue
        policy = profiles[slug]
        status = policy["status"]
        d = derive_digest(item)
        tier = "L4 · 监管历史财务" if item["evidence_level"] == 4 else "L3 · 历史经营自述"
        badge = escape(info["label"])
        cards.append(
            f'<article class="rec-card{" rec-card--primary" if status == "TEST_IDEA_ONLY" else " rec-card--reference"}" id="case-{slug}" data-case="{slug}" data-solo-fit="{status}">'
            '<div class="rec-card__top">'
            f'<span class="rec-card__order">{badge}</span><span class="rec-card__tier">{tier}</span></div>'
            f'<p class="rec-card__gate">{escape(policy["tag"])}</p>'
            f'<h3>{escape(info["headline"])}</h3>'
            f'<p class="rec-card__business-idea"><b>从零测试方向：</b>{escape(policy["prototype"])}</p>'
            f'<p class="rec-card__sub">已核实经营披露的案例：{escape(item["title"].split("｜",1)[0])}</p>'
            '<dl>'
            f'<dt>为什么看</dt><dd>{escape(info["reason"])}</dd>'
            f'<dt>适合研究</dt><dd>{escape(info["fit"])}</dd>'
            f'<dt>最大疑问</dt><dd>{escape(info["risk"])}</dd>'
            f'<dt>第一步</dt><dd>{escape(policy["first_step"])}</dd>'
            '</dl>'
            '<div class="rec-card__solo"><b>一人小资金怎么判断？</b>'
            f'{escape(policy["solo_logic"])}'
            f'<p class="rec-card__capital">资金边界：{escape(policy["capital_logic"])}</p>'
            f'<p class="rec-card__capital">尚缺证据：{escape(policy["blocker"])}</p></div>'
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
    quick_links = "".join(
        '<a href="'+escape(item["href"],quote=True)+'"><b>'+escape(item["label"])+'</b>'
        '<span>'+escape(item["description"])+'</span></a>'
        for item in quick
    )
    stats = "".join(
        '<div class="rec-stat"><strong>'+str(metrics[item["key"]])+'</strong>'
        '<span>'+escape(item["label"])+'</span></div>'
        for item in ux["metrics"]
    )
    return (
        '<section class="recommend-first" id="recommendations" aria-labelledby="rec-title">'
        '<span class="rec-kicker">JIANSHI PICKS / 一个人 · 小资金 · 从零启动</span>'
        f'<h1 id="rec-title">{escape(home["headline"])}</h1>'
        f'<p class="rec-lead">{escape(home["subhead"])}'
        '默认从一个人、小资金、从零起步考虑适配性；历史公司经营不等于你的创业收益。</p>'
        '<div class="rec-actions">'
        f'<a href="{escape(home["primary_action"]["href"],quote=True)}">{escape(home["primary_action"]["label"])} ↘</a>'
        f'<a href="{escape(home["secondary_action"]["href"],quote=True)}">{escape(home["secondary_action"]["label"])} ↘</a>'
        '</div>'
        '<div class="rec-stats" aria-label="已审核项目与商业模式数量">'
        + stats + '</div>'
        '<section class="rec-quick" id="quick-start" aria-labelledby="quick-title">'
        '<h2 id="quick-title">你想从哪里开始？</h2>'
        '<p>按研究目标选择，不是自动计算成功概率。当前仅有可先小成本测试的方向（未证实盈利），先验证需求，再考虑投入。</p>'
        '<nav class="rec-quick__list" aria-label="研究路径选择">' + quick_links + '</nav>'
        '</section>'
        '<div class="rec-profile" aria-label="默认推荐条件"><span>一人创业</span><span>无库存优先</span>'
        '<span>不用先组团队</span><span>不假定会编程</span><span>资金预算仍待确认</span></div>'
        '<div class="rec-head" id="pick-list"><h2>一个人从零，先试什么？</h2>'
        '<p>优先给能一人做小范围需求测试的方向；技术型项目和大型平台默认降级。</p></div>'
        f'<div class="rec-cards">{"".join(cards)}</div>'
        '<p class="rec-no-promise"><strong>为什么没有“闭眼开干”的项目？</strong> '
        f'当前已证明适合直接投入创业的项目有 {metrics["verified_launch"]} 个。'
        '企业过去赚过钱，只证明该企业的历史经营，不证明新创业者可以复制。'
        '目前只建议先访谈客户、制作样板和尝试获取试单，不建议直接投入完整开发。'
        '见势会继续验证具体需求、成本与获客，满足落地条件后才给出可启动推荐。'
        '建议中的第一步属于研究计划，尚不是经过验证的落地结果。</p>'
        '<a class="rec-card__link" href="/sources/">商业市场数据从哪来？查看资料来源与证据口径 ↗</a>'
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
    # P4.39: primary navigation has only three user-facing choices. The
    # dossiers, sources and comparison remain accessible via page CTAs.
    start = '<nav aria-label="主要导航">'
    if public_html.count(start) != 1:
        raise RuntimeError("Primary navigation changed")
    left = public_html.index(start) + len(start)
    right = public_html.find("</nav>", left)
    if right < 0:
        raise RuntimeError("Unclosed primary navigation")
    primary = entry_contract()["public_home"]["navigation"]
    if len(primary) != 3 or [n.get("href") for n in primary] != [
            "#recommendations", "#models", "#about"]:
        raise RuntimeError("Unsafe main navigation contract")
    links = "".join(
        '<a href="' + escape(item["href"],quote=True) + '">'
        + escape(item["label"]) + '</a>' for item in primary
    )
    public_html = public_html[:left] + "\n" + links + "\n" + public_html[right:]
    return public_html
