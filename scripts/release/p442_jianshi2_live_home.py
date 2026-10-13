"""JIANSHI 2.0: release-time portal, built only from admitted case evidence.

Keeps the P4.12E interactive research experience, strict named-case admission,
privacy, public research appendix and static-only deployment intact.
Never fetches network data or writes private source records.
"""
from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path

from p438_public_ux_contract import public_metrics

ROOT = Path(__file__).resolve().parents[2]
VISUAL_SOURCE = ROOT / "web/prototypes/jianshi2-v1/index.html"

STYLE = """
/* JIANSHI 2.0 portal: scoped to the release-only homepage. */
#j2{--j2-ink:#101d30;--j2-muted:#66758d;--j2-edge:#e5eaf3;--j2-blue:#538dff;--j2-violet:#9975ff;color:var(--j2-ink);background:#f7f9fd;font:15px/1.67 "PingFang SC","Microsoft YaHei",Inter,system-ui,sans-serif;isolation:isolate}
#j2,#j2 *{box-sizing:border-box}#j2 a{text-decoration:none}#j2 .j2-wrap{width:min(1260px,calc(100% - 56px));margin-inline:auto}
#j2 .j2-mast{position:relative;overflow:hidden;background:#07101e;color:#fff}
#j2 .j2-mast:before{content:"";position:absolute;inset:-40% -30% auto 30%;height:700px;background:radial-gradient(ellipse,rgba(99,79,242,.28),transparent 65%);pointer-events:none}
#j2 .j2-hero{position:relative;display:grid;grid-template-columns:1.1fr 1fr;align-items:center;gap:24px;padding-top:70px;padding-bottom:90px;min-height:530px}
#j2 .j2-kicker{display:inline-flex;align-items:center;padding:6px 13px;border:1px solid #536487;border-radius:40px;background:#182844;color:#d6ddff;font-size:12px;letter-spacing:.05em}
#j2 h1{font-size:clamp(42px,4.7vw,70px);line-height:1.18;font-weight:850;letter-spacing:-.05em;color:#fff;margin:24px 0 20px}
#j2 h1 em{font-style:normal;color:#a9a0ff;background:linear-gradient(100deg,#b3a0ff,#52bbff);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}
#j2 .j2-lead{font-size:clamp(15px,1.55vw,19px);line-height:1.8;color:#c2cede;max-width:600px;margin:0 0 30px}
#j2 .j2-actions{display:flex;gap:12px;flex-wrap:wrap}
#j2 .j2-button{display:inline-flex;justify-content:center;align-items:center;gap:8px;min-height:47px;padding:11px 21px;border-radius:12px;font-weight:750;font-size:14px;transition:transform .24s,box-shadow .24s;border:1px solid #64718a;color:#eff5ff}
#j2 .j2-button:hover,#j2 .j2-button:focus-visible{transform:translateY(-3px)}
#j2 .j2-button--primary{border:0;background:linear-gradient(110deg,#936aff,#418efb);box-shadow:0 12px 30px #383fbc55;color:white}
#j2 .j2-proofnote{margin-top:23px;font-size:12px;line-height:1.7;color:#a1b0c8;max-width:575px}
#j2 .j2-visual{position:relative}
#j2 .j2-visual:before{content:"";position:absolute;inset:10% 4%;border-radius:50%;background:#6e7bff60;filter:blur(70px)}
#j2 .j2-visual img{position:relative;display:block;width:100%;height:auto;max-height:430px;object-fit:contain;filter:drop-shadow(0 28px 38px #0008);border-radius:18px;animation:j2Float 7s ease-in-out infinite}
@keyframes j2Float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
#j2 .j2-metrics{background:#101c30;border:1px solid #34405a;border-radius:18px;position:relative;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;transform:translateY(-31px);margin-bottom:-31px;box-shadow:0 18px 35px #121e3533}
#j2 .j2-metric{padding:18px 25px;border-right:1px solid #34405a;color:#fff}#j2 .j2-metric:last-child{border:0}
#j2 .j2-metric strong{display:block;font-size:31px;line-height:1.2;font-weight:800}#j2 .j2-metric span{display:block;color:#c6d1e3;font-size:12px;margin-top:7px}
#j2 .j2-content{padding:58px 0 82px}#j2 .j2-intro{display:flex;justify-content:space-between;align-items:end;gap:25px;margin-bottom:25px}
#j2 .j2-overline{font-size:11px;font-weight:800;letter-spacing:.14em;color:#6855d2}
#j2 h2{font-size:clamp(27px,3.1vw,42px);line-height:1.25;letter-spacing:-.035em;margin:9px 0 8px;font-weight:780;color:#172338}
#j2 .j2-intro p,#j2 .j2-muted{color:#66758d;font-size:14px;margin:0}
#j2 .j2-shortcuts{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-bottom:70px}
#j2 .j2-shortcut{display:flex;min-width:0;min-height:145px;flex-direction:column;justify-content:space-between;border:1px solid #e3e9f4;background:#fff;border-radius:17px;padding:20px;transition:transform .25s,box-shadow .25s,border-color .25s}
#j2 .j2-shortcut:hover,#j2 .j2-shortcut:focus-visible{transform:translateY(-6px);border-color:#b5bcfa;box-shadow:0 19px 42px #303d7815}
#j2 .j2-shortcut i{font-size:25px;font-style:normal}#j2 .j2-shortcut strong{font-size:15px;color:#14253c}
#j2 .j2-shortcut small{display:block;color:#718097;font-size:11px;margin-top:3px}#j2 .j2-shortcut .j2-arrow{align-self:flex-end;color:#7e70df;font-weight:bold}
#j2 .j2-study-paths{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin:0 0 42px}
#j2 .j2-study-path{display:flex;flex-direction:column;gap:7px;border:1px solid #dce6f4;background:white;border-radius:16px;padding:22px;color:#172a45;min-height:145px}
#j2 .j2-study-path:hover,#j2 .j2-study-path:focus-visible{border-color:#8972e7;box-shadow:0 12px 28px #303d7815}
#j2 .j2-study-path strong{font-size:16px}#j2 .j2-study-path span{font-size:13px;line-height:1.7;color:#64748b}
#j2 .j2-study-path small{font-size:12px;font-weight:750;color:#6252bf;margin-top:auto}
#j2 .j2-research-check{background:#f7f9fe;border-left:3px solid #a69af4;padding:13px 14px;display:flex;flex-direction:column;gap:5px}
#j2 .j2-research-check dt{font-size:12px;font-weight:800;color:#33486c}#j2 .j2-research-check dd{font-size:12px;line-height:1.65;color:#66758d;margin:0}
#j2 .j2-section{margin-top:70px;scroll-margin-top:92px}
#j2 .j2-sectionhead{display:flex;align-items:end;justify-content:space-between;gap:18px;margin-bottom:23px}
#j2 .j2-sectionhead .j2-plainlink{color:#4753c9;text-decoration:underline;text-underline-offset:5px;white-space:nowrap;font-size:13px}
#j2 .j2-projects{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px}
#j2 .j2-project{background:white;border:1px solid var(--j2-edge);border-radius:17px;padding:25px;min-width:0;display:flex;flex-direction:column;gap:13px;transition:transform .22s,box-shadow .22s}
#j2 .j2-project:hover{transform:translateY(-4px);box-shadow:0 16px 35px #34477a16}
#j2 .j2-project .j2-case-type{color:#655ad8;font-size:11px;letter-spacing:.04em;font-weight:800}
#j2 .j2-project h3{font-size:22px;line-height:1.35;margin:0;color:#172238}
#j2 .j2-project p{margin:0;color:#61708a;font-size:13px;line-height:1.8;flex-grow:1}
#j2 .j2-project a{color:#525bc9;font-size:13px;font-weight:780}
#j2 .j2-solutions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}
#j2 .j2-solution{overflow:hidden;background:white;border:1px solid var(--j2-edge);border-radius:16px;min-width:0}
#j2 .j2-solution-body a{display:inline-block;margin-top:14px;color:#5853c4;font-size:12px;font-weight:800}
#j2 .j2-art{height:144px;display:flex;align-items:center;justify-content:center;font-size:58px;position:relative;color:white;overflow:hidden}
#j2 .j2-art::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 65% 30%,#ffffff49,transparent 58%)}
#j2 .j2-solution:nth-child(1) .j2-art{background:linear-gradient(135deg,#d999e5,#6452a8)}
#j2 .j2-solution:nth-child(2) .j2-art{background:linear-gradient(135deg,#292b50,#638bdc)}
#j2 .j2-solution:nth-child(3) .j2-art{background:linear-gradient(135deg,#266a9d,#3dcaaf)}
#j2 .j2-solution:nth-child(4) .j2-art{background:linear-gradient(135deg,#142d4b,#777cff)}
#j2 .j2-solution-body{padding:18px 20px 21px}
#j2 .j2-solution h3{font-size:17px;font-weight:780;color:#1b2841;margin:0 0 7px}
#j2 .j2-solution p{font-size:13px;color:#65748d;margin:0;min-height:60px}
#j2 .j2-solution small{color:#7b6cc5;display:block;margin-top:15px;font-size:11px}
#j2 .j2-two{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:70px}
#j2 .j2-panel{border:1px solid #e1e8f4;background:white;border-radius:19px;padding:32px;scroll-margin-top:100px}
#j2 .j2-panel--dark{background:linear-gradient(130deg,#101a2d,#222e51);color:#fff;border-color:#303c5a}
#j2 .j2-panel--dark h2{color:#fff}#j2 .j2-panel--dark .j2-muted{color:#c0cbe1}
#j2 .j2-panel .j2-status{display:inline-flex;border-radius:100px;padding:4px 11px;background:#f0edff;color:#6752b8;font-size:11px;font-weight:800}
#j2 .j2-panel--dark .j2-status{background:#364266;color:#ebe4ff}
#j2 .j2-panel a{display:inline-block;margin-top:22px;font-weight:760;font-size:13px;color:#5c59c8;text-decoration:underline;text-underline-offset:4px}
#j2 .j2-panel--dark a{color:#c9bcff}
#j2 .j2-academy{background:linear-gradient(112deg,#0b1530,#2a2560);color:white;border-radius:22px;padding:37px;margin-top:19px;scroll-margin-top:90px}
#j2 .j2-academy h2{color:white;margin-top:13px}#j2 .j2-academy p{font-size:14px;color:#c4ceef;max-width:770px}
#j2 .j2-tags{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}#j2 .j2-tags span{border:1px solid #53638a;border-radius:90px;font-size:12px;padding:7px 12px}
#j2 a:focus-visible{outline:3px solid #74b4ff;outline-offset:4px}
body:has(#j2) .top{background:#07101e;border-bottom:1px solid #273549;color:#f1f5ff}
body:has(#j2) .top .mark,body:has(#j2) .top .mark em{color:#f1f5ff}
body:has(#j2) .top .menu-btn,body:has(#j2) .top .theme-toggle{color:#eff5ff;border-color:#516078}
body:has(#j2) #splash{display:none!important}
@media(max-width:1050px){#j2 .j2-shortcuts{grid-template-columns:repeat(3,minmax(0,1fr))}#j2 .j2-solutions{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){#j2 .j2-wrap{width:calc(100% - 36px)}#j2 .j2-hero{grid-template-columns:1fr;padding-top:52px;padding-bottom:85px;gap:15px;min-height:0}#j2 .j2-visual img{max-height:310px}#j2 h1{font-size:clamp(36px,8.9vw,53px)}#j2 .j2-actions .j2-button{min-height:45px}#j2 .j2-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}#j2 .j2-metric{padding:14px 11px}#j2 .j2-metric strong{font-size:clamp(22px,6vw,31px)}#j2 .j2-metric span{font-size:10px}#j2 .j2-content{padding-top:41px}#j2 .j2-shortcuts{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}#j2 .j2-study-paths{grid-template-columns:1fr;gap:10px}#j2 .j2-projects{grid-template-columns:1fr}#j2 .j2-two{grid-template-columns:1fr}#j2 .j2-section{margin-top:52px}#j2 .j2-sectionhead{align-items:start;flex-direction:column;gap:8px}#j2 .j2-panel{padding:25px}#j2 .j2-academy{padding:27px 23px}}
@media(max-width:450px){#j2 .j2-solutions{grid-template-columns:1fr}#j2 .j2-intro{display:block}#j2 .j2-shortcut{min-height:115px;padding:15px}}
@media(prefers-reduced-motion:reduce){#j2 .j2-visual img{animation:none}#j2 .j2-button,#j2 .j2-project,#j2 .j2-shortcut{transition:none;transform:none!important}}
"""


CASES = {
    "carrd": ("轻量建站与数字服务", "从小范围客户需求出发，研究如何以单页网站和数字产品提供服务。"),
    "plausible": ("隐私友好型网站分析", "研究订阅软件、技术维护和企业用户付费模式，不默认适合零基础直接创业。"),
    "nerdwallet": ("内容与产品比较平台", "研究成熟信息平台的内容、信任和流量模式；不将历史财报当成个人可复制收益。"),
}

# Editorial research prompts, not company-specific business facts or verified
# recommendations. Fixed, reviewed copy; independent of private listings.
RESEARCH_QUESTIONS = {
    "carrd": (
        "哪些细分客户愿意为单页网站和后续维护付费？",
        "目标客户的实际采购预算、获客渠道及交付时间仍未知。",
        "先访谈少量目标客户，核实是否存在可重复的付费需求。"
    ),
    "plausible": (
        "订阅分析工具解决什么问题，客户为何持续付费？",
        "对新进入者的开发、运维、获客门槛尚无独立验证。",
        "先比较现有工具与客户切换成本，不以原公司收入推导个人收益。"
    ),
    "nerdwallet": (
        "成熟内容比较平台如何通过信任与用户需求提供价值？",
        "获客规模、合规成本及个人复制可能性均缺乏直接证据。",
        "以经营与信任机制为研究对象，不将其列为新手启动推荐。"
    ),
}

SOLUTION_SLUGS = ("ecommerce-visual", "brand-video", "automation", "localization")

SOLUTIONS = (
    ("✦", "AI 电商视觉", "商品图片、品牌海报、视觉素材与批量内容制作。"),
    ("▣", "AI 视频与品牌短片", "短视频、品牌宣传与视频创意工作流。"),
    ("⌘", "AI 企业自动化", "知识库、智能客服与内部流程协作。"),
    ("◎", "AI 出海内容", "多语言创作、品牌内容本地化及海外营销素材。"),
)


def _get_visual() -> str:
    source = VISUAL_SOURCE.read_text(encoding="utf-8")
    hits = re.findall(r'<img src="(data:image/webp;base64,[A-Za-z0-9+/=]+)"', source)
    if len(hits) != 1:
        raise RuntimeError("F1 concept artwork not uniquely found")
    data = base64.b64decode(hits[0].split(",", 1)[1], validate=True)
    if not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"
            and 1_000 < len(data) <= 100_000):
        raise RuntimeError("Unexpected F1 artwork payload")
    return hits[0]


def render_portal(cases: list[dict]) -> str:
    metrics = public_metrics(cases)
    if set(CASES) != {case["id"] for case in cases}:
        raise RuntimeError("Only source-admitted cases can enter JIANSHI2 homepage")
    case_rows = "".join(
        '<article class="j2-project"><span class="j2-case-type">已审核历史研究案例 · '
        + ("监管历史财报" if case["evidence_level"] == 4 else "历史经营自述") + "</span>"
        + "<h3>" + escape(case["title"].split("｜", 1)[0]) + "</h3>"
        + "<p>" + escape(CASES[case["id"]][1]) + "</p>"
        + '<dl class="j2-research-check"><dt>先研究什么</dt><dd>'
        + escape(RESEARCH_QUESTIONS[case["id"]][0])
        + '</dd><dt>哪些问题还不知道</dt><dd>'
        + escape(RESEARCH_QUESTIONS[case["id"]][1])
        + '</dd><dt>可以怎样开始核实</dt><dd>'
        + escape(RESEARCH_QUESTIONS[case["id"]][2])
        + '</dd></dl>'
        + '<a href="/projects/' + escape(case["id"], quote=True)
        + '/">查看来源和证据边界 ↗</a></article>'
        for case in cases
    )
    solution_rows = "".join(
        '<article class="j2-solution"><div class="j2-art" aria-hidden="true">'
        + escape(icon) + '</div><div class="j2-solution-body"><h3>'
        + escape(title) + "</h3><p>" + escape(desc)
        + '</p><small>应用方向示意 · 暂无已核实平台交付案例</small>'
        + '<a href="/solutions/' + slug + '/">查看场景与交付清单 ↗</a></div></article>'
        for (icon, title, desc), slug in zip(SOLUTIONS, SOLUTION_SLUGS)
    )
    shortcut_data = (
        ("◈", "商业机会库", "经审核的公开研究", "j2-opportunities"),
        ("▤", "企业解决方案", "从业务问题出发", "j2-solutions"),
        ("◇", "商机大厅", "需求撮合规划", "j2-marketplace"),
        ("♙", "人才与服务商", "作品与技能体系", "j2-talent"),
        ("✧", "AIGC 学院", "自主课程筹备", "j2-academy"),
    )
    shortcuts = "".join(
        '<a class="j2-shortcut" href="#' + anchor + '"><i aria-hidden="true">'
        + escape(icon) + "</i><span><strong>" + escape(title)
        + "</strong><small>" + escape(detail)
        + '</small></span><span class="j2-arrow" aria-hidden="true">↗</span></a>'
        for icon, title, detail, anchor in shortcut_data
    )
    image = _get_visual()
    return (
        '<section id="j2" aria-label="见势 2.0 商业机会与解决方案门户">'
        '<div class="j2-mast"><div class="j2-wrap j2-hero">'
        '<div><span class="j2-kicker">JIANSHI 2.0 · 个人创业机会发现与决策</span>'
        '<h1>发现值得研究的<br><em>商业机会。</em></h1>'
        '<p class="j2-lead">面向个人创业者与小团队，发现经审核的真实商业案例，'
        '看懂收费模式、证据与风险，找到下一步值得核实的问题。'
        '不仅研究 AI，也关注电商、内容、数字产品和服务等商业模式。</p>'
        '<div class="j2-actions">'
        '<a class="j2-button j2-button--primary" href="#j2-opportunities">开始找项目 ↗</a>'
        '<a class="j2-button" href="/discover/">按主题筛选研究 ↗</a></div>'
        '<p class="j2-proofnote">见势帮助做研究判断，不保证项目收益或可复制性。'
        '商业证据有历史期间和来源局限；企业 AI 方案研究另见下方独立板块。'
        '概念配图不是项目证明，企业接单及课程平台正在建设中。</p></div>'
        '<div class="j2-visual"><img width="800" height="650" fetchpriority="high"'
        ' decoding="async" alt="AI 生成的见势 2.0 概念主视觉，非真实项目案例或企业客户"'
        ' src="' + image + '"></div></div></div>'
        '<div class="j2-wrap"><div class="j2-metrics" aria-label="真实来源受控研究概况">'
        '<div class="j2-metric"><strong>' + str(metrics["approved_cases"]) + '</strong><span>有历史经营证据的具名案例</span></div>'
        '<div class="j2-metric"><strong>' + str(metrics["verified_launch"]) + '</strong><span>已验证可直接启动的项目</span></div>'
        '<div class="j2-metric"><strong>' + str(metrics["business_models"]) + '</strong><span>已整理的商业模式</span></div>'
        '</div></div>'
        '<div class="j2-wrap j2-content">'
        '<div class="j2-intro"><div><span class="j2-overline">FIND · COMPARE · VERIFY</span>'
        '<h2>找项目，先从可信的研究开始。</h2>'
        '<p>三个入口帮助你按现有证据找项目、看商业模式，不要求注册。</p></div></div>'
        '<nav class="j2-study-paths" aria-label="创业机会三条研究路径">'
        '<a class="j2-study-path" href="/projects/"><strong>找真实案例</strong>'
        '<span>先看已审核的具名经营案例与原始来源。</span><small>查看具名案例 →</small></a>'
        '<a class="j2-study-path" href="/research/"><strong>比较商业模式</strong>'
        '<span>了解匿名分类研究，辨别数据样本与真实企业的区别。</span><small>比较六类模式 →</small></a>'
        '<a class="j2-study-path" href="/discover/"><strong>按主题探索</strong>'
        '<span>浏览已经审核的项目、行业与实用指南，不新增未经证实的推荐。</span><small>进入内容发现 →</small></a>'
        '</nav>'
        '<div class="j2-intro"><div><span class="j2-overline">MORE FROM JIANSHI</span>'
        '<h2>从商业机会研究，延伸到企业 AI 应用。</h2>'
        '<p>个人创业研究是当前核心业务；其他方向按实际开放状态展示。</p></div></div>'
        '<nav class="j2-shortcuts" aria-label="见势 2.0 五大业务入口">' + shortcuts + '</nav>'
        '<section class="j2-section" id="j2-opportunities"><div class="j2-sectionhead">'
        '<div><span class="j2-overline">RESEARCH OPPORTUNITIES</span><h2>有证据的商业机会研究</h2>'
        '<p class="j2-muted">历史案例供研究参考，不代表可以直接复制收益。</p></div>'
        '<a class="j2-plainlink" href="/projects/">查看全部严格收录档案 ↗</a></div>'
        '<div class="j2-projects">' + case_rows + '</div>'
        '<p class="j2-muted" style="margin-top:18px">另有六类匿名商业挂牌研究，'
        '不与具名公司收入或项目推荐混合。 <a href="/research/">查看匿名分类研究 →</a></p></section>'
        '<section class="j2-section" id="j2-solutions"><div class="j2-sectionhead">'
        '<div><span class="j2-overline">BUSINESS SOLUTIONS</span><h2>企业的问题，用合适的 AI 方法解决。</h2>'
        '<p class="j2-muted">首期展示典型应用场景，尚未开放真实服务采购或报价。</p></div>''<a class="j2-plainlink" href="/solutions/">查看完整解决方案指南 ↗</a></div>'
        '<div class="j2-solutions">' + solution_rows + '</div></section>'
        '<div class="j2-two">'
        '<section class="j2-panel" id="j2-marketplace"><span class="j2-status">商机大厅 · 建设中</span>'
        '<h2>让需求找到合适的交付者。</h2>'
        '<p class="j2-muted">企业需求发布、实名认证、审核及创作者项目申请将在 V2 开放。'
        '当前不展示虚构企业、订单、竞标人数或服务报价。</p>'
        '<a href="/marketplace/">查看企业需求模板与审核流程 ↗</a></section>'
        '<section class="j2-panel j2-panel--dark" id="j2-talent">'
        '<span class="j2-status">人才与服务商 · 建设中</span>'
        '<h2>让技能和作品成为可信的履历。</h2>'
        '<p class="j2-muted">计划提供作品集、技能标签、授权联系方式及人工审核。'
        '目前未开放真实入驻、自动匹配或项目投递。</p>'
        '<a href="/talent/">查看人才入驻与作品集准备指南 ↗</a></section>'
        '</div><section class="j2-academy" id="j2-academy">'
        '<span class="j2-overline" style="color:#bdb2ff">JIANSHI AIGC ACADEMY</span>'
        '<h2>学到的 AI 技能，最终形成可展示的作品。</h2>'
        '<p>课程视频、章节、学习进度、作业与作品集将在 V3 陆续开放。'
        '课程由团队后续自主制作并上传，当前不展示虚构的课程数、讲师或学员。</p>'
        '<div class="j2-tags"><span>AI 商业视觉</span><span>AI 视频与短片</span>'
        '<span>企业智能体</span><span>自动化工作流</span>'
        '<span>商业项目验证</span></div>''<a class="j2-button" style="margin-top:22px" href="/academy/">查看课程路线与实战成果规划 ↗</a></section>'
        '</div></section>'
    )


def integrate(portal_ready_html: str, admitted_cases: list[dict]) -> str:
    if (portal_ready_html.count('<main id="top">') != 1
            or portal_ready_html.count("</style>") != 1
            or portal_ready_html.count('id="recommendations"') != 1
            or portal_ready_html.count('id="ring"') != 1
            or portal_ready_html.count('id="lb"') != 1
            or portal_ready_html.count('id="grid"') != 1
            or 'id="j2"' in portal_ready_html):
        raise RuntimeError("Cannot safely integrate V2 portal into production research home")
    integrated = portal_ready_html.replace("</style>", STYLE + "</style>", 1)
    integrated = integrated.replace('<main id="top">', '<main id="top">' + render_portal(admitted_cases), 1)
    # Preserve older 3D, gallery, archival research and themes, but don't force
    # users to dismiss the original editorial splash before using the new site.
    if integrated.count('<body class="locked">') != 1:
        raise RuntimeError("Legacy splash body contract changed")
    integrated = integrated.replace('<body class="locked">', '<body>', 1)
    # Replace legacy three-entry overlay navigation only *after* P4.39's
    # independent gate has checked it in public_home().
    start = '<nav aria-label="主要导航">'
    if integrated.count(start) != 1:
        raise RuntimeError("Legacy navigation lost before V2 link integration")
    a = integrated.index(start) + len(start)
    b = integrated.index("</nav>", a)
    navigation = (
        '<a href="#j2-opportunities">商业机会</a>'
        '<a href="#j2-solutions">企业解决方案</a>'
        '<a href="#j2-marketplace">商机大厅</a>'
        '<a href="#j2-talent">人才与服务商</a>'
        '<a href="#j2-academy">AI 学院</a>'
        '<a href="#recommendations">项目研究建议</a>'
        '<a href="#models">商业模式</a>'
        '<a href="/sources/">数据来源</a>'
    )
    integrated = integrated[:a] + navigation + integrated[b:]
    # The production homepage's document metadata must describe JIANSHI 2.0,
    # not the earlier research-only portal. Keep the reviewed source unchanged.
    old_title = "<title>见势 JIANSHI｜发现海外项目，看懂一门生意</title>"
    old_description = ('<meta name="description" content="探索海外真实项目和商业模式，'
                       '了解它们提供什么、向谁收费、如何运作，以及哪些经营事实还需要进一步核实。">')
    title = "见势 JIANSHI 2.0｜AI 商业机会、企业解决方案与创作者"
    description = ("发现经审核的 AI 商业机会研究，了解企业 AI 解决方案与创作者服务。"
                   "商机撮合与 AIGC 课程正在建设，项目历史经营不代表可复制收益。")
    if integrated.count(old_title) != 1 or integrated.count(old_description) != 1:
        raise RuntimeError("Homepage metadata source contract changed")
    integrated = integrated.replace(old_title, "<title>" + escape(title) + "</title>", 1)
    integrated = integrated.replace(
        old_description,
        '<meta name="description" content="' + escape(description, quote=True) + '">',
        1,
    )
    if integrated.count("</head>") != 1:
        raise RuntimeError("Invalid main document head")
    social = (
        '<meta property="og:type" content="website">'
        '<meta property="og:title" content="' + escape(title, quote=True) + '">'
        '<meta property="og:description" content="' + escape(description, quote=True) + '">'
        '<meta property="og:url" content="https://jianshi-bua.pages.dev/">'
        '<meta name="twitter:card" content="summary">'
    )
    integrated = integrated.replace("</head>", social + "</head>", 1)
    return integrated
