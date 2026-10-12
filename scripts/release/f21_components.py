"""F2.1 reusable G1 public layout primitives: one top nav and footer.

Only static, authored routes. The component library does not authenticate,
upload, fetch, log or accept untrusted HTML. All user-facing text is escaped.
"""
from __future__ import annotations

from html import escape

PUBLIC_NAV = (
    ("/", "首页"),
    ("/projects/", "商业机会"),
    ("/solutions/", "企业解决方案"),
    ("/marketplace/", "商机大厅"),
    ("/talent/", "人才与服务商"),
    ("/academy/", "AIGC 学院"),
)
FOOTER_NAV = (
    ("/projects/", "审核项目"),
    ("/research/", "匿名研究"),
    ("/discover/", "内容发现"),
    ("/sources/", "数据来源"),
    ("/privacy/", "隐私政策"),
)


def _e(text: str) -> str:
    return escape(text, quote=True)


def site_nav(active_route: str, *, mobile: bool = False) -> str:
    if not isinstance(active_route, str) or not active_route.startswith("/"):
        raise ValueError("Invalid active route")
    output = []
    for href, label in PUBLIC_NAV:
        current = href != "/" and (active_route == href or active_route.startswith(href))
        if href == "/" and active_route == "/":
            current = True
        attrs = ' aria-current="page"' if current else ""
        output.append('<a href="' + href + '"' + attrs + '>' + _e(label) + '</a>')
    return '<nav aria-label="' + ("移动导航" if mobile else "主要导航") + '">' + "".join(output) + "</nav>"


def site_header(active_route: str) -> str:
    return (
        '<header class="top"><div class="wrap row">'
        '<a class="logo" href="/" aria-label="见势首页">见势 <small>JIANSHI 2.0</small></a>'
        '<div class="desktop">' + site_nav(active_route) + '</div>'
        '<details class="mobile"><summary aria-label="展开导航">☰ 菜单</summary>'
        + site_nav(active_route, mobile=True) + '</details>'
        '</div></header>'
    )


def site_footer() -> str:
    links = "".join('<a href="' + path + '">' + _e(label) + "</a>" for path, label in FOOTER_NAV)
    return (
        '<footer class="footer"><div class="wrap row">'
        '<div><b>见势 JIANSHI</b><p>发现机会 · 掌握 AI · 对接需求 · 创造价值。</p>'
        '<p>商业研究不保证个人收益；企业撮合和课程能力以实际开放状态为准。</p></div>'
        '<nav aria-label="辅助信息">' + links + '</nav></div></footer>'
    )
