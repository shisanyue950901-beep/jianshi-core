"""P4.45: a single, source-governed JIANSHI2 production homepage.

Legacy P4.12E interactive gallery remains in an unpublished prototype only.
The public research/library pages retain their own audited build contract.
"""
from __future__ import annotations

from html import escape
from p442_jianshi2_live_home import STYLE, render_portal
from f21_design_tokens import render_css as render_design_css

SITE = "https://jianshi-bua.pages.dev"
TITLE = "见势 JIANSHI 2.0｜AI 商业机会、企业解决方案与创作者"
DESCRIPTION = ("发现经审核的 AI 商业机会研究，了解企业 AI 解决方案与创作者服务。"
               "商机撮合与 AIGC 课程正在建设，项目历史经营不代表可复制收益。")

EXTRA_STYLE = """
html{scroll-behavior:smooth;scroll-padding-top:88px}
html,body{padding:0;margin:0;background:#f7f9fd;min-width:320px}
body{overflow-x:hidden}
#j2 .j2-top{position:sticky;top:0;z-index:30;background:rgba(7,16,30,.96);color:#fff;border-bottom:1px solid #29374f;backdrop-filter:blur(15px)}
#j2 .j2-top-inner{display:flex;align-items:center;gap:27px;min-height:72px}
#j2 .j2-brand{display:inline-flex;align-items:baseline;gap:10px;white-space:nowrap;color:#fff;font-size:24px;font-weight:900;letter-spacing:-.05em}
#j2 .j2-brand span{color:#a9b5d2;letter-spacing:.09em;font-size:11px;font-weight:500}
#j2 .j2-nav{display:flex;gap:20px;align-items:center;margin-left:auto}
#j2 .j2-nav a{color:#c8d3e5;font-size:13px;white-space:nowrap}
#j2 .j2-nav a:hover,#j2 .j2-nav a:focus-visible{color:#fff}
#j2 .j2-nav .j2-nav-secondary{color:#a99eff}
#j2 .j2-mobile{display:none;margin-left:auto;position:relative}
#j2 .j2-mobile summary{list-style:none;cursor:pointer;border:1px solid #566584;border-radius:10px;min-height:44px;padding:9px 14px;font-size:13px}
#j2 .j2-mobile summary::-webkit-details-marker{display:none}
#j2 .j2-mobile-list{position:absolute;top:calc(100% + 12px);right:0;display:grid;gap:2px;width:min(280px,calc(100vw - 42px));padding:12px;background:#121d32;border:1px solid #33415b;box-shadow:0 16px 36px #0006;border-radius:13px}
#j2 .j2-mobile-list a{padding:10px;color:#e3e8f5;font-size:14px}
#j2 .j2-mobile-list a:hover{background:#263754;border-radius:7px}
#j2 .j2-footer{padding:38px 0 44px;background:#081120;color:#cad4e6;border-top:1px solid #263753}
#j2 .j2-footer-inner{display:flex;justify-content:space-between;gap:30px;align-items:start}
#j2 .j2-footer b{font-size:18px;color:#fff}
#j2 .j2-footer p{font-size:12px;line-height:1.7;margin:9px 0}
#j2 .j2-footer-links{display:flex;flex-wrap:wrap;gap:19px}
#j2 .j2-footer-links a{font-size:13px;color:#b2c6e8;text-decoration:underline;text-underline-offset:4px}
#j2 :target{scroll-margin-top:90px}
@media(max-width:1080px){#j2 .j2-nav{display:none}#j2 .j2-mobile{display:block}}
@media(max-width:760px){#j2 .j2-footer-inner{flex-direction:column;gap:15px}#j2 .j2-top-inner{min-height:64px}#j2 .j2-brand{font-size:22px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}#j2 .j2-shortcut,#j2 .j2-button{animation:none;transition:none}}
"""

def build_home(cases: list[dict]) -> str:
    """Any unsafe or unadmitted input aborts through render_portal/public_metrics."""
    portal = render_portal(cases)
    if not portal.startswith('<section id="j2"') or not portal.endswith("</section>"):
        raise RuntimeError("Unexpected JIANSHI2 portal wrapper")
    nav = (
        '<header class="j2-top"><div class="j2-wrap j2-top-inner">'
        '<a class="j2-brand" href="/" aria-label="见势首页">见势 <span>JIANSHI 2.0</span></a>'
        '<nav class="j2-nav" aria-label="主要导航">'
        '<a href="#j2-opportunities">商业机会</a>'
        '<a href="#j2-solutions">企业解决方案</a>'
        '<a href="#j2-marketplace">商机大厅</a>'
        '<a href="#j2-talent">人才与服务商</a>'
        '<a href="#j2-academy">AI 学院</a>'
        '<a class="j2-nav-secondary" href="/sources/">证据与来源</a>'
        '</nav><details class="j2-mobile"><summary aria-label="展开主要导航">☰ 菜单</summary>'
        '<nav class="j2-mobile-list" aria-label="移动导航">'
        '<a href="#j2-opportunities">商业机会</a>'
        '<a href="#j2-solutions">企业解决方案</a>'
        '<a href="#j2-marketplace">商机大厅</a>'
        '<a href="#j2-talent">人才与服务商</a>'
        '<a href="#j2-academy">AI 学院</a>'
        '<a href="/sources/">证据与来源</a>'
        '</nav></details></div></header>'
    )
    footer = (
        '<footer class="j2-footer"><div class="j2-wrap j2-footer-inner">'
        '<div><b>见势 JIANSHI</b>'
        '<p>发现机会 · 掌握 AI · 对接需求 · 创造价值。</p>'
        '<p>历史经营数据仅供研究，企业撮合、人才入驻与课程平台尚在建设中。</p></div>'
        '<nav class="j2-footer-links" aria-label="其他信息">'
        '<a href="/projects/">具名研究案例</a>'
        '<a href="/research/">匿名研究库</a>'
        '<a href="/validation/">证据边界</a>'
        '<a href="/privacy/">隐私政策</a></nav>'
        '</div></footer>'
    )
    portal = portal.replace('<section id="j2" aria-label="见势 2.0 商业机会与解决方案门户">',
                            '<section id="j2" aria-label="见势 2.0 商业机会与解决方案门户">' + nav, 1)
    portal = portal[:-len("</section>")] + footer + "</section>"
    # Old fragment bookmarks are browser-side only and cannot be handled
    # by HTTP redirects. Map them to the appropriate standalone research pages.
    fragments = {
        "#item-saas": "/research/vertical-industry-saas/",
        "#item-fba": "/research/amazon-fba-niche-brand/",
        "#item-digital": "/research/digital-product-business/",
        "#item-content": "/research/affiliate-content-site/",
        "#item-kdp": "/research/amazon-kdp-publishing/",
        "#item-agency": "/research/agency-business/",
        "#archive": "/#j2-opportunities",
        "#models": "/research/",
        "#compare": "/research/",
        "#researchLibrary": "/projects/",
        "#recommendations": "/#j2-opportunities",
        "#pick-list": "/#j2-opportunities",
    }
    # Inline only fixed destination paths; never interpolate arbitrary input.
    import json
    legacy_script = ("<script>(function(){const m="
                     + json.dumps(fragments, ensure_ascii=False, separators=(",", ":"))
                     + ";const to=m[location.hash];if(to)location.replace(to);"
                     "})();</script>")
    head = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="color-scheme" content="light">'
        '<meta name="robots" content="index,follow">'
        '<title>' + escape(TITLE) + '</title>'
        '<meta name="description" content="' + escape(DESCRIPTION, quote=True) + '">'
        '<link rel="canonical" href="' + SITE + '/">'
        '<meta property="og:type" content="website">'
        '<meta property="og:title" content="' + escape(TITLE, quote=True) + '">'
        '<meta property="og:description" content="' + escape(DESCRIPTION, quote=True) + '">'
        '<meta property="og:url" content="' + SITE + '/">'
        '<meta name="twitter:card" content="summary">'
        '<style>' + STYLE + EXTRA_STYLE + render_design_css() + '</style></head>'
    )
    rendered = head + '<body><main id="top">' + portal + '</main>' + legacy_script + '</body></html>\n'
    if (rendered.count("<main ") != 1 or rendered.count("</main>") != 1
            or rendered.count('id="j2"') != 1
            or rendered.count('<script>') != 1
            or rendered.count('data:image/webp;base64,') != 1
            or len(rendered.encode("utf-8")) > 200_000):
        raise RuntimeError("Unified home contract violation")
    return rendered
