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
        "slug": "ecommerce-visual", "tag": "VISUAL COMMERCE",
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
        "slug": "brand-video", "tag": "MOTION & STORY",
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
        "slug": "automation", "tag": "AI OPERATIONS",
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
        "slug": "localization", "tag": "GLOBAL CONTENT",
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
    ("AI Agent 与工作流", "学习触发、工具调用、权限、错误处理及人工复核。", "构建可暂停的沙盒自动化演示。"),
    ("AI 出海内容表达", "熟悉多语言信息核对、文化适配与审校流程。", "制作两种语种的内容对照与审校清单。"),
    ("AI 商业机会研究", "区分产品存在、公开收费、历史经营和新进入者可行性。", "完成注明证据等级与研究缺口的项目简报。"),
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
@media(max-width:650px){.wrap{width:calc(100% - 34px)}.hero .wrap{padding:42px 0 62px}.cards,.cards.four,.steps{grid-template-columns:1fr}.section{margin-top:46px}.content{padding-top:32px}.card{padding:20px}.status{padding:12px}.top .row{min-height:62px}th,td{padding:12px;font-size:12px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.card.link{transition:none;transform:none!important}}
"""


def e(s: str) -> str:
    return escape(s, quote=True)


def items(seq: tuple[str, ...]) -> str:
    return '<ul class="list">' + ''.join('<li>' + e(item) + '</li>' for item in seq) + '</ul>'


def block(title: str, lines: tuple[str, ...], caption: str = "") -> str:
    return ('<article class="card"><strong>' + e(caption or "CONTENT GUIDE")
            + '</strong><h3>' + e(title) + '</h3>' + items(lines) + '</article>')


def section(title: str, intro: str, body: str, label: str = "CONTENT / EDITORIAL") -> str:
    return ('<section class="section"><span class="label">' + e(label)
            + '</span><h2>' + e(title) + '</h2><p class="lead">'
            + e(intro) + '</p>' + body + '</section>')


def shell(path: str, title: str, description: str, label: str, body: str,
          actions: tuple[tuple[str, str], ...] = ()) -> str:
    if path not in PAGES:
        raise ValueError("Unregistered public page")
    buttons = ''.join('<a class="btn ' + ("primary" if i == 0 else "") + '" href="' + e(href) + '">' + e(text) + ' ↗</a>' for i, (text, href) in enumerate(actions))
    current = "/" + path
    catalogue = path == "solutions/"
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="index,follow">'
        '<title>' + e(title) + '｜见势 JIANSHI 2.0</title>'
        '<meta name="description" content="' + e(description) + '">'
        '<link rel="canonical" href="' + SITE + '/' + path + '">'
        '<meta property="og:title" content="' + e(title) + '｜见势 JIANSHI 2.0">'
        '<meta property="og:description" content="' + e(description) + '">'
        '<style>' + CSS + render_design_css() + (CATALOG_CSS if catalogue else "") + '</style></head><body>'
        + site_header(current)
        + '<main><div class="hero"><div class="wrap">'
        '<div class="crumb"><a href="/">见势首页</a> / ' + e(label) + '</div>'
        '<span class="kicker">JIANSHI / ' + e(label) + '</span>'
        '<h1>' + e(title) + '</h1><p>' + e(description) + '</p>'
        '<div class="hero-links">' + buttons + '</div></div></div>'
        '<div class="wrap content">'
        '<div class="status"><b>内容状态：</b>这是公开的应用指南与业务准备资料。'
        '当前平台尚未开放在线委托、人才竞标、支付或课程观看；此处的流程和成果是规划与示例，不是实际客户交付记录。</div>'
        + body + '</div></main>' + site_footer()
        + ('<script>' + CATALOG_JS + '</script>' if catalogue else '')
        + '</body></html>\n'
    )


def solution_link(row: dict) -> str:
    category = category_for_slug(row["slug"])
    keywords = e(row["name"] + " " + row["tag"] + " " + row["summary"] + " " + row["fit"])
    return ('<a class="card link" data-f21-solution data-category="' + category
            + '" data-keywords="' + keywords + '" href="/solutions/' + row["slug"] + '/">'
            '<strong>' + e(row["tag"]) + '</strong><h3>' + e(row["icon"] + " " + row["name"])
            + '</h3><p>' + e(row["summary"]) + '</p>'
            '<span class="go">查看应用场景、交付与验收清单 ↗</span></a>')


def solutions_index() -> str:
    body = section(
        "先找到问题，再决定用不用 AI",
        "以下是四个可进一步研究的业务服务方向。不是已上架服务商或有报价的产品。",
        filter_panel() + '<div class="cards f21-catalog-grid">'
        + ''.join(solution_link(row) for row in SOLUTIONS) + '</div>'
        + empty_state(),
        "01 / SOLUTION CATALOG",
    )
    body += section(
        "一份有用的企业需求，需要回答什么？",
        "发布需求前先明确业务目标、可用资料、交付边界和审核人。",
        '<div class="steps">'
        '<div class="step"><b>01 · 业务问题</b><h3>描述当前阻碍</h3><p>写清使用场景、实际流程、目标用户和成功判据，不仅写“想用 AI”。</p></div>'
        '<div class="step"><b>02 · 资源与限制</b><h3>核对可用条件</h3><p>确认输入资料的授权、时间安排、企业系统权限与合规要求。</p></div>'
        '<div class="step"><b>03 · 试点验收</b><h3>先做最小成果</h3><p>从可复核的样片或沙盒流程开始，再考虑规模化交付。</p></div>'
        '</div>', "02 / DISCOVERY",
    )
    body += section("下一步如何准备合作？", "当前是参考指南，不会向平台后台提交数据。",
                    '<div class="notice"><h3>先整理需求，不必留下敏感信息</h3>'
                    '<p>需求背景、预期成果、素材授权、交付期限、验收口径和预算约束可先在本地整理。'
                    '需要的模板在商机大厅指南中；平台正式开放后才会提供经授权的提交与审核入口。</p>'
                    '<a class="btn primary" style="margin-top:20px" href="/marketplace/">查看需求准备模板 ↗</a></div>',
                    "03 / NEXT ACTION")
    return shell("solutions/", "企业 AI 解决方案", "按业务问题查找可实施的 AI 应用路径，了解典型交付物、试点步骤与风险边界。", "企业解决方案", body,
                 (("探索解决方案", "#catalog"), ("准备企业需求", "/marketplace/"))).replace('<div class="cards f21-catalog-grid">', '<div class="cards f21-catalog-grid" id="catalog">', 1)


def solution_detail(row: dict) -> str:
    body = section(
        "适合什么业务场景？", "先判断这类 AI 应用是否真正适合当前企业条件。",
        '<div class="cards">'
        '<article class="card"><strong>PAIN POINT</strong><h3>典型业务问题</h3><p>' + e(row["problem"]) + '</p></article>'
        '<article class="card"><strong>GOOD FIT</strong><h3>建议先核对的适用条件</h3><p>' + e(row["fit"]) + '</p></article>'
        '</div>', "01 / USE CASE",
    )
    body += section(
        "准备材料与实施步骤", "按具体合同和业务风险调整，不代表平台已经完成任何实际交付。",
        '<div class="cards">'
        + block("企业需要准备", row["inputs"], "INPUT / REQUIREMENTS")
        + block("建议实施流程", row["steps"], "PROCESS / PILOT") + '</div>',
        "02 / DELIVERY PROCESS",
    )
    body += section(
        "建议交付物与验收要点", "是否提供源文件、修改次数、使用权、售后或接口文档，均须在实际合作前明确。",
        '<div class="cards">'
        + block("参考交付清单", row["outputs"], "DELIVERABLES")
        + block("验收与质量检查", row["checks"], "QUALITY GATE") + '</div>',
        "03 / ACCEPTANCE",
    )
    body += section(
        "风险与下一步", "应用方案并不意味着存在某个已经验证的平台客户或服务团队。",
        '<div class="notice"><h3>使用与责任边界</h3><p>' + e(row["boundary"]) +
        '</p><p style="margin-top:13px">请避免将未经授权的客户信息、员工个人信息、'
        '商业机密或真实凭证粘贴到公开渠道；需求发布功能启用之前，不在本站采集这些材料。</p>'
        '<a class="btn primary" style="margin-top:22px" href="/marketplace/">查看企业需求模板 ↗</a></div>',
        "04 / SAFETY",
    )
    return shell("solutions/" + row["slug"] + "/", row["name"], row["subtitle"] + "。" + row["summary"],
                 "解决方案 / " + row["name"], body,
                 (("查看交付与验收", "#delivery"), ("返回方案目录", "/solutions/"))).replace(
                     '<span class="label">02 / DELIVERY PROCESS</span>',
                     '<span class="label" id="delivery">02 / DELIVERY PROCESS</span>', 1
                 )


def marketplace_page() -> str:
    body = section(
        "企业与创作者，将如何建立合作？",
        "首版计划采用人工审核及人工辅助匹配，避免把审核、支付和交付责任留成空白。",
        '<div class="steps">'
        '<div class="step"><b>01 · 企业描述问题</b><h3>明确交付</h3><p>围绕成果、使用范围、时间、约束及验收标准编写需求。</p></div>'
        '<div class="step"><b>02 · 平台审核需求</b><h3>确认真实性</h3><p>核验企业身份、需求合规、素材授权和可公开字段。</p></div>'
        '<div class="step"><b>03 · 创作者申请</b><h3>人工匹配</h3><p>基于作品和能力选择沟通对象；不展示未经授权的联系方式。</p></div>'
        '</div>', "01 / FUTURE WORKFLOW",
    )
    body += section(
        "企业需求准备模板", "可以在本地复制下面的字段，暂时无需向网站提交任何企业或个人资料。",
        '<div class="card"><h3>需求说明应包含的字段</h3>'
        '<pre>项目名称：\n行业及业务场景：\n目前的问题：\n预期交付物与数量：\n目标用户与使用渠道：\n现有资料及使用授权：\n期望完成时间：\n质量验收与修改标准：\n预算约束（可选）：\n保密、数据及审批要求：</pre>'
        '<p>仅为本地编辑参考。本站当前无上传、邮件发送、竞价或订单创建功能。</p>''<a class="btn primary" style="margin-top:18px" href="/marketplace/brief/">打开本地需求整理器 ↗</a></div>',
        "02 / REQUEST BRIEF",
    )
    body += section(
        "哪些需求不能直接进入撮合？",
        "审核阶段首先保护企业和个人，而不是追求订单数量。",
        '<div class="cards">'
        + block("发布前必须核实", ("企业身份与联系人授权", "需求描述不侵犯他人著作权或肖像权", "可公开信息与仅对匹配者展示的信息分级"), "ADMISSION RULES")
        + block("暂不支持", ("匿名要求他人提供账户、密码或内部数据", "虚构客户案例、实际收入或成交证明", "无法说明成果边界和验收责任的高风险任务"), "NOT SUPPORTED")
        + '</div>', "03 / TRUST & SAFETY",
    )
    body += section("当前开放状态", "先用业务指南帮助你准确提出问题，而不是展示不存在的订单。",
                    '<div class="notice"><h3>商机列表尚未开放</h3>'
                    '<p>当前没有经后台审核并公开发布的真实企业商单。正式上线前将完成企业认证、'
                    '角色权限、需求审核、创作者申请、状态记录及隐私授权。</p>'
                    '<a class="btn primary" style="margin-top:20px" href="/solutions/">返回解决方案目录 ↗</a></div>',
                    "04 / ROLLOUT")
    return shell("marketplace/", "商机大厅与合作流程", "为企业需求和 AI 创作者建立透明的合作路径；先提供需求模板、审核规则及未来撮合流程，不展示虚构订单。",
                 "商机大厅", body, (("查看需求准备模板", "#request-brief"), ("查看企业方案", "/solutions/"))).replace(
                     '<div class="card"><h3>需求说明应包含的字段', '<div class="card" id="request-brief"><h3>需求说明应包含的字段', 1)


def talent_page() -> str:
    body = section(
        "作品比自我介绍更有说服力", "创作者可提前整理作品与能力，但目前尚无入驻、公开作品上传或真实商单投递功能。",
        '<div class="cards">'
        + block("视觉与视频创作", ("商品或品牌视觉样片", "脚本、分镜与视频成果", "原创及素材授权说明"), "CREATIVE")
        + block("Agent 与自动化", ("沙盒演示或系统架构图", "人工审核、容错和权限说明", "明确可支持和不可支持的场景"), "AUTOMATION")
        + block("出海及商业内容", ("多语言内容对照", "事实核查及本地化审校记录", "实际样本与使用规范"), "LOCALIZATION")
        + block("商业分析与研究", ("研究假设和来源链接", "证据等级及限制", "不包含保证收益的表达"), "RESEARCH")
        + '</div>', "01 / SKILL CATEGORIES",
    )
    body += section(
        "创作者作品集参考结构", "无需晒出个人证件、真实客户的未授权信息或未经审计的营收数据。",
        '<table><thead><tr><th>模块</th><th>需要说明</th><th>展示原则</th></tr></thead><tbody>'
        '<tr><td>个人能力</td><td>技能方向、工具与可交付服务</td><td>避免夸大资历</td></tr>'
        '<tr><td>代表作品</td><td>目标、方法、前后对比、你的真实贡献</td><td>演示作品明确标注</td></tr>'
        '<tr><td>交付方式</td><td>格式、沟通、修订、验收和授权边界</td><td>双方确认范围</td></tr>'
        '<tr><td>使用权</td><td>第三方素材、客户保密和商业使用许可</td><td>没有授权就不公开</td></tr>'
        '</tbody></table>''<p style="margin-top:18px"><a class="btn primary" href="/talent/portfolio/">打开作品集本地整理器 ↗</a></p>', "02 / PORTFOLIO",
    )
    body += section(
        "未来的入驻与接单路径", "不是已经存在的账户或认证服务。",
        '<div class="steps">'
        '<div class="step"><b>01 · 准备作品</b><h3>建立能力档案</h3><p>将练习项目与真实商业交付明确区分。</p></div>'
        '<div class="step"><b>02 · 授权审核</b><h3>选择可公开信息</h3><p>按技能、作品版权和身份授权要求进行审核。</p></div>'
        '<div class="step"><b>03 · 申请合作</b><h3>匹配真实需求</h3><p>企业审核通过后按需求申请，并由双方确认合作条件。</p></div>'
        '</div>', "03 / FUTURE ONBOARDING",
    )
    body += section("当前开放状态", "我们先建设真实、可审核的供需结构。",
                    '<div class="notice"><h3>尚未开放创作者入驻</h3>'
                    '<p>目前没有“平台认证设计师”“已接单服务商”名单，也不采集简历、身份证件、'
                    '手机号或私人作品文件。你可以先根据下方学习规划完善自己的交付能力。</p>'
                    '<a class="btn primary" style="margin-top:20px" href="/academy/">查看 AIGC 学习路线 ↗</a></div>', "04 / ROLLOUT")
    return shell("talent/", "人才与服务商", "围绕作品集、技能与交付标准建设可信的 AI 创作者生态。当前可阅读准备指南，正式入驻和项目申请尚未开放。",
                 "人才与服务商", body, (("查看作品集结构", "#portfolio"), ("浏览学习路线", "/academy/"))).replace(
                     '<table><thead>', '<table id="portfolio"><thead>', 1)


def academy_page() -> str:
    cards = ''.join(
        '<article class="card"><strong>CURRICULUM PLAN · ' + str(i).zfill(2)
        + '</strong><h3>' + e(title) + '</h3><p>' + e(goal)
        + '</p><p style="margin-top:13px"><b>计划实战成果：</b>' + e(work)
        + '</p></article>'
        for i, (title, goal, work) in enumerate(COURSE_PATHS, start=1)
    )
    body = section(
        "学习方向与实战成果规划",
        "这里只公开计划课程方向与练习成果，没有伪造授课视频、讲师、学习人数或学员案例。",
        '<div class="cards">' + cards + '</div>', "01 / LEARNING PATHS",
    )
    body += section(
        "未来每门课程的结构", "优先让学员能拿出可检验的作品，而不是堆叠知识点。",
        '<div class="steps">'
        '<div class="step"><b>01 · 目标</b><h3>场景与成果</h3><p>明确适合谁、需具备什么基础，以及实际要完成什么。</p></div>'
        '<div class="step"><b>02 · 实操</b><h3>练习与拆解</h3><p>视频和配套素材待授权制作后发布，附练习步骤和常见错误。</p></div>'
        '<div class="step"><b>03 · 验收</b><h3>作品与改进</h3><p>提交前检查事实、质量、版权和边界，逐步形成个人作品集。</p></div>'
        '</div>', "02 / COURSE STRUCTURE",
    )
    body += section(
        "课程正式上线前需要完成什么？",
        "不是所有课程都需要会员收费；先把内容质量与授权边界做好。",
        '<div class="cards">'
        + block("内容制作与上架", ("由授权讲师或团队自主录制课程", "课程视频、封面和演示素材完成版权核查", "设定章节、前置知识与更新记录"), "PUBLISHING")
        + block("学习体验与安全", ("支持章节进度和作业结果归档", "不以虚构收入案例引导课程购买", "涉及个人资料时先完善账户授权与隐私设置"), "LEARNING EXPERIENCE")
        + '</div>', "03 / RELEASE RULES",
    )
    body += section(
        "现在可以做什么？",
        "没有可播放课程时，仍然可以通过独立项目研究培养判断能力。",
        '<div class="notice"><h3>自主课程制作中</h3>'
        '<p>目前没有已上线的可播放课程，也没有公开课程支付入口。'
        '先选择一条学习方向，使用公开工具练习，再到见势项目库阅读带来源的商业案例，'
        '切勿根据历史企业收益推断个人学习变现。</p>'
        '<a class="btn primary" style="margin-top:20px" href="/projects/">查看经审核的商业案例 ↗</a></div>',
        "04 / START HERE",
    )
    return shell("academy/", "AIGC 学院｜课程规划", "从 AI 视觉、视频、Agent、自动化到商业研究，按可检验的交付成果设计学习路线。课程内容将后续制作并上传。",
                 "AIGC 学院", body, (("浏览学习路径", "#learning-paths"), ("探索商业研究", "/projects/"))).replace(
                     '<div class="cards">', '<div class="cards" id="learning-paths">', 1)


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
        expected_scripts = 1 if key == "solutions/" else 0
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
