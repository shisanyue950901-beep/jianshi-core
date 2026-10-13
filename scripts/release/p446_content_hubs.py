#!/usr/bin/env python3
"""P4.46: editorial-only JIANSHI2 content hubs and solution playbooks.

The pages describe potential deliverables and learning plans, NOT real jobs,
providers, customer testimonials, financial results, courses or matched deals.
Pure offline HTML. No user input collection, network, or source-derived finance.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from f21_design_tokens import render_css as render_design_css
from f21_components import site_header, site_footer
from f21_catalog_filter import (
    CSS as CATALOG_CSS, JS as CATALOG_JS, filter_panel, empty_state, category_for_slug,
)
from f21_g2b_guided_actions import (
    CSS as GUIDED_CSS, JS as GUIDED_JS, readiness, learning_selector, solution_trial,
)
from f21_g2c_related_quality import CSS as RELATED_CSS, render_related

SITE = "https://jianshi-bua.pages.dev"
PAGES = (
    "solutions/",
    "solutions/ecommerce-visual/",
    "solutions/brand-video/",
    "solutions/automation/",
    "solutions/localization/",
    "marketplace/",
    "talent/",
    "academy/",
)

SOLUTIONS = (
    {
        "slug": "ecommerce-visual", "tag": "电商做图",
        "name": "AI 电商视觉", "icon": "✦",
        "subtitle": "让商品视觉制作从单张图片走向规范化内容流程",
        "summary": "适用于需要频繁制作商品主图、详情页视觉、活动海报与多尺寸素材的商家。",
        "fit": "商品信息与图片版权明确，品牌风格已有基线，需要多平台尺寸适配的团队。",
        "problem": "新品上线与活动上新频繁，视觉素材需保持一致，但传统制作沟通和修订链条较长。",
        "inputs": ("商品原始图片及使用授权", "品牌字体、颜色、标识规范", "渠道规格、文案禁用词和审核责任人"),
        "steps": ("确定商品和渠道的视觉规格", "制作少量风格样片并人工确认", "扩展到尺寸适配、交付与版本归档"),
        "outputs": ("风格参考板与首轮视觉样片", "按约定尺寸整理的静态素材", "可追溯的提示词或设计说明（按协议）"),
        "checks": ("商品信息、材质和卖点没有凭空生成", "品牌用语、商标及字体授权明确", "导出规格与修改次数写入验收清单"),
        "boundary": "AI 图像可能生成失真的商品外观；涉及产品功能、功效及价格的表述均须企业审核。",
    },
    {
        "slug": "brand-video", "tag": "短视频制作",
        "name": "AI 视频与品牌短片", "icon": "▣",
        "subtitle": "从创意分镜到可复用的短视频制作流程",
        "summary": "用于品牌短片、社交媒体创意视频和营销方案中的视觉预演，不代表视频效果保证。",
        "fit": "已有产品、受众和传播目标，希望先以分镜或概念片验证表达方向。",
        "problem": "脚本、镜头与画面需要跨团队协同，修改周期长；直接大规模生成容易产生版权和质量风险。",
        "inputs": ("产品及传播目标简介", "合法授权的图片、音乐、声音或肖像素材", "时长、画幅、平台规则与禁用信息"),
        "steps": ("形成脚本、结构与分镜草案", "制作风格测试片并审查人物和品牌信息", "合成剪辑与音效，按版本审阅交付"),
        "outputs": ("脚本与分镜说明", "样片和最终导出文件（按协议）", "素材使用及版权核对清单"),
        "checks": ("时长、格式和字幕可读性符合约定", "音乐、声音、肖像及商标使用得到授权", "生成镜头的错误信息和视觉瑕疵已复查"),
        "boundary": "概念短片不能被冒充真实拍摄记录或客户见证；制作前确认使用权和传播许可。",
    },
    {
        "slug": "automation", "tag": "日常工作自动化",
        "name": "AI 企业自动化", "icon": "⌘",
        "subtitle": "从业务流程梳理，到可人工接管的 AI 工作流",
        "summary": "适用于企业知识库、客服辅助、工单分流与重复文书流程的可控试点。",
        "fit": "流程有明确负责人，数据使用经过授权，允许建立测试环境和人工复核关口。",
        "problem": "跨系统复制信息、重复归档及知识查询造成时间损耗，但贸然自动化可能放大权限或判断错误。",
        "inputs": ("现有流程及允许自动处理的范围", "系统接口、数据授权及访问角色", "异常处理、人工审核与停止机制"),
        "steps": ("绘制流程和权限边界，定义失败处理", "在测试环境制作最小可用流程", "人工验证典型与异常样本后逐步使用"),
        "outputs": ("流程图与节点职责清单", "测试环境演示和操作说明", "权限、日志、异常回退与验收文档"),
        "checks": ("未授权数据不会被第三方服务访问", "高风险决策需要人工复核", "出现异常时可暂停、回滚并追踪"),
        "boundary": "示例流程不应直接接管付款、人员管理或重要客户决策；真实上线需独立安全审查。",
    },
    {
        "slug": "localization", "tag": "出海内容",
        "name": "AI 出海内容与本地化", "icon": "◎",
        "subtitle": "用语言与文化适配，提高海外内容制作的可协同程度",
        "summary": "用于多语言网站文案、海外社媒内容、产品表达和营销素材的本地化准备。",
        "fit": "已确定目标地区、产品定位和合规要求，具备对应语言的人工审校资源。",
        "problem": "直译内容可能与当地语境不符，文化元素、商品表述和广告限制需要逐地区确认。",
        "inputs": ("目标国家、语言及渠道", "真实产品信息、术语表与品牌用语", "当地法律限制和人工审校负责人"),
        "steps": ("整理产品事实与目标市场表达规范", "生成多版本内容并请语言人员校验", "审核法规和渠道规范后制作最终素材"),
        "outputs": ("多语言内容草案与术语表", "按地区区分的文案和创意方向", "待人工确认项、禁用词及审核记录"),
        "checks": ("产品事实与价格不因翻译产生偏差", "本地敏感表达及营销合规被检查", "可按地区和版本追踪修改记录"),
        "boundary": "AI 生成的市场资料、法规摘要和翻译不得替代当地专业审核。",
    },
)

COURSE_PATHS = (
    ("AI 图像与电商设计", "掌握素材授权、图片生成、商品信息校验与导出规格。", "完成一套含审核说明的商品视觉练习。"),
    ("AI 视频与短片制作", "理解脚本、分镜、镜头一致性、剪辑及传播版权。", "完成一支标注为概念练习的短片与分镜。"),
    ("AI Agent 与工作流", "学习用 AI 完成重复任务，并在重要环节保留人工检查。", "制作一个可以随时停止的自动化演示。"),
    ("AI 出海内容表达", "熟悉多语言信息核对、文化适配与审校流程。", "制作两种语种的内容对照与审校清单。"),
    ("AI 商业机会研究", "区分产品存在、公开收费、历史经营和新进入者可行性。", "写一份说明赚钱方式、事实来源和未知风险的项目简介。"),
)

CSS = """
:root{color-scheme:light}*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;min-width:320px;color:#132038;background:#f6f8fc;font:15px/1.8 "PingFang SC","Microsoft YaHei",Inter,system-ui,sans-serif}
a{color:inherit;text-decoration:none}button{font:inherit}a:focus-visible,summary:focus-visible{outline:3px solid #77aafa;outline-offset:4px}
.wrap{width:min(1180px,calc(100% - 44px));margin:auto}
.top{background:#071120;color:#eff3ff;position:sticky;top:0;z-index:20;border-bottom:1px solid #263955;backdrop-filter:blur(14px)}
.top .row{display:flex;justify-content:space-between;align-items:center;min-height:68px;gap:24px}
.logo{font-size:22px;font-weight:850;white-space:nowrap;letter-spacing:-.04em}.logo small{margin-left:8px;letter-spacing:.13em;color:#a5b7d3;font-size:10px}
.top nav{display:flex;gap:23px;align-items:center}.top nav a{font-size:13px;color:#c6d5e8}.top nav a[aria-current="page"]{color:#bdb0ff;font-weight:800}
.mobile{display:none;position:relative}.mobile summary{border:1px solid #647390;padding:7px 13px;border-radius:11px;cursor:pointer;list-style:none}
.mobile summary::-webkit-details-marker{display:none}
.mobile nav{position:absolute;display:grid;gap:4px;right:0;top:calc(100% + 10px);background:#12233c;min-width:235px;box-shadow:0 12px 35px #0004;padding:14px;border-radius:14px}
.mobile nav a{padding:8px 10px}
.hero{background:#081223;color:#fff;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;width:650px;height:550px;right:-130px;top:-210px;background:radial-gradient(ellipse,#6e64e858,transparent 67%);pointer-events:none}
.hero .wrap{position:relative;padding:76px 0 88px}
.crumb{font-size:12px;letter-spacing:.02em;color:#adbcd7}.crumb a{text-decoration:underline;text-underline-offset:3px}
.kicker{display:inline-flex;margin-top:34px;border:1px solid #4c5d7d;background:#142542;color:#c4cbff;border-radius:80px;padding:5px 13px;letter-spacing:.08em;font-size:11px;font-weight:750}
h1{font-size:clamp(37px,5.7vw,67px);font-weight:850;line-height:1.14;letter-spacing:-.05em;max-width:920px;margin:20px 0}
.hero p{max-width:780px;color:#c1cfe3;font-size:clamp(15px,1.8vw,19px);margin:0}
.hero-links{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}
.btn{display:inline-flex;align-items:center;border-radius:12px;min-height:46px;padding:10px 18px;font-size:13px;font-weight:800;border:1px solid #667590;color:#e7ecff}
.btn.primary{background:linear-gradient(110deg,#8e70ff,#4a8fff);border-color:transparent;color:#fff}
.content{padding:48px 0 95px}.status{border:1px solid #d8d9f7;border-left:4px solid #7869d5;border-radius:12px;background:#f0edff;padding:13px 17px;color:#42466b;font-size:13px;line-height:1.8;margin-bottom:32px}
.section{margin:64px 0 0;scroll-margin-top:105px}.section:first-child{margin-top:0}
.label{font-size:11px;letter-spacing:.17em;color:#6856cc;font-weight:850}
h2{font-size:clamp(26px,3.2vw,39px);font-weight:820;letter-spacing:-.04em;line-height:1.26;color:#17253e;margin:9px 0 14px}
h3{font-size:19px;line-height:1.35;margin:0 0 9px;color:#192945}
.lead{font-size:14px;color:#60708c;max-width:820px;margin:0 0 23px}
.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.cards.four{grid-template-columns:repeat(4,minmax(0,1fr))}
.card{border-radius:17px;border:1px solid #e0e7f2;background:#fff;padding:23px;min-width:0}
.card.link{transition:transform .23s,box-shadow .23s,border-color .23s;display:block}
.card.link:hover{transform:translateY(-4px);box-shadow:0 16px 40px #23345619;border-color:#aea6ef}
.card p,.card li{color:#60708a;font-size:13px;margin:0;line-height:1.85}
.card strong{display:block;color:#6254bf;font-size:11px;letter-spacing:.08em;margin-bottom:8px}
.card .go{display:block;margin-top:20px;color:#6357c9;font-weight:800;font-size:13px}
.solution-hero .wrap{padding:34px 0 41px}
.solution-hero h1{font-size:clamp(31px,4.4vw,50px);margin:13px 0}
.solution-problem{font-weight:700;color:#273e60!important;margin:0 0 15px!important}
.solution-facts{display:grid;gap:8px;padding:12px 0;margin:13px 0 0;border-top:1px solid #e7ebf5}
.solution-facts div{display:flex;gap:10px;align-items:baseline}
.solution-facts dt{font-size:12px;color:#64738d;flex:0 0 56px}
.solution-facts dd{margin:0;font-size:13px;color:#243953;line-height:1.6}
.solution-warning{font-size:12px!important;color:#705568!important;border-top:1px solid #e7ebf5;padding-top:10px}
.solution-guide,.solution-technical{margin-top:24px}
.solution-guide summary,.solution-technical summary{min-height:44px;display:flex;align-items:center}
.solution-guide summary:focus-visible,.solution-technical summary:focus-visible{outline:3px solid #796ce8;outline-offset:3px}
.solution-guide li,.solution-technical p{color:#526580;font-size:13px;line-height:1.8}
.solution-guide a{color:#5548ac;text-decoration:underline;text-underline-offset:3px}
.solution-technical .cards{margin-top:14px}
.solution-risk{padding:19px 22px;border:1px solid #d8dfed;background:#f0f3fb;border-radius:17px;margin-top:22px}
.solution-risk h3{font-size:17px}
.solution-risk p{font-size:13px;color:#536581;line-height:1.8;margin:7px 0}
.guide-hero .wrap{padding:30px 0 38px}
.guide-hero h1{font-size:clamp(31px,4.4vw,50px);margin:13px 0}
.guide-first-action{max-width:880px;padding:26px}
.guide-first-action h3{font-size:23px}
.guide-first-action p{font-size:14px;line-height:1.75}
.guide-first-action .btn{margin-top:18px}
.guide-first-action .list{margin:15px 0 4px}
.guide-first-action .guide-privacy{font-size:12px;color:#62718b;margin-top:14px}
.guide-more{margin-top:25px;max-width:900px}
.guide-more summary{min-height:44px;display:flex;align-items:center}
.guide-more summary:focus-visible{outline:3px solid #796ce8;outline-offset:3px}
.guide-more .g2b-panel{border:0;box-shadow:none;padding:14px 0 0}
.guide-next{font-size:14px;color:#536581;margin-top:22px}
.guide-next a{color:#5548ac;text-decoration:underline;text-underline-offset:3px}
.list{padding-left:19px;margin:0}.list li{margin-bottom:8px}
.steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.step{border-top:2px solid #8572dc;padding:17px 10px 0}
.step b{display:block;color:#695cd4;font-size:12px;margin-bottom:12px}
.step p{color:#65748d;font-size:13px;margin:0}
.notice{background:#10203b;border-radius:19px;padding:29px;color:#eaf0fb}
.notice h3{color:#fff}.notice p{color:#bdc8dd;margin:0;font-size:13px}
table{width:100%;border-collapse:collapse;background:white;border:1px solid #e3e9f2;border-radius:16px;overflow:hidden}
th,td{text-align:left;padding:15px 17px;border-bottom:1px solid #e7edf5;font-size:13px;vertical-align:top}
th{background:#f0f3fb;color:#2a3d62}td{color:#60708a}tr:last-child td{border-bottom:0}
details{background:#fff;border:1px solid #e2e9f4;border-radius:14px;padding:17px 20px;margin-top:12px}
summary{cursor:pointer;color:#243956;font-weight:750}
details p,details li{color:#62718b;font-size:13px;margin:11px 0}
code,pre{font:12px/1.8 ui-monospace,Consolas,monospace}
pre{white-space:pre-wrap;word-break:break-word;background:#f0f4fa;border:1px solid #e1e8f3;padding:16px;border-radius:13px}
.footer{background:#0a1527;color:#c1cde2;padding:36px 0 43px}
.footer .row{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}
.footer p{font-size:12px;margin:5px 0;max-width:620px}
.footer nav{display:flex;gap:16px;flex-wrap:wrap;font-size:12px}.footer nav a{text-decoration:underline;text-underline-offset:4px}
@media(max-width:1050px){.top .desktop{display:none}.mobile{display:block}.cards.four{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){.wrap{width:calc(100% - 34px)}.hero .wrap{padding:42px 0 62px}.solution-hero .wrap,.guide-hero .wrap{padding:24px 0 30px}.guide-first-action{padding:19px}.cards,.cards.four,.steps{grid-template-columns:1fr}.section{margin-top:46px}.content{padding-top:32px}.card{padding:20px}.status{padding:12px}.top .row{min-height:62px}th,td{padding:12px;font-size:12px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.card.link{transition:none;transform:none!important}}
"""



# B1: visual continuity for the four already approved solution guides.
# Appended after the existing filter/guided CSS to preserve controls.
B1_SOLUTIONS_VISUAL_CSS = """
.solution-hero{isolation:isolate;background:
 radial-gradient(ellipse 43% 135% at 94% 2%,#5d4caf55,transparent 82%),
 radial-gradient(ellipse 46% 110% at 4% 100%,#2664a568,transparent 78%),
 linear-gradient(135deg,#081221 8%,#142542 75%,#1b2045)}
.solution-hero:after{content:"";position:absolute;inset:0;z-index:0;pointer-events:none;
 background:linear-gradient(#a3b9ff0d 1px,transparent 1px),linear-gradient(90deg,#a3b9ff0d 1px,transparent 1px);
 background-size:44px 44px;mask-image:linear-gradient(90deg,transparent,#0009)}
.solution-hero .wrap{position:relative;z-index:1;padding:37px 0 42px}
.solution-hero h1{margin:14px 0 12px;font-size:clamp(34px,4.5vw,55px);letter-spacing:-.05em}
.solution-hero p{font-size:clamp(14px,1.55vw,17px);line-height:1.72}
.solution-journey{display:flex;align-items:center;flex-wrap:wrap;gap:8px 14px;margin-top:20px}
.solution-journey span:not(.solution-journey-arrow){display:inline-flex;align-items:center;gap:7px;
 color:#d5dff4;font-size:12px}
.solution-journey b{min-width:27px;height:27px;padding:0 4px;display:grid;place-items:center;
 border:1px solid #a0affb61;background:#8582ff23;border-radius:9px;color:#cfcaff;font-size:10px}
.solution-journey .solution-journey-arrow{color:#8da6cf;font-size:12px}
.f21-filters{background:linear-gradient(180deg,#fff,#fcfdff);border:1px solid #dce4f1;
 border-radius:19px;box-shadow:0 12px 31px #283f7610;padding:21px}
.f21-filter-field input,.f21-filter-field select{border-radius:11px;background:#f9faff}
.f21-filter-field input:focus-visible,.f21-filter-field select:focus-visible{outline-color:#b6abff}
.f21-catalog-grid .card.link{position:relative;overflow:hidden;background:linear-gradient(180deg,#fff,#fcfdff);
 border-radius:19px;border:1px solid #dfe6f4;box-shadow:0 6px 23px #293f6e0b;
 padding:24px;transition:transform .2s,border-color .2s,box-shadow .2s}
.f21-catalog-grid .card.link:before{content:"";position:absolute;top:0;left:0;right:0;height:3px;
 background:linear-gradient(90deg,#9675f4,#6c96ff,#65caee)}
.f21-catalog-grid .card.link:nth-child(2):before{background:linear-gradient(90deg,#6f84ff,#77c0ff)}
.f21-catalog-grid .card.link:nth-child(3):before{background:linear-gradient(90deg,#2ba6c6,#63bd9f)}
.f21-catalog-grid .card.link:nth-child(4):before{background:linear-gradient(90deg,#8464d9,#6f85d8)}
.f21-catalog-grid .card.link:hover,.f21-catalog-grid .card.link:focus-visible{transform:translateY(-3px);
 border-color:#a2a8f4;box-shadow:0 17px 39px #303c921f}
.f21-catalog-grid .solution-icon{width:44px;height:44px;display:grid;place-items:center;
 border-radius:14px;background:linear-gradient(135deg,#ede7ff,#e4edff);font-size:23px;
 color:#6156c2;margin-bottom:15px}
.f21-catalog-grid .card.link:nth-child(3) .solution-icon{background:#e0f5f4;color:#258c9a}
.f21-catalog-grid .card.link:nth-child(4) .solution-icon{background:#efebff;color:#7254c8}
.f21-catalog-grid .card.link strong{color:#6962b9}
.f21-catalog-grid .card.link h3{font-size:21px;letter-spacing:-.03em}
.f21-catalog-grid .solution-facts{padding-top:15px;gap:10px}
.f21-catalog-grid .solution-facts dt{font-weight:750}
.f21-catalog-grid .go{display:flex;align-items:center;justify-content:space-between;
 background:linear-gradient(90deg,#f0edff,#eaf3ff);padding:12px 14px;
 min-height:45px;border-radius:11px;margin-top:auto}
.solution-detail-guide .cards .card,.solution-technical .cards .card{border:1px solid #dfe6f2;
 box-shadow:0 5px 20px #273c7610;background:linear-gradient(180deg,#fff,#fbfcff)}
.solution-detail-guide .g2b-trial{border-color:#d5dff1;box-shadow:0 10px 27px #344a8210}
.solution-detail-guide .solution-risk{background:linear-gradient(120deg,#eff3fc,#f5f2ff);
 border-color:#d9def1}
.solution-detail-guide .section h2{font-size:clamp(24px,3vw,35px)}
.solution-detail-guide .solution-technical{border-color:#dce3f2}
.solution-guide,.solution-technical{box-shadow:0 4px 18px #20385a09}
@media(max-width:650px){
 .solution-hero .wrap{padding:26px 0 31px}
 .solution-hero h1{font-size:clamp(31px,8vw,42px)}
 .solution-hero:after{background-size:33px 33px}
 .solution-journey{gap:7px;margin-top:17px}
 .solution-journey span:not(.solution-journey-arrow){font-size:11px}
 .solution-journey b{width:24px;height:24px}
 .f21-filters{padding:16px}
 .f21-catalog-grid .card.link{padding:21px}
}
@media(prefers-reduced-motion:reduce){.f21-catalog-grid .card.link{transition:none;transform:none!important}}
"""


def e(s: str) -> str:
    return escape(s, quote=True)


def items(seq: tuple[str, ...]) -> str:
    return '<ul class="list">' + ''.join('<li>' + e(item) + '</li>' for item in seq) + '</ul>'


def block(title: str, lines: tuple[str, ...], caption: str = "") -> str:
    return ('<article class="card"><h3>' + e(title) + '</h3>' + items(lines) + '</article>')


def section(title: str, intro: str, body: str, label: str = "使用说明") -> str:
    return ('<section class="section"' + (' id="delivery"' if label == "02 / DELIVERY PROCESS" else "")
            + '><h2>' + e(title) + '</h2>'
            + ('<p class="lead">' + e(intro) + '</p>' if intro else '')
            + body + '</section>')


def shell(path: str, title: str, description: str, label: str, body: str,
          actions: tuple[tuple[str, str], ...] = ()) -> str:
    if path not in PAGES:
        raise ValueError("Unregistered public page")
    buttons = ''.join('<a class="btn ' + ("primary" if i == 0 else "") + '" href="' + e(href) + '">' + e(text) + ' ↗</a>' for i, (text, href) in enumerate(actions))
    buttons_markup = '<div class="hero-links">' + buttons + '</div>' if buttons else ''
    current = "/" + path
    catalogue = path == "solutions/"
    guided = path in ("marketplace/", "talent/", "academy/")
    trial_page = path.startswith("solutions/") and not catalogue
    solution_route = catalogue or trial_page
    kicker = "" if solution_route or guided else '<span class="kicker">' + e(label) + '</span>'
    visual_steps = (
        '<div class="solution-journey" aria-label="企业 AI 方案的三个步骤">'
        '<span><b>01</b> 选业务问题</span><span class="solution-journey-arrow" aria-hidden="true">→</span>'
        '<span><b>02</b> 看参考做法</span><span class="solution-journey-arrow" aria-hidden="true">→</span>'
        '<span><b>03</b> 先小范围测试</span></div>'
    ) if solution_route else ''
    guide_status = {
        "marketplace/": "商机列表尚未开放，暂时不能在网站上购买服务或发布订单。",
        "talent/": "尚未开放创作者入驻或接单，暂时不能在网站上购买服务。",
        "academy/": "没有已上线的可播放课程，暂时不能在网站上购买服务。",
    }
    status = (
        '这里只展示参考方案，暂时不能在网站上购买服务或提交企业需求。'
        if solution_route else
        guide_status.get(path, '这里只提供介绍和参考，暂时不能在网站上购买服务。')
    )
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="index,follow">'
        '<title>' + e(title) + '｜见势 JIANSHI 2.0</title>'
        '<meta name="description" content="' + e(description) + '">'
        '<link rel="canonical" href="' + SITE + '/' + path + '">'
        '<meta property="og:title" content="' + e(title) + '｜见势 JIANSHI 2.0">'
        '<meta property="og:description" content="' + e(description) + '">'
        '<style>' + CSS + render_design_css() + (CATALOG_CSS if catalogue else "") + (GUIDED_CSS if guided or trial_page else "") + B1_SOLUTIONS_VISUAL_CSS + RELATED_CSS + '</style></head><body>'
        + site_header(current)
        + '<main><div class="hero' + (' solution-hero' if solution_route else ' guide-hero' if guided else '') + '"><div class="wrap">'
        '<div class="crumb"><a href="/">见势首页</a> / ' + e(label) + '</div>'
        + kicker
        + '<h1>' + e(title) + '</h1><p>' + e(description) + '</p>'
        + visual_steps + buttons_markup + '</div></div>'
        '<div class="wrap content' + (' solution-detail-guide' if trial_page else '') + '">'
        '<div class="status">' + status + '</div>'
        + body + render_related(current) + '</div></main>' + site_footer()
        + ('<script>' + CATALOG_JS + '</script>' if catalogue else '')
        + ('<script>' + GUIDED_JS + '</script>' if guided else '')
        + '</body></html>\n'
    )



# Public-facing comparisons of existing editorial concepts only. Never clients,
# signed work, results or pricing. Keep these four records tied to SOLUTIONS.
CARD_PREVIEWS = {
    "ecommerce-visual": {
        "problem": "商品上新频繁，主图和活动图总要重做。",
        "fit": "需要持续上新、常做活动的电商商家",
        "result": "主图、详情图和活动海报的样片",
        "prepare": "商品原图和可使用的素材授权",
        "risk": "AI 商品图必须核实真实外观",
    },
    "brand-video": {
        "problem": "想做品牌短视频，但脚本和画面难统一。",
        "fit": "有产品和传播目标的品牌团队",
        "result": "视频脚本、分镜与概念样片",
        "prepare": "产品信息和图片、音乐等授权",
        "risk": "概念视频不能冒充真实拍摄",
    },
    "automation": {
        "problem": "客服、工单和资料整理反复占用人力。",
        "fit": "流程稳定、能安排人工复核的团队",
        "result": "可人工接管的工作流测试演示",
        "prepare": "现有流程、数据授权和负责人员",
        "risk": "重要决策不能交由 AI 自动执行",
    },
    "localization": {
        "problem": "面向海外市场的内容，直译容易出错。",
        "fit": "有目标市场和人工审校资源的商家",
        "result": "多语言文案、术语表与待核实清单",
        "prepare": "目标语言、真实产品资料和术语",
        "risk": "必须进行当地语言与合规复核",
    },
}
if set(CARD_PREVIEWS) != {row["slug"] for row in SOLUTIONS}:
    raise RuntimeError("Solution preview set must match approved solution pages")


def solution_link(row: dict) -> str:
    category = category_for_slug(row["slug"])
    preview = CARD_PREVIEWS[row["slug"]]
    keywords = e(" ".join((row["name"], row["tag"], row["summary"],
                           row["fit"], *preview.values())))
    details = "".join(
        '<div><dt>' + e(title) + '</dt><dd>' + e(preview[key]) + '</dd></div>'
        for title, key in (("适合谁", "fit"), ("参考成果", "result"), ("先准备", "prepare"))
    )
    icon = {"ecommerce-visual": "✦", "brand-video": "▣",
            "automation": "⌘", "localization": "◎"}[row["slug"]]
    return (
        '<a class="card link" data-f21-solution data-category="' + category
        + '" data-keywords="' + keywords + '" href="/solutions/' + e(row["slug"]) + '/">'
        '<span class="solution-icon" aria-hidden="true">' + icon + '</span>'
        '<strong>' + e(row["tag"]) + '</strong>'
        '<h3>' + e(row["name"]) + '</h3>'
        '<p class="solution-problem">' + e(preview["problem"]) + '</p>'
        '<dl class="solution-facts">' + details + '</dl>'
        '<p class="solution-warning">注意：' + e(preview["risk"]) + '</p>'
        '<span class="go">查看做法和小测试 →</span></a>'
    )


def solutions_index() -> str:
    body = section(
        "选一个业务问题",
        "",
        filter_panel()
        + '<div class="cards f21-catalog-grid" id="catalog">'
        + "".join(solution_link(row) for row in SOLUTIONS) + '</div>'
        + empty_state(),
    )
    body += (
        '<details class="solution-guide">'
        '<summary>第一次尝试前，先确认这三件事</summary>'
        '<ol>'
        '<li>写清要解决的问题，以及怎样算做成了。</li>'
        '<li>核实素材使用权、系统权限和负责审核的人。</li>'
        '<li>先做一份样片或测试流程，人工检查后再考虑扩大。</li>'
        '</ol>'
        '<p>需要整理具体要求，可以打开'
        '<a href="/marketplace/brief/">本地需求草稿</a>。'
        '它不会提交订单或上传企业资料。</p></details>'
    )
    return shell(
        "solutions/", "企业能用 AI 做什么？",
        "看看四种常见业务问题能怎么处理，先比较适合谁、参考成果和需要准备的材料。",
        "企业解决方案", body,
    )


def solution_detail(row: dict) -> str:
    body = section(
        "这类 AI 能帮你做什么？",
        "",
        '<div class="cards">'
        '<article class="card"><h3>能解决什么问题？</h3><p>' + e(row["problem"]) + '</p></article>'
        '<article class="card"><h3>什么情况下适合用？</h3><p>' + e(row["fit"]) + '</p></article>'
        '</div>',
        "01 / USE CASE",
    )
    body += section(
        "先看准备材料和参考成果",
        "",
        '<div class="cards">'
        + block("企业需要准备", row["inputs"])
        + block("参考交付清单", row["outputs"]) + '</div>',
        "02 / DELIVERY PROCESS",
    )
    body += section(
        "先做一个低风险的小测试",
        "这是可以自己尝试的步骤，不是已交付的客户案例。",
        solution_trial(row["slug"]),
        "03 / SELF PRACTICE",
    )
    body += (
        '<details class="solution-technical">'
        '<summary>展开实施流程和验收检查</summary>'
        '<div class="cards">'
        + block("建议实施流程", row["steps"])
        + block("验收与质量检查", row["checks"])
        + '</div><p>实际交付范围、使用权、修改次数和验收标准，'
        '应在真实合作前由双方明确。</p></details>'
        '<aside class="solution-risk" aria-label="使用提醒">'
        '<h3>使用时要注意什么？</h3><p>' + e(row["boundary"]) + '</p>'
        '<p>这里只提供参考。不要上传未经授权的客户数据、'
        '个人信息或商业机密；本站不接收此类需求文件。</p></aside>'
    )
    return shell(
        "solutions/" + row["slug"] + "/", row["name"],
        row["summary"], "解决方案 / " + row["name"], body,
        (("查看准备材料", "#delivery"), ("返回全部方案", "/solutions/")),
    )


def marketplace_page() -> str:
    """Unopened marketplace: an immediately usable local draft, not fake jobs."""
    body = section(
        "现在可以做什么？",
        "",
        '<article class="card guide-first-action" id="request-brief">'
        '<h3>先把企业需求写清楚</h3>'
        '<p>需求说明应包含的字段：要解决的问题、预期成果、素材授权、'
        '期望完成时间、质量验收与修改标准。整理前先确认企业身份与联系人授权。</p>'
        '<a class="btn primary" href="/marketplace/brief/">打开本地需求整理器 ↗</a>'
        '<p class="guide-privacy">只在当前浏览器整理，不上传、不发布订单；关闭或刷新后内容会消失。</p>'
        '</article>',
    )
    body += (
        '<details class="guide-more">'
        '<summary>整理好了吗？做一次本地自检</summary>'
        + readiness("marketplace")
        + '</details>'
    )
    return shell(
        "marketplace/", "商机大厅（暂未开放）",
        "这里还不能发布、查找或申请企业商单；可以先把真实需求整理成一份草稿。",
        "商机大厅", body,
        (("立即整理需求", "/marketplace/brief/"),),
    )


def talent_page() -> str:
    """Unopened service-provider directory: help visitors prepare real work."""
    body = section(
        "现在可以做什么？",
        "",
        '<article class="card guide-first-action" id="portfolio">'
        '<h3>先整理一份自己的作品介绍</h3>'
        '<p>作品介绍可以怎么写？说明你会做什么、实际负责哪些部分、'
        '作品解决了什么问题，以及别人可以怎样核对。</p>'
        '<ul class="list">'
        '<li>演示作品明确标注，不能冒充客户交付。</li>'
        '<li>图片、品牌、人物和客户资料：没有授权就不公开。</li>'
        '<li>写清参考交付格式、修改范围和个人真实贡献。</li>'
        '</ul>'
        '<a class="btn primary" href="/talent/portfolio/">打开本地作品集整理器 ↗</a>'
        '<p class="guide-privacy">仅供本地整理，不创建公开人才档案；关闭或刷新后内容会消失。</p>'
        '</article>',
    )
    body += (
        '<details class="guide-more">'
        '<summary>作品准备好了？核对公开边界</summary>'
        + readiness("talent")
        + '</details>'
    )
    return shell(
        "talent/", "人才与服务商（暂未开放）",
        "尚未开放创作者入驻、作品发布或接单；可以先整理一份有授权的作品介绍。",
        "人才与服务商", body,
        (("立即整理作品", "/talent/portfolio/"),),
    )


def academy_page() -> str:
    """Unopened course catalog: retain the genuinely usable local exercises."""
    body = section(
        "选一个方向，做三项练习",
        "",
        '<div id="learning-paths">' + learning_selector() + '</div>'
        '<p class="guide-next">也可以先到 <a href="/projects/">真实公司案例</a>'
        ' 学习如何核对产品、收费方式和资料来源。</p>',
    )
    return shell(
        "academy/", "AI 技能学习（课程筹备中）",
        "没有可播放课程或报名入口；先选择一种 AI 技能，照着练习清单动手。",
        "AIGC 学院", body,
        (("查看练习清单", "#learning-paths"),),
    )


def render_pages() -> dict[str, str]:
    pages = {
        "solutions/": solutions_index(),
        "marketplace/": marketplace_page(),
        "talent/": talent_page(),
        "academy/": academy_page(),
    }
    for row in SOLUTIONS:
        key = "solutions/" + row["slug"] + "/"
        pages[key] = solution_detail(row)
    if set(pages) != set(PAGES):
        raise RuntimeError("Content page contract changed")
    for key, document in pages.items():
        expected_scripts = 1 if key in ("solutions/", "marketplace/", "talent/", "academy/") else 0
        if (document.count("<main>") != 1 or document.count("</main>") != 1
                or document.count("<style>") != 1
                or document.count("<script>") != expected_scripts
                or document.count('<link rel="canonical"') != 1
                or len(document.encode("utf-8")) > 80_000):
            raise RuntimeError("Invalid static content page: " + key)
    return pages


def publish(output: Path) -> int:
    """Offline only; write under the supplied audited public release directory."""
    pages = render_pages()
    for route, markup in pages.items():
        target = output / route / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markup, encoding="utf-8")
    return len(pages)
