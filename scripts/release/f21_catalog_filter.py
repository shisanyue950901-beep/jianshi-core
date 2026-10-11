"""F2.1 accessible local-only filtering for reviewed solution categories.

This UI never sends queries anywhere, never stores history, never claims
newly available services, and only filters the four reviewed editorial cards.
"""
from __future__ import annotations

from html import escape

CATEGORIES = (
    ("all", "全部方向"),
    ("creative", "视觉与视频"),
    ("automation", "企业自动化"),
    ("global", "出海内容"),
)
BY_SLUG = {
    "ecommerce-visual": "creative",
    "brand-video": "creative",
    "automation": "automation",
    "localization": "global",
}

CSS = """
.f21-filters{display:grid;grid-template-columns:1fr auto auto;align-items:end;gap:12px;padding:19px;
  border:1px solid var(--js21-border);border-radius:16px;background:#fff;margin-bottom:20px}
.f21-filter-field{display:flex;flex-direction:column;gap:7px;min-width:0}
.f21-filter-field label{color:#364866;font-size:12px;font-weight:750}
.f21-filter-field input,.f21-filter-field select{width:100%;min-height:44px;border:1px solid #cbd5e5;
  background:#fff;color:#16253c;border-radius:10px;padding:9px 12px;font:inherit;font-size:14px}
.f21-filter-field input:focus-visible,.f21-filter-field select:focus-visible{
  outline:3px solid #a9b8f9;outline-offset:2px}
.f21-filters button{border:1px solid #bbc6df;border-radius:10px;min-height:44px;background:#f7f8fe;
  color:#344665;font-weight:750;padding:8px 15px;cursor:pointer}
.f21-resultline{font-size:12px;color:#677893;margin:10px 0 16px}
.f21-empty{padding:30px;text-align:center;background:#fff;border:1px dashed #adbdd9;border-radius:15px;color:#576781}
.f21-catalog-grid [hidden],.f21-empty[hidden]{display:none!important}
@media(max-width:680px){.f21-filters{grid-template-columns:1fr;align-items:stretch;padding:15px}
  .f21-filters button{width:100%}}
@media(prefers-reduced-motion:reduce){.f21-catalog-grid .card{transition:none!important;transform:none!important}}
"""

# Do not evaluate or insert HTML from input values. Query and tags are plain
# strings from reviewed authored content, not remote databases.
JS = r"""
(function(){
  'use strict';
  const root=document.getElementById('f21-solutions-search');
  const grid=document.getElementById('catalog');
  if(!root||!grid)return;
  const query=root.querySelector('#f21-search');
  const kind=root.querySelector('#f21-category');
  const reset=root.querySelector('#f21-reset');
  const feedback=document.getElementById('f21-results');
  const empty=document.getElementById('f21-empty');
  const cards=Array.from(grid.querySelectorAll('[data-f21-solution]'));
  const apply=function(){
    const q=query.value.trim().toLocaleLowerCase();
    const category=kind.value;
    let visible=0;
    cards.forEach(function(card){
      const matchesText=!q||(card.getAttribute('data-keywords')||'').toLocaleLowerCase().includes(q);
      const matchesCategory=category==='all'||card.getAttribute('data-category')===category;
      const show=matchesText&&matchesCategory;
      card.hidden=!show;
      if(show)visible+=1;
    });
    feedback.textContent='已找到 '+String(visible)+' / '+String(cards.length)+' 个应用方向';
    empty.hidden=visible!==0;
  };
  query.addEventListener('input',apply);
  kind.addEventListener('change',apply);
  reset.addEventListener('click',function(){
    query.value='';
    kind.value='all';
    apply();
    query.focus();
  });
  apply();
}());
"""


def filter_panel() -> str:
    options = "".join(
        '<option value="' + code + '">' + escape(label) + '</option>'
        for code, label in CATEGORIES
    )
    return (
        '<section class="f21-filters" id="f21-solutions-search" aria-label="筛选企业 AI 解决方案">'
        '<div class="f21-filter-field"><label for="f21-search">搜索应用方向</label>'
        '<input id="f21-search" type="search" autocomplete="off" maxlength="90"'
        ' placeholder="如：电商、短视频、自动化、海外营销"></div>'
        '<div class="f21-filter-field"><label for="f21-category">业务类别</label>'
        '<select id="f21-category">' + options + '</select></div>'
        '<button type="button" id="f21-reset">清除筛选</button></section>'
        '<p class="f21-resultline" id="f21-results" aria-live="polite">'
        '当前收录 4 个编辑审核过的应用方向，非真实客户订单。</p>'
    )


def empty_state() -> str:
    return ('<p class="f21-empty" id="f21-empty" hidden role="status">'
            '没有找到符合条件的应用方向。请尝试其他关键词，或点击“清除筛选”。</p>')


def category_for_slug(slug: str) -> str:
    return BY_SLUG[slug]
