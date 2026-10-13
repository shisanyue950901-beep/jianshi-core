"""G2-C: authored cross-section reading paths and fail-closed public-page quality audit.

Never reads research sources, personal information, private artifacts or remote
resources. Audits *rendered public HTML only* and never modifies an output.
"""
from __future__ import annotations

from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

# Route -> (destination, task-specific title, accurate editorial explanation).
# All destinations must exist as PUBLIC rendered content at release time.
RELATED = {
    "/solutions/": (
        ("/marketplace/brief/", "先写清企业需求", "使用本地草稿整理目标、素材授权、验收标准，不提交客户信息。"),
        ("/academy/", "补齐 AI 基础能力", "按图像、视频、Agent 等方向选择可独立完成的练习。"),
        ("/discover/", "查找相关研究", "从企业方案延伸到公开项目、匿名模式研究与证据说明。"),
    ),
    "/solutions/ecommerce-visual/": (
        ("/marketplace/brief/", "整理视觉需求", "把产品授权、导出尺寸与修改范围写入本地需求草稿。"),
        ("/talent/", "核对作品授权", "了解设计成果如何区分概念练习与获准公开的交付作品。"),
        ("/academy/", "练习商品视觉", "选择图像设计学习路线，先做低风险样品和人工核验。"),
    ),
    "/solutions/brand-video/": (
        ("/academy/", "从分镜练习开始", "按视频学习路线整理短片脚本、镜头与版权检查。"),
        ("/marketplace/brief/", "整理视频交付说明", "本地编写时长、画幅、版本与素材许可条件。"),
        ("/solutions/ecommerce-visual/", "对照静态视觉流程", "了解多规格视觉素材与视频短片在验收上的差异。"),
    ),
    "/solutions/automation/": (
        ("/academy/", "先做 Agent 沙盒", "通过合成数据练习审批节点、异常回退与人工接管。"),
        ("/marketplace/brief/", "梳理自动化需求", "本地整理真实业务边界、责任人和停止条件。"),
        ("/solutions/localization/", "理解跨市场内容流程", "对比有人工审校要求的内容生产工作流。"),
    ),
    "/solutions/localization/": (
        ("/academy/", "做多语言审校练习", "从术语表、事实核对和语言复核开始。"),
        ("/research/agency-business/", "研究服务模式", "参考匿名数字服务模式研究，保留证据局限。"),
        ("/marketplace/brief/", "准备出海需求", "注明目标市场、内容渠道、授权与合规负责人。"),
    ),
    "/marketplace/": (
        ("/marketplace/brief/", "创建本地需求草稿", "在个人浏览器整理待核对信息，不创建订单。"),
        ("/solutions/", "选择适合的应用方案", "查看业务场景、资料输入与建议交付标准。"),
        ("/talent/", "了解作品审核边界", "先明确服务商能力和作品公开授权条件。"),
    ),
    "/talent/": (
        ("/talent/portfolio/", "建立本地作品集草稿", "区分概念练习、个人贡献和真实授权内容。"),
        ("/academy/", "寻找下一项技能练习", "根据作品缺口选一条实践路线。"),
        ("/marketplace/", "了解合作准备流程", "阅读需求审核规则，不等于可立即接单。"),
    ),
    "/academy/": (
        ("/discover/", "继续发现公开主题", "按关键词查找现有企业方案、研究与指南。"),
        ("/projects/", "学习具名案例核验", "阅读有来源约束的项目档案，不推断个人收益。"),
        ("/sources/", "了解证据判断方法", "研究之前先区分原始来源、推测和时间局限。"),
    ),
    "/discover/": (
        ("/projects/", "比较三家公司的做法", "看真实付款方、收费方式和上手门槛。"),
        ("/research/", "了解六种生意模式", "对照卖什么、谁付款，选择一项再核实。"),
        ("/sources/", "核对经营资料", "看看来源时间及尚未验证的部分。"),
    ),
}

CSS = """
.g2c-related{margin:54px 0 0;padding:25px;border-radius:20px;background:#eef2fa;border:1px solid #d7e0f0}
.g2c-related .g2c-eyebrow{font-size:11px;color:#6858ae;letter-spacing:.1em;font-weight:850}
.g2c-related h2{font-size:clamp(22px,2.8vw,30px);margin:8px 0}
.g2c-related .g2c-intro{font-size:13px;line-height:1.75;color:#60708b;margin:0 0 18px}
.g2c-links{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px}
.g2c-link{display:flex;flex-direction:column;min-height:172px;padding:19px;background:#fff;border:1px solid #dfe6f1;border-radius:14px;text-decoration:none;color:#193250;transition:border-color .18s,box-shadow .18s}
.g2c-link:hover{border-color:#9287dc;box-shadow:0 8px 24px #24325012}
.g2c-link:focus-visible{outline:3px solid #7867d6;outline-offset:3px}
.g2c-link strong{display:block;color:#253858;font-size:16px;line-height:1.5;margin:0 0 8px}
.g2c-link span{display:block;font-size:13px;color:#65768c;line-height:1.7}
.g2c-link .g2c-action{margin-top:auto;padding-top:12px;color:#5b4cb3;font-size:12px;font-weight:850}
@media(max-width:900px){.g2c-links{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.g2c-related{padding:17px;margin-top:38px}.g2c-links{grid-template-columns:1fr}.g2c-link{min-height:0;padding:16px}.g2c-related .g2c-intro{font-size:14px}}
@media(prefers-reduced-motion:reduce){.g2c-link{transition:none}}
.g2c-related-compact{margin-top:20px;padding:12px 18px}
.g2c-related-compact summary{cursor:pointer;font-size:14px;font-weight:750;color:#433984;min-height:44px;display:flex;align-items:center}
.g2c-related-compact summary:focus-visible{outline:3px solid #7867d6;outline-offset:3px}
.g2c-related-compact .g2c-links{margin:10px 0}
.g2c-related-compact .g2c-link{min-height:110px;padding:13px 15px}
.g2c-related-compact .g2c-intro{margin:4px 0 0}
"""


def e(value: str) -> str:
    return escape(value, quote=True)


def render_related(route: str) -> str:
    if route not in RELATED:
        raise ValueError("Unapproved G2-C related-content route")
    rows = RELATED[route]
    if len(rows) != 3 or len({x[0] for x in rows}) != 3:
        raise RuntimeError("Related content must have three distinct targets")
    cards = "".join(
        '<a class="g2c-link" href="' + e(target)
        + '"><strong>' + e(title) + '</strong><span>' + e(reason)
        + '</span><span class="g2c-action">继续阅读 ↗</span></a>'
        for target, title, reason in rows
    )
    if route == "/discover/":
        return (
            '<section class="g2c-related g2c-related-compact" aria-label="相关内容与下一步">'
            '<details><summary>还想继续比较？</summary>'
            '<div class="g2c-links">' + cards + '</div>'
            '<p class="g2c-intro">均为站内已有研究内容，不代表服务、课程或商单已开放；'
            '不代表在线服务、课程或商单已开放。</p></details></section>'
        )
    return (
        '<section class="g2c-related" aria-label="相关内容与下一步">'
        '<div class="g2c-eyebrow">更多选择</div>'
        '<h2>接下来，可以这样继续探索</h2>'
        '<p class="g2c-intro">根据当前主题，选择可实际阅读的公开指南。'
        '链接只指向站内已经发布的内容，不代表在线服务、课程或商单已开放。</p>'
        '<div class="g2c-links">' + cards + '</div></section>'
    )


class _ContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.main_count = 0
        self.related_count = 0
        self.related_links: list[str] = []
        self._within = 0
        self.head_title = False
        self.description = False
        self.has_h1 = False
        self.canonical = False
        self.viewport = False
        self.main_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.main_count += 1
            self.main_depth += 1
        if tag == "section" and "g2c-related" in a.get("class", "").split():
            self.related_count += 1
            self._within += 1
        elif tag == "section" and self._within:
            self._within += 1
        if tag == "a" and self._within and "g2c-link" in a.get("class", "").split():
            self.related_links.append(a.get("href", ""))
        if tag == "title":
            self.head_title = True
        if tag == "meta" and a.get("name") == "description" and a.get("content"):
            self.description = True
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = True
        if tag == "h1":
            self.has_h1 = True

    def handle_endtag(self, tag):
        if tag == "section" and self._within:
            self._within -= 1
        if tag == "main":
            self.main_depth -= 1


def audit_release(output: Path) -> dict[str, int]:
    """Mechanical publication gate, not a subjective accuracy or copyright rating."""
    if len(RELATED) != 9:
        raise RuntimeError("G2-C audited route registry unexpectedly changed")
    audited = 0
    targets: set[str] = set()
    for route, rows in RELATED.items():
        doc = output / route.lstrip("/") / "index.html"
        if not doc.is_file():
            raise RuntimeError("G2-C missing public document: " + route)
        markup = doc.read_text(encoding="utf-8")
        parsed = _ContentParser()
        parsed.feed(markup)
        if not (parsed.main_count == 1 and parsed.main_depth == 0
                and parsed.related_count == 1 and len(parsed.related_links) == 3
                and parsed.head_title and parsed.description and parsed.canonical
                and parsed.viewport and parsed.has_h1):
            raise RuntimeError("G2-C accessibility/metadata/content integrity failure: " + route)
        if set(parsed.related_links) != {row[0] for row in rows}:
            raise RuntimeError("G2-C unintended related link: " + route)
        for target, title, reason in rows:
            parsed_target = urlsplit(target)
            if (not target.startswith("/") or not target.endswith("/")
                    or parsed_target.scheme or parsed_target.netloc or "?" in target
                    or "#" in target or ".." in target or target == route
                    or not title or not reason):
                raise RuntimeError("G2-C invalid editorial target: " + route)
            page = output / target.lstrip("/") / "index.html"
            if not page.is_file():
                raise RuntimeError("G2-C broken internal link: " + target)
            if "<main" not in page.read_text(encoding="utf-8").lower():
                raise RuntimeError("G2-C destination not a content page: " + target)
            targets.add(target)
        audited += 1
    return {"audited_pages": audited, "related_links": audited * 3, "unique_targets": len(targets)}
