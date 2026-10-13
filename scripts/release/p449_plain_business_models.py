"""B1: show a business model in plain Chinese before historical sample statistics.

This adapts only public /research/ mirrors AFTER the audited, no-index
appendix is generated. Does not change raw data, source anonymization,
rankings, original research, ingestion jobs or website authentication.
"""
from __future__ import annotations

from html import escape
import re

# Editorial model EXPLANATIONS, not current customer, earnings or feasibility
# claims. Cases and statistics retain their original independent audit.
MODEL_SUMMARIES = {
    "vertical-industry-saas": {
        "title": "给某个行业做软件",
        "what": "帮一个行业解决经常出现的问题，例如预约、记录或工作安排。",
        "payer": "需要这类工具的企业或个人",
        "charge": "通常按月或按年收软件使用费",
        "needs": "了解客户的问题，并负责软件开发、维护和客户支持",
        "first": "先找一种具体工作中的麻烦事，问实际使用者会不会为解决它付钱。",
    },
    "amazon-fba-niche-brand": {
        "title": "卖一类有特色的商品",
        "what": "找到细分消费需求，采购或生产商品，再通过电商渠道销售。",
        "payer": "购买商品的消费者",
        "charge": "卖商品获得销售收入；扣除各种成本后才可能有利润",
        "needs": "选品、供应商、备货、物流、退货和成本核算",
        "first": "先核实买家需求和实际运费、平台费用，不要先大量囤货。",
    },
    "digital-product-business": {
        "title": "卖模板、资料和数字工具",
        "what": "把一项具体需求做成能重复交付的模板、素材或数字商品。",
        "payer": "愿意购买成品的个人或组织",
        "charge": "按次购买、按套售卖或按授权收费",
        "needs": "确定买家需求，制作商品，确认版权和交付方式",
        "first": "先制作一份小样，给目标用户看，再了解是否有人愿意实际付款。",
    },
    "affiliate-content-site": {
        "title": "做内容，再通过推荐赚钱",
        "what": "为读者提供教程、选购建议或产品比较，帮助他们作决定。",
        "payer": "广告主或按约定结算推广费用的商家，不是每一位读者",
        "charge": "广告收入或符合条件的推广佣金",
        "needs": "原创内容、稳定读者、推广规则和持续更新",
        "first": "先确定一群有真实问题的读者，写几篇有用的内容，观察是否有人需要。",
    },
    "amazon-kdp-publishing": {
        "title": "写书并在线销售",
        "what": "制作符合平台要求的原创电子书或纸质书，面向有兴趣的读者销售。",
        "payer": "购买书籍的读者",
        "charge": "图书销售后按相应规则结算版税或销售收入",
        "needs": "选题、写作或制作、版权确认、排版和推广",
        "first": "先研究一个小题材的实际读者需求和同类书籍，再决定是否制作。",
    },
    "agency-business": {
        "title": "靠专业服务接项目",
        "what": "帮助企业或个人完成设计、内容制作、网站建设等具体任务。",
        "payer": "委托并验收服务的客户",
        "charge": "按项目、工时或持续服务合同收费",
        "needs": "明确交付成果、报价、沟通、合同与按时完成服务",
        "first": "先选一种你确实会做的服务，找潜在客户了解问题和预算。",
    },
}

STYLE = """
/* B1: clear business answers first, long historical tables only on demand. */
.model-overview{border:1px solid #dbe4f2;border-radius:20px;padding:clamp(20px,3vw,32px);background:linear-gradient(135deg,#f7f8ff,#fff);margin:18px 0 25px;color:#182842}
.model-overview .model-hint{font-size:12px;font-weight:800;color:#6254b0;letter-spacing:.02em}
.model-overview h1,.model-overview h2{font-size:clamp(26px,3.8vw,42px);line-height:1.22;margin:11px 0}
.model-overview .model-lead{font-size:16px;line-height:1.65;color:#34435b;max-width:800px}
.model-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:22px 0}
.model-facts div{min-width:0;background:#fff;border:1px solid #e5eaf4;border-radius:12px;padding:16px}
.model-facts dt{font-size:12px;color:#65748b;font-weight:700;margin-bottom:7px}
.model-facts dd{font-size:15px;line-height:1.65;color:#1e304b;margin:0;font-weight:600}
.model-first{border-left:3px solid #7a6ad6;background:#f1effe;border-radius:0 9px 9px 0;padding:13px 17px;line-height:1.7;font-size:14px}
.model-first strong{display:block;margin-bottom:5px}
.model-warning{margin:14px 0 0;color:#617187;font-size:12px;line-height:1.7}
.model-data-fold{border:1px solid #dce3f1;border-radius:15px;margin:24px 0;padding:0 18px 16px}
.model-data-fold>summary{cursor:pointer;min-height:55px;padding:17px 0;font-size:15px;font-weight:750;color:#3c3972}
.model-data-fold>summary:focus-visible{outline:3px solid #7667dc;outline-offset:3px}
.model-data-fold[open]>summary{border-bottom:1px solid #e2e8f2;margin-bottom:15px}
.model-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:18px 0}
.model-card{display:flex;flex-direction:column;gap:8px;padding:18px;border:1px solid #e0e6f0;border-radius:14px;background:#fff;color:#1c2a43;text-decoration:none;min-width:0}
.model-card:hover,.model-card:focus-visible{border-color:#796ae2;box-shadow:0 10px 25px #14264a12}
.model-card strong{font-size:19px;line-height:1.4}
.model-card span{font-size:13px;line-height:1.7;color:#54647d}
.model-card small{font-size:12px;font-weight:750;color:#6656bf;margin-top:auto;padding-top:5px}
.model-index-intro{background:transparent;border:0;padding:5px 0}
@media(max-width:720px){.model-facts,.model-grid{grid-template-columns:1fr}.model-overview{padding:18px}.model-overview .model-lead{font-size:14px}.model-facts div{padding:13px}.model-card{padding:16px}.model-data-fold{padding:0 12px 12px}}
@media print{.model-data-fold{display:none}.model-overview{break-inside:avoid}.model-facts{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""


def _e(s: str) -> str:
    return escape(s, quote=True)


def _inject_css(markup: str) -> str:
    if markup.count("</head>") != 1 or "model-overview" in markup:
        raise RuntimeError("B1 business model styling already exists or head changed")
    return markup.replace("</head>", "<style>" + STYLE + "</style></head>", 1)


def _replace_one(markup: str, pattern: str, replacement: str) -> str:
    matches = list(re.finditer(pattern, markup, flags=re.S))
    if len(matches) != 1:
        raise RuntimeError("B1 research page template anchor changed")
    m = matches[0]
    return markup[:m.start()] + replacement + markup[m.end():]


def _fold_between(markup: str, begin: str, end: str, *, sample_count: str | None = None) -> str:
    if markup.count(begin) != 1 or markup.count(end) != 1:
        raise RuntimeError("B1 research statistics boundary changed")
    start, finish = markup.index(begin), markup.index(end)
    if start >= finish:
        raise RuntimeError("B1 research statistics in wrong order")
    opening = ('<details class="model-data-fold" id="historical-stats">'
               '<summary>查看历史样本、统计数字与详细说明（展开）</summary>')
    # Existing Cloudflare snapshot gate compares public and archival
    # sample counts. Retain this ORIGINAL count only inside collapsed data.
    if sample_count is not None:
        opening += ('<p class="model-sample-count">当前分类包含 '
                    + _e(sample_count) + ' 个去重项目案例。'
                    '这些是历史匿名样本，不代表新创业者收益。</p>')
    return markup[:start] + opening + markup[start:finish] + "</details>\n" + markup[finish:]


def _detail_intro(slug: str) -> str:
    item = MODEL_SUMMARIES[slug]
    return (
        '<section class="model-overview" aria-label="这是什么生意">'
        '<a class="breadcrumb-v2" href="/research/">← 返回六种生意</a>'
        '<div class="model-hint">先看这门生意怎么做</div>'
        '<h1>' + _e(item["title"]) + '</h1>'
        '<p class="model-lead">' + _e(item["what"]) + '</p>'
        '<dl class="model-facts">'
        '<div><dt>谁付钱</dt><dd>' + _e(item["payer"]) + '</dd></div>'
        '<div><dt>怎么赚钱</dt><dd>' + _e(item["charge"]) + '</dd></div>'
        '<div><dt>需要什么</dt><dd>' + _e(item["needs"]) + '</dd></div>'
        '<div><dt>适合先做什么</dt><dd>先了解客户需求，别急着投入</dd></div></dl>'
        '<div class="model-first"><strong>第一步可以怎么做？</strong>'
        + _e(item["first"]) + '</div>'
        '<p class="model-warning">这是生意模式介绍，不代表你能直接照做赚钱。'
        '下方历史挂牌数字是第三方披露资料，见势未独立审计；'
        '它们不代表新项目的收入、利润或实际工作时间。</p>'
        '</section>'
    )


def _index_intro() -> str:
    cards = "".join(
        '<a class="model-card" href="/research/' + _e(slug) + '/">'
        '<strong>' + _e(item["title"]) + '</strong>'
        '<span>' + _e(item["what"]) + '</span>'
        '<span><b>怎么赚钱：</b>' + _e(item["charge"]) + '</span>'
        '<small>看这门生意 →</small></a>'
        for slug, item in MODEL_SUMMARIES.items()
    )
    return (
        '<section class="model-overview model-index-intro" aria-label="六种生意怎么赚钱">'
        '<div class="model-hint">从你感兴趣的生意开始</div>'
        '<h1>六种生意，先看怎么赚钱。</h1>'
        '<p class="model-lead">这些是六种常见生意模式，不是六个已验证能赚钱的项目。'
        '先了解卖什么、谁付钱，再决定要不要深入研究。</p>'
        '<div class="model-grid">' + cards + '</div>'
        '<p class="model-warning">以前企业报过的收入，不代表你也能赚到钱。'
        '详细样本数据和计算口径可以在下面展开查看。</p>'
        '</section>'
    )


def simplify(markup: str, slug: str | None = None) -> str:
    """Pure transformation of an already approved public research HTML page."""
    if slug is not None and slug not in MODEL_SUMMARIES:
        raise RuntimeError("B1 unsupported business research slug")
    markup = _inject_css(markup)
    if slug is None:
        if ('id="category-comparison"' not in markup
                or markup.count('class="research-card-v2"') < 6):
            raise RuntimeError("B1 research catalogue lost its six approved model links")
        markup = _replace_one(
            markup, r'<section class="catalog-hero-v2">.*?</section>',
            _index_intro()
        )
        return _fold_between(
            markup, '<section class="catalog-guide-v2"', '<section class="secondary-link-v2">'
        )

    if ('id="sample-scope"' not in markup or
            'id="sample-metrics"' not in markup or
            'id="sample-examples"' not in markup or
            'id="sample-boundary"' not in markup or
            'noindex,nofollow' not in markup):
        raise RuntimeError("B1 research detail missing approved statistics and privacy")
    old_count = re.search(r"当前分类包含\s*([\d,]+)\s*个去重项目案例", markup)
    if old_count is None:
        raise RuntimeError("B1 archived public sample count unavailable")
    markup = _replace_one(
        markup, r'<section class="research-hero-v2">.*?</section>',
        _detail_intro(slug)
    )
    return _fold_between(
        markup, '<nav class="research-anchor-nav-v2"',
        '<section class="detail-section-v2 related-v2">',
        sample_count=old_count.group(1)
    )
