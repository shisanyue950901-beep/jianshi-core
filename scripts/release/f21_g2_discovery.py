#!/usr/bin/env python3
"""F2.1 G2-A: a no-network directory of ALREADY public JIANSHI pages.

A hard-coded editorial allowlist is deliberate. Nothing here can import a
private scan, create fake listings, infer earnings, or publish CMS drafts.
"""
from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path
import re

from f21_components import site_header, site_footer
from f21_design_tokens import render_css as design_css
from p446_content_hubs import CSS as SHARED_CSS

SITE = "https://jianshi-bua.pages.dev"
ROUTE = "discover/"
# path, category, title, description, evidence/status label
ENTRIES = (
    ("/solutions/ecommerce-visual/", "solutions", "AI 电商视觉", "商品图、详情页和活动视觉：从素材授权到交付验收的步骤。", "应用指南 · 非成交服务"),
    ("/solutions/brand-video/", "solutions", "AI 视频与品牌短片", "了解脚本、分镜、概念片、版权和短视频交付边界。", "应用指南 · 非案例"),
    ("/solutions/automation/", "solutions", "AI 企业自动化", "从流程梳理、权限边界到人工复核与安全回退。", "应用指南 · 非已售产品"),
    ("/solutions/localization/", "solutions", "AI 出海内容与本地化", "目标语言、营销渠道、术语表与人工审校的业务准备。", "应用指南 · 非实际订单"),
    ("/research/vertical-industry-saas/", "research", "垂直行业 SaaS", "查看匿名行业模式的研究、局限和可核验线索。", "匿名模式研究 · 非个体收益"),
    ("/research/amazon-fba-niche-brand/", "research", "细分品牌与 FBA", "理解选品、履约、成本结构和竞争风险的研究框架。", "匿名模式研究 · 非收益承诺"),
    ("/research/digital-product-business/", "research", "数字产品业务", "产品构建、分发、内容授权与续费机制的研究线索。", "匿名模式研究 · 非收益承诺"),
    ("/research/affiliate-content-site/", "research", "联盟内容网站", "搜索内容、佣金模式、流量依赖与平台政策风险。", "匿名模式研究 · 非收益承诺"),
    ("/research/amazon-kdp-publishing/", "research", "KDP 数字出版", "了解原创版权、平台规则与低成本试验的边界。", "匿名模式研究 · 非收益承诺"),
    ("/research/agency-business/", "research", "数字服务工作室", "从客户问题、交付范围到服务流程与增长约束。", "匿名模式研究 · 非收益承诺"),
    ("/projects/plausible/", "projects", "Plausible", "以已公开资料建立的具名项目研究档案，查看来源与证据边界。", "公开项目档案 · 非投资建议"),
    ("/projects/carrd/", "projects", "Carrd", "以已公开资料整理的产品项目档案，区分事实与解读。", "公开项目档案 · 非投资建议"),
    ("/projects/nerdwallet/", "projects", "NerdWallet", "了解项目公开资料与可核验证据，不推断个人收益。", "公开项目档案 · 非投资建议"),
    ("/marketplace/", "guides", "商机大厅｜需求准备", "在真实业务入口开放前，用指南整理目标、素材、时间与验收口径。", "准备指南 · 暂无真实订单展示"),
    ("/talent/", "guides", "人才与服务商｜作品规范", "学习作品授权、技能描述、审核与公开展示的基本规则。", "准备指南 · 非服务商名录"),
    ("/academy/", "guides", "AIGC 学院｜学习路径", "图像、视频、Agent 与商业研究的学习计划和练习目标。", "学习路线 · 非已上线付费课程"),
    ("/sources/", "guides", "资料来源与证据边界", "理解研究资料来源、验证局限及不能公开的内容范围。", "透明度说明 · 不含私有原文"),
)
CATEGORIES = (
    ("all", "全部内容"),
    ("solutions", "企业方案"),
    ("research", "行业研究"),
    ("projects", "项目档案"),
    ("guides", "实用指南"),
)
CSS = """
.discover-intro{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap}
.discover-intro .lead{margin:0;max-width:740px}
.discover-search{margin:22px 0 0;padding:22px;background:#fff;border:1px solid #dce4f0;border-radius:20px;box-shadow:0 12px 30px #1727430a}
.discover-search label{font-size:13px;font-weight:800;color:#20324f;display:block;margin-bottom:8px}
.discover-search input{width:100%;min-height:51px;font:inherit;font-size:16px;color:#132038;border:1px solid #bac8dc;border-radius:11px;padding:12px 15px;outline-offset:3px}
.discover-search input:focus-visible{outline:3px solid #8c80f2;border-color:#6656ca}
.discover-controls{display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap;margin-top:17px}
.discover-filters{display:flex;gap:8px;flex-wrap:wrap}
.discover-filters button{border:1px solid #cbd5e6;background:#f4f6fb;border-radius:999px;padding:7px 13px;cursor:pointer;color:#3b4c6b;font-size:12px;font-weight:750}
.discover-filters button[aria-pressed=true]{background:#211d4d;border-color:#211d4d;color:#fff}
.discover-filters button:focus-visible,#discover-reset:focus-visible{outline:3px solid #796ce8;outline-offset:3px}
#discover-reset{border:0;background:transparent;color:#5548ac;text-decoration:underline;text-underline-offset:4px;cursor:pointer;padding:8px;font-weight:750}
.discover-meta{display:flex;gap:12px;flex-wrap:wrap;align-items:center;justify-content:space-between;margin:24px 0 14px;font-size:13px;color:#5c6a83}
.discover-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
.discover-card{display:flex;flex-direction:column;background:#fff;border:1px solid #e0e7f2;border-radius:17px;padding:23px;min-width:0;min-height:240px;transition:transform .18s,border-color .18s,box-shadow .18s}
.discover-card:hover{transform:translateY(-2px);border-color:#a49adb;box-shadow:0 14px 28px #1b2d4a12}
.discover-card[hidden]{display:none}
.discover-card .type{font-size:11px;color:#6755ba;font-weight:800;letter-spacing:.08em}
.discover-card h3{margin:12px 0;font-size:19px}
.discover-card p{margin:0;color:#66748a;font-size:13px;line-height:1.85;flex:1}
.discover-card .source-note{font-size:11px;color:#7c8495;display:block;margin-top:16px}
.discover-card .go{display:block;margin-top:12px;color:#4e45a7;font-size:13px;font-weight:800}
#discover-empty{border:1px dashed #b6c1d7;background:#fff;border-radius:16px;padding:34px 24px;text-align:center;color:#475978}
#discover-empty[hidden]{display:none}
.discover-notice{border-radius:18px;padding:24px;background:#10203b;color:#d8e4f5;margin-top:55px}
.discover-notice h2{font-size:23px;color:#fff;margin:0 0 12px}
.discover-notice p{color:#bcd0e7;font-size:13px;margin:0}
.discover-notice a{color:#dfd4ff;text-decoration:underline;text-underline-offset:4px}
@media(max-width:950px){.discover-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){.discover-grid{grid-template-columns:1fr}.discover-card{min-height:0;padding:20px}.discover-search{padding:17px}.discover-intro{display:block}}
@media(prefers-reduced-motion:reduce){.discover-card{transition:none;transform:none!important}}
"""
JS = """(function(){'use strict';
const root=document.getElementById('discover');
const input=document.getElementById('discover-query');
const controls=Array.from(root.querySelectorAll('[data-discover-category]'));
const cards=Array.from(root.querySelectorAll('[data-discover-card]'));
const counter=document.getElementById('discover-count');
const empty=document.getElementById('discover-empty');
const reset=document.getElementById('discover-reset');
const form=document.getElementById('discover-form');
let category='all';
function update(){
 const query=input.value.trim().toLocaleLowerCase('zh-CN');
 let visible=0;
 cards.forEach(card=>{
  const match=(category==='all'||card.dataset.category===category)
   &&(!query||card.dataset.search.toLocaleLowerCase('zh-CN').includes(query));
  card.hidden=!match;
  if(match)visible++;
 });
 controls.forEach(btn=>btn.setAttribute('aria-pressed',String(btn.dataset.discoverCategory===category)));
 counter.textContent='已找到 '+visible+' 条公开内容 · 共 '+cards.length+' 条';
 empty.hidden=visible!==0;
}
controls.forEach(btn=>btn.addEventListener('click',()=>{category=btn.dataset.discoverCategory;update();}));
input.addEventListener('input',update);
reset.addEventListener('click',()=>{input.value='';category='all';update();input.focus();});
form.addEventListener('submit',event=>event.preventDefault());
update();
})();"""


def e(value: str) -> str:
    return escape(value, quote=True)


def validate_entries(output: Path) -> None:
    if len(ENTRIES) != 17 or len({row[0] for row in ENTRIES}) != len(ENTRIES):
        raise RuntimeError("Discovery entry count or duplicate route invalid")
    category_names = {key for key, _ in CATEGORIES} - {"all"}
    for route, group, title, description, label in ENTRIES:
        if not re.fullmatch(r"/[a-z0-9/-]+/", route) or group not in category_names:
            raise RuntimeError("Discovery entry has unregistered route/category")
        if not all((title, description, label)) or any(len(s) > 160 for s in (title, description, label)):
            raise RuntimeError("Discovery entry invalid label length")
        if any(s in (title + description + label).lower() for s in
               ("synthetic_", "test_", "service_role", "private_notes", "listing_number")):
            raise RuntimeError("Discovery contains restricted terminology")
        page = output / route.lstrip("/") / "index.html"
        if not page.is_file():
            raise RuntimeError("Discovery source route missing: " + route)
        # Only index actual published pages, not internal workbench files or
        # redirects. No source/financial text is loaded into this directory.
        markup = page.read_text(encoding="utf-8")
        if "<!doctype html>" not in markup.lower() or "<main" not in markup.lower():
            raise RuntimeError("Discovery route is not a content page: " + route)


def render() -> str:
    counts = Counter(row[1] for row in ENTRIES)
    filters = "".join(
        '<button type="button" data-discover-category="' + key
        + '" aria-pressed="' + ("true" if key == "all" else "false") + '">'
        + e(label) + " · " + str(len(ENTRIES) if key == "all" else counts[key])
        + "</button>" for key, label in CATEGORIES
    )
    categories = dict(CATEGORIES)
    cards = "".join(
        '<a class="discover-card" data-discover-card data-category="' + e(group)
        + '" data-search="' + e(" ".join((title, description, label, categories[group]))) + '"'
        + ' href="' + e(route) + '"><span class="type">' + e(categories[group])
        + '</span><h3>' + e(title) + '</h3><p>' + e(description)
        + '</p><span class="source-note">' + e(label)
        + '</span><span class="go">阅读公开内容 ↗</span></a>'
        for route, group, title, description, label in ENTRIES
    )
    body = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="index,follow">'
        '<title>内容发现｜见势 JIANSHI 2.0</title>'
        '<meta name="description" content="统一查找见势公开的企业 AI 方案、匿名模式研究、项目档案和实用指南。">'
        '<link rel="canonical" href="' + SITE + '/discover/">'
        '<style>' + SHARED_CSS + design_css() + CSS + '</style></head><body>'
        + site_header("/discover/")
        + '<main id="discover"><section class="hero"><div class="wrap">'
        '<div class="crumb"><a href="/">见势首页</a> / 内容发现</div>'
        '<span class="kicker">G2 / PUBLIC DISCOVERY</span>'
        '<h1>从问题出发，找到可读的答案。</h1>'
        '<p>把已经公开的方案、研究、项目档案和指南放在同一个入口。'
        '不混入未审核订单、私有采集记录或不存在的课程。</p>'
        '</div></section><div class="wrap content">'
        '<section aria-labelledby="discover-title" class="section">'
        '<div class="discover-intro"><div><span class="label">01 / CONTENT DIRECTORY</span>'
        '<h2 id="discover-title">探索已公开的内容</h2>'
        '<p class="lead">按关键词或栏目筛选。所有搜索都在当前浏览器本地完成，不采集输入或发送查询请求。</p>'
        '</div></div><form id="discover-form" role="search" class="discover-search">'
        '<label for="discover-query">搜索主题、场景或项目</label>'
        '<input id="discover-query" type="search" placeholder="例如：自动化、SaaS、视频、版权"'
        ' autocomplete="off" maxlength="80">'
        '<div class="discover-controls"><div class="discover-filters" role="group" aria-label="筛选内容栏目">'
        + filters + '</div><button type="button" id="discover-reset">重置筛选</button></div></form>'
        '<div class="discover-meta"><span id="discover-count" role="status" aria-live="polite">'
        '共 ' + str(len(ENTRIES)) + ' 条公开内容</span>'
        '<span>仅收录可访问的正式公开页面，不代表实时更新或新增商机。</span></div>'
        '<div class="discover-grid" id="discover-grid">' + cards + '</div>'
        '<div id="discover-empty" role="status" hidden><h3>没有匹配的内容</h3>'
        '<p>尝试更宽泛的关键词，或清除筛选重新浏览。</p></div></section>'
        '<aside class="discover-notice" aria-label="研究与服务边界"><h2>如何判断一条信息是否值得行动？</h2>'
        '<p>先看发布日期、来源与证据类型，再判断是否适合你的实际条件。'
        '行业研究不等于个人可复制收益；方案指南不代表平台已经提供对应服务。'
        '阅读 <a href="/sources/">资料来源</a> 与 <a href="/validation/">证据边界</a>。</p>'
        '</aside></div></main>' + site_footer()
        + '<script>' + JS + '</script></body></html>\n'
    )
    if (body.count('<main ') != 1 or body.count('</main>') != 1
            or body.count('<script>') != 1 or body.count('<style>') != 1
            or len(body.encode("utf-8")) > 115_000):
        raise RuntimeError("Discovery HTML contract invalid")
    return body


def publish(output: Path) -> int:
    """Build a single reviewed directory after existing public pages exist."""
    validate_entries(output)
    dest = output / ROUTE / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(), encoding="utf-8")
    return len(ENTRIES)
