"""P4.45: a single, source-governed JIANSHI2 production homepage.

Legacy P4.12E interactive gallery remains in an unpublished prototype only.
The public research/library pages retain their own audited build contract.
"""
from __future__ import annotations

from html import escape
from p442_jianshi2_live_home import STYLE, render_portal
from f21_design_tokens import render_css as render_design_css

SITE = "https://jianshi-bua.pages.dev"
TITLE = "见势｜找创业项目，看懂怎么赚钱"
DESCRIPTION = ("直接看创业案例：做什么、谁付钱、怎么赚钱、需要什么能力。"
               "所有案例仅供参考，不承诺盈利；也有中小企业 AI 应用方向。")

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
#j2 .j2-account-cta{display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;white-space:nowrap;
 min-height:40px;padding:0 15px;border:1px solid #8e86e8;border-radius:11px;
 background:linear-gradient(120deg,#7462da,#547bea);color:#fff;font-size:13px;font-weight:800;letter-spacing:.015em;
 text-decoration:none;box-shadow:0 6px 22px #6158d540}
#j2 .j2-account-cta:hover{filter:brightness(1.13);color:#fff}
#j2 .j2-account-cta:focus-visible{outline:3px solid #c8c1ff;outline-offset:3px}
#j2 .j2-mobile{display:none;margin-left:auto;position:relative}
#j2 .j2-mobile summary{list-style:none;cursor:pointer;border:1px solid #566584;border-radius:10px;min-height:44px;padding:9px 14px;font-size:13px}
#j2 .j2-mobile summary::-webkit-details-marker{display:none}
#j2 .j2-mobile-list{position:absolute;top:calc(100% + 12px);right:0;display:grid;gap:2px;width:min(280px,calc(100vw - 42px));padding:12px;background:#121d32;border:1px solid #33415b;box-shadow:0 16px 36px #0006;border-radius:13px}
#j2 .j2-mobile-list a{padding:10px;color:#e3e8f5;font-size:14px}
#j2 .j2-mobile-list a:hover{background:#263754;border-radius:7px}
#j2 .j2-top-inner{min-width:0}
#j2 .j2-mobile{flex-shrink:0}
#j2 .j2-mobile summary:focus-visible,#j2 .j2-mobile-list a:focus-visible{outline:3px solid #a9a0ff;outline-offset:2px}
#j2 .j2-mobile[open] summary{background:#253857;border-color:#9586e7}
#j2 .j2-mobile-list{max-height:min(65dvh,460px);overflow-y:auto;overscroll-behavior:contain}
@media(max-width:400px){#j2 .j2-top-inner{gap:8px}#j2 .j2-brand{font-size:18px;gap:5px}#j2 .j2-brand span{font-size:9px;letter-spacing:0}#j2 .j2-mobile summary{padding:9px 8px}#j2 .j2-account-cta{padding:0 9px;min-height:38px;font-size:12px}}

#j2 .j2-footer{padding:38px 0 44px;background:#081120;color:#cad4e6;border-top:1px solid #263753}
#j2 .j2-footer-inner{display:flex;justify-content:space-between;gap:30px;align-items:start}
#j2 .j2-footer b{font-size:18px;color:#fff}
#j2 .j2-footer p{font-size:12px;line-height:1.7;margin:9px 0}
#j2 .j2-footer-links{display:flex;flex-wrap:wrap;gap:19px}
#j2 .j2-footer-links a{font-size:13px;color:#b2c6e8;text-decoration:underline;text-underline-offset:4px}
#j2 :target{scroll-margin-top:90px}
#j2 .j2-roadmap{display:flex;gap:12px;align-items:center;justify-content:center;padding:11px 20px;background:#13243c;border-bottom:1px solid #304262;color:#cbd7eb;flex-wrap:wrap;font-size:12px}
#j2 .j2-roadmap a{color:#dad5ff;text-decoration:underline;text-underline-offset:3px;font-weight:800}
#j2 .j2-roadmap span{white-space:nowrap}
@media(max-width:600px){#j2 .j2-roadmap{font-size:11px;gap:7px;padding:10px 6px}}
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
        '<a class="j2-brand" href="/" aria-label="见势首页">见势 <span>项目研究</span></a>'
        '<nav class="j2-nav" aria-label="主要导航">'
        '<a href="#j2-opportunities">商业机会</a>'
        '<a href="#j2-solutions">企业解决方案</a>'
        '<a href="#j2-marketplace">商机大厅</a>'
        '<a href="#j2-talent">人才与服务商</a>'
        '<a href="#j2-academy">AI 学院</a>'
        '<a class="j2-nav-secondary" href="/sprint/">30 天冲刺</a>'
        '<a class="j2-nav-secondary" href="/sources/">证据与来源</a>'
        '</nav><a class="j2-account-cta" href="/account/" aria-label="进入见势注册与登录">登录 / 注册</a>'
        '<details class="j2-mobile"><summary aria-label="展开主要导航">☰ 菜单</summary>'
        '<nav class="j2-mobile-list" aria-label="移动导航">'
        '<a href="#j2-opportunities">商业机会</a>'
        '<a href="#j2-solutions">企业解决方案</a>'
        '<a href="#j2-marketplace">商机大厅</a>'
        '<a href="#j2-talent">人才与服务商</a>'
        '<a href="#j2-academy">AI 学院</a>'
        '<a href="/sprint/">30 天冲刺</a>'
        '<a href="/sources/">证据与来源</a>'
        '<a href="/account/">登录 / 注册</a>'
        '</nav></details></div></header>'
    )
    footer = (
        '<footer class="j2-footer"><div class="j2-wrap j2-footer-inner">'
        '<div><b>见势 JIANSHI</b>'
        '<p>发现机会 · 掌握 AI · 对接需求 · 创造价值。</p>'
        '<p>历史经营数据仅供研究，企业撮合、人才入驻与课程平台尚在建设中。</p></div>'
        '<nav class="j2-footer-links" aria-label="其他信息">'
        '<a href="/discover/">内容发现与筛选</a>'
        '<a href="/projects/">具名研究案例</a>'
        '<a href="/sprint/">30 天冲刺手册</a>'
        '<a href="/research/">匿名研究库</a>'
        '<a href="/validation/">证据边界</a>'
        '<a href="/privacy/">隐私政策</a>'
        '<a href="/account/">账户入口</a></nav>'
        '</div></footer>'
    )
    nav += ('<div class="j2-roadmap" aria-label="第一笔收入四步路线">'
            '<span>01　<a href="/projects/">对标</a></span><span>→</span>'
            '<span>02　<a href="/sprint/#step0">诊断</a></span><span>→</span>'
            '<span>03　<a href="/sprint/">冲刺</a></span><span>→</span>'
            '<span>04　<a href="/sprint/#week4">验证</a></span>'
            '</div>')
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
    # Keep one bounded inline script; old hash migration and nav behaviour
    # are purely client-side. No network calls, storage, tracking or private data.
    mobile_script = (
        "const menu=document.querySelector('#j2 .j2-mobile');"
        "if(menu){"
        "menu.querySelectorAll('.j2-mobile-list a').forEach(a=>"
        "a.addEventListener('click',()=>{menu.open=false;}));"
        "menu.addEventListener('keydown',e=>{"
        "if(e.key==='Escape'&&menu.open){menu.open=false;"
        "menu.querySelector('summary').focus();}});"
        "document.addEventListener('pointerdown',e=>{"
        "if(menu.open&&!menu.contains(e.target)){menu.open=false;}});"
        "window.addEventListener('resize',()=>{"
        "if(menu.open&&window.matchMedia('(min-width:1081px)').matches)"
        "menu.open=false;});"
        "}"
    )
    legacy_script = ("<script>(function(){const m="
                     + json.dumps(fragments, ensure_ascii=False, separators=(",", ":"))
                     + ";const to=m[location.hash];if(to)location.replace(to);"
                     + mobile_script
                     + "})();</script>")
    head = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="color-scheme" content="light"><meta name="generator" content="JIANSHI 2.0">'
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
