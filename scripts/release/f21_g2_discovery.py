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
from f21_g2c_related_quality import CSS as RELATED_CSS, render_related

SITE = "https://jianshi-bua.pages.dev"
ROUTE = "discover/"
# path, category, title, description, evidence/status label
ENTRIES = (
    ("/solutions/ecommerce-visual/", "solutions", "AI 电商做图", "制作商品图、详情页图片和活动海报。", "企业 AI 用法 · 未开放购买"),
    ("/solutions/brand-video/", "solutions", "AI 短视频制作", "了解如何制作短视频脚本、画面和样片。", "企业 AI 用法 · 未开放购买"),
    ("/solutions/automation/", "solutions", "AI 帮你处理重复工作", "看看客服辅助、整理资料和工单处理怎么开始。", "企业 AI 用法 · 未开放购买"),
    ("/solutions/localization/", "solutions", "AI 出海内容", "制作多语言内容前，要先确认翻译、审核和授权。", "企业 AI 用法 · 未开放购买"),
    ("/research/vertical-industry-saas/", "research", "行业订阅软件", "为某类行业做工具，按月或按年向客户收费。", "商业模式参考 · 非现成项目"),
    ("/research/amazon-fba-niche-brand/", "research", "电商细分品牌", "找到细分商品需求，卖产品时要核算库存、运费和退货。", "商业模式参考 · 非收益承诺"),
    ("/research/digital-product-business/", "research", "数字产品", "出售模板、资料或数字工具，先核实客户真正需要什么。", "商业模式参考 · 非收益承诺"),
    ("/research/affiliate-content-site/", "research", "内容推荐网站", "通过内容推荐相关产品，收入可能来自推广合作。", "商业模式参考 · 非收益承诺"),
    ("/research/amazon-kdp-publishing/", "research", "电子书与出版", "制作原创图书或电子书，需遵守版权和销售平台规则。", "商业模式参考 · 非收益承诺"),
    ("/research/agency-business/", "research", "为企业提供数字服务", "帮客户完成设计、内容或技术服务，按项目或服务收费。", "商业模式参考 · 非收益承诺"),
    ("/projects/plausible/", "projects", "Plausible｜网站数据分析", "卖网站统计软件，需要开发和长期运维能力。", "真实公司案例 · 非创业收益"),
    ("/projects/carrd/", "projects", "Carrd｜单页网站", "提供简洁建站工具，个人可研究小范围建站服务。", "真实公司案例 · 非创业收益"),
    ("/projects/nerdwallet/", "projects", "NerdWallet｜金融产品比较", "内容与广告合作模式，不适合个人直接照搬大型平台。", "真实公司案例 · 非创业收益"),
    ("/marketplace/", "guides", "商机大厅（暂未开放）", "先了解如何把客户需求写清楚；目前没有线上订单。", "功能说明 · 未开放接单"),
    ("/talent/", "guides", "人才与服务商（暂未开放）", "看看如何整理作品，暂时无法注册或接单。", "功能说明 · 未开放入驻"),
    ("/academy/", "guides", "AI 技能学习（筹备中）", "了解可以学的 AI 技能；目前还没有可观看的课程。", "学习方向 · 课程未开放"),
    ("/sources/", "guides", "资料从哪里来？", "查看项目资料的来源、更新时间和使用限制。", "资料说明 · 不包含私有内容"),
)

# Founder-first default filter is a grouping of existing admitted public pages.
# This grouping does not assert that the nine pages are executable startups.
CATEGORIES = (
    ("founder", "找创业方向"),
    ("projects", "真实公司案例"),
    ("research", "生意模式"),
    ("solutions", "企业用 AI"),
    ("guides", "其他"),
    ("all", "全部内容"),
)
PICK_COUNT = 9

# Short, human-readable comparisons. These are editorial explanations of
# how an existing business model operates, not new revenue or customer proof.
PROJECT_FACTS = {
    "/projects/carrd/": ("谁付钱", "付费使用高级功能的人", "怎么收费", "高级功能按年订阅"),
    "/projects/plausible/": ("谁付钱", "使用网站统计服务的站长", "怎么收费", "按订阅方案收费"),
    "/projects/nerdwallet/": ("谁付钱", "广告及商业合作伙伴", "怎么赚钱", "广告和商业合作"),
}
RESEARCH_FACTS = {
    "/research/vertical-industry-saas/": "收费方式：软件订阅",
    "/research/amazon-fba-niche-brand/": "收费方式：销售实体产品",
    "/research/digital-product-business/": "收费方式：销售数字商品",
    "/research/affiliate-content-site/": "收费方式：推广合作",
    "/research/amazon-kdp-publishing/": "收费方式：销售图书",
    "/research/agency-business/": "收费方式：按服务收费",
}

CSS = """
.discover-shell{padding-top:22px}
.discover-choice{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:0 0 16px;color:#475978;font-size:13px}
.discover-choice strong{font-weight:800;color:#21304b}
.discover-card .business-facts{display:grid;gap:7px;margin-top:12px;padding-top:13px;border-top:1px solid #edf0f6}
.discover-card .business-facts div{font-size:13px;line-height:1.5;color:#263955}
.discover-card .business-facts b{font-size:12px;color:#65748a;font-weight:700;margin-right:8px}
.discover-card .business-facts span{font-weight:650}
.discover-card .source-note{font-size:12px}
.discover-card .type{letter-spacing:0}
.discover-card h3{font-size:18px;line-height:1.4;margin:9px 0}
.discover-card p{line-height:1.6}
.discover-card .go{margin-top:auto;padding-top:15px;min-height:34px}
.discover-notice{margin-top:30px;padding:17px 22px}
.discover-notice h2{font-size:17px}
@media(max-width:650px){.discover-choice{font-size:12px}.discover-card{padding:17px}.discover-card .business-facts div{font-size:12px}}
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
let category='founder';
function update(){
 const query=input.value.trim().toLocaleLowerCase('zh-CN');
 let visible=0;
 cards.forEach(card=>{
  const match=(category==='all'||category==='founder'&&['projects','research'].includes(card.dataset.category)||card.dataset.category===category)
   &&(!query||card.dataset.search.toLocaleLowerCase('zh-CN').includes(query));
  card.hidden=!match;
  if(match)visible++;
 });
 controls.forEach(btn=>btn.setAttribute('aria-pressed',String(btn.dataset.discoverCategory===category)));
 counter.textContent=category==='founder'?'找到 '+visible+' 个可研究的案例与方向':'找到 '+visible+' 条内容';
 empty.hidden=visible!==0;
}
controls.forEach(btn=>btn.addEventListener('click',()=>{category=btn.dataset.discoverCategory;update();}));
input.addEventListener('input',()=>{if(input.value.trim())category='all';update();});
reset.addEventListener('click',()=>{input.value='';category='founder';update();input.focus();});
form.addEventListener('submit',event=>event.preventDefault());
update();
})();"""


def e(value: str) -> str:
    return escape(value, quote=True)


def validate_entries(output: Path) -> None:
    if len(ENTRIES) != 17 or len({row[0] for row in ENTRIES}) != len(ENTRIES):
        raise RuntimeError("Discovery entry count or duplicate route invalid")
    category_names = {key for key, _ in CATEGORIES} - {"all", "founder"}
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
    if sum(counts[g] for g in ("projects", "research")) != PICK_COUNT:
        raise RuntimeError("Founder-first content total drift")
    labels = dict(CATEGORIES)
    filters = "".join(
        '<button type="button" data-discover-category="' + e(key)
        + '" aria-pressed="' + ("true" if key == "founder" else "false") + '">'
        + e(label) + " · " + str(PICK_COUNT if key == "founder"
                  else len(ENTRIES) if key == "all" else counts[key])
        + "</button>" for key, label in CATEGORIES
    )
    order = {"projects": 0, "research": 1, "solutions": 2, "guides": 3}
    cards = []
    for route, group, title, description, status in sorted(
        ENTRIES, key=lambda item: order[item[1]]
    ):
        if route in PROJECT_FACTS:
            l1, v1, l2, v2 = PROJECT_FACTS[route]
            business_facts = (
                '<div class="business-facts">'
                '<div><b>' + e(l1) + '</b><span>' + e(v1) + '</span></div>'
                '<div><b>' + e(l2) + '</b><span>' + e(v2) + '</span></div></div>'
            )
        elif route in RESEARCH_FACTS:
            business_facts = '<div class="business-facts"><div><span>' + e(RESEARCH_FACTS[route]) + '</span></div></div>'
        else:
            business_facts = ""
        searchable = " ".join((title, description, status, labels[group], business_facts))
        cards.append(
            '<a class="discover-card" data-discover-card data-category="' + e(group)
            + '" data-search="' + e(searchable) + '"'
            + ' href="' + e(route) + '"><span class="type">' + e(labels[group])
            + '</span><h3>' + e(title) + '</h3><p>' + e(description)
            + '</p>' + business_facts + '<span class="source-note">' + e(status)
            + '</span><span class="go">' + (
                "看这个案例 →" if group == "projects"
                else "看看怎么做 →" if group == "research"
                else "了解一下 →") + '</span></a>'
        )
    body = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="index,follow">'
        '<title>找创业项目与赚钱方式｜见势</title>'
        '<meta name="description" content="先看真实公司案例，再比较六类商业模式。每张卡片告诉你卖什么、谁付钱、怎么收费，并明确哪些资料还不够。">'
        '<link rel="canonical" href="' + SITE + '/discover/">'
        '<style>' + SHARED_CSS + design_css() + CSS + RELATED_CSS + '</style></head><body>'
        + site_header("/discover/")
        + '<main id="discover"><section class="hero"><div class="wrap">'
        '<div class="crumb"><a href="/">见势首页</a> / 找项目</div>'
        '<h1>找创业项目，先看怎么赚钱。</h1>'
        '<p>先看真实公司案例，再看看不同生意怎么收费。历史案例不保证你照着做能赚钱。</p>'
        '</div></section><div class="wrap content discover-shell">'
        '<section aria-labelledby="discover-title" class="section">'
        '<div class="discover-intro"><div><h2 id="discover-title">按方向找</h2>'
        '<p class="lead">先看创业案例与商业模式；企业 AI 方案在独立分类里。</p>'
        '</div></div><form id="discover-form" role="search" class="discover-search">'
        '<label for="discover-query">你想找什么生意？</label>'
        '<input id="discover-query" type="search" placeholder="例如：网站、数字产品、电商、内容"'
        ' autocomplete="off" maxlength="80">'
        '<div class="discover-controls"><div class="discover-filters" role="group" aria-label="按内容方向筛选">'
        + filters + '</div><button type="button" id="discover-reset">清除筛选</button></div></form>'
        '<div class="discover-meta"><span id="discover-count" role="status" aria-live="polite">'
        '找到 ' + str(PICK_COUNT) + ' 个可研究的案例与方向</span>'
        '<span>3 个真实公司案例和 6 种商业模式，都是研究参考，不是现成商机。</span></div>'
        '<div class="discover-grid" id="discover-grid">' + "".join(cards) + '</div>'
        '<div id="discover-empty" role="status" hidden><h3>暂时没有找到</h3>'
        '<p>换个词试试，或者点击“清除筛选”。</p></div></section>'
        '<aside class="discover-notice" aria-label="重要说明"><h2>这里的案例可以直接照做吗？</h2>'
        '<p>不能这样保证。先了解项目怎么收费，再核实自己能不能找到客户、需要花多少钱。'
        '想看出处，可以打开 <a href="/sources/">资料来源</a> 和 '
        '<a href="/validation/">更多说明</a>。</p>'
        '</aside>' + render_related('/discover/') + '</div></main>' + site_footer()
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
