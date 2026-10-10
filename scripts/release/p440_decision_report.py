"""P4.40: decision-ready case research cards from vetted existing sources only.

This model adds no externally inferred business claims. It merges P4.24
attributable *historical* evidence with P4.28 editorial startup suitability.
A business having historical revenue never proves a new solo project can work.
"""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from p426_evidence_digest import derive_digest
from p427_recommendation_first import load_solo_profile

STATUS_LABELS = {
    "TEST_IDEA_ONLY": "可以先研究一个低成本需求测试方向",
    "SKILL_GATED": "需要相关开发与维护能力，暂不作为新手首选",
    "NOT_SOLO_STARTUP": "成熟企业参考案例，不推荐一人低资金照搬",
}
SOURCE_LABELS = {
    ("regulatory_filing", 4): "L4 · 历史监管申报",
    ("founder_historical", 3): "L3 · 创始人／企业历史自述（未经独立审计）",
}


def decision_data(case: dict, *, profile: dict | None = None) -> dict:
    if not isinstance(case, dict) or not isinstance(case.get("id"), str):
        raise RuntimeError("P4.40: invalid company dossier")
    policy = profile if profile is not None else load_solo_profile()
    indexed = policy.get("cases") if isinstance(policy, dict) else None
    if not isinstance(indexed, dict):
        raise RuntimeError("P4.40: missing approved founder suitability")
    slug = case["id"]
    item = indexed.get(slug)
    if not isinstance(item, dict) or item.get("status") not in STATUS_LABELS:
        raise RuntimeError("P4.40: no approved decision profile for company")
    if item.get("ready_for_launch") is not False:
        raise RuntimeError("P4.40: historical operating evidence does not qualify a new startup")
    audit = case.get("research_evidence")
    level = case.get("evidence_level")
    if not isinstance(audit, dict) or (audit.get("tier"),level) not in SOURCE_LABELS:
        raise RuntimeError("P4.40: named L3/L4 original evidence required")
    digest = derive_digest(case)
    parsed = urlsplit(digest.source_url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or any(ord(char)<32 for char in digest.source_url)):
        raise RuntimeError("P4.40: original historical citation must be valid HTTPS")
    if not isinstance(digest.period,str) or len(digest.period.strip())<4:
        raise RuntimeError("P4.40: historical reporting period required")
    # The four aspects below are all from the existing approved P4.28 research
    # model. 'Skills' and 'capital' are editorial hypotheses, not audited cost.
    for key in ("tag","prototype","solo_logic","capital_logic","first_step","blocker","skills"):
        if not isinstance(item.get(key),str) or len(item[key].strip())<8:
            raise RuntimeError("P4.40: founder research field missing: " + key)
    research = audit.get("next_research")
    if not isinstance(research,str) or len(research.strip())<8:
        raise RuntimeError("P4.40: historical company's remaining research task missing")
    return {
        "slug":slug,
        "name":str(case.get("title","")).split("｜")[0],
        "fit_status":item["status"],
        "fit_label":STATUS_LABELS[item["status"]],
        "startup_ready":False,
        "test_direction":item["prototype"],
        "rationale":item["solo_logic"],
        "skills":item["skills"],
        "capital_uncertainty":item["capital_logic"],
        "first_step":item["first_step"],
        "blocking_evidence":item["blocker"],
        "historical_evidence":digest.evidence,
        "historical_period":digest.period,
        "historical_limit":digest.limitation,
        "historical_category":SOURCE_LABELS[(audit["tier"],level)],
        "original_source_url":digest.source_url,
        "company_followup":research,
        "financial_audit_status":audit["financial_status"],
    }


def render_decision_panel(data: dict) -> str:
    """Emit static HTML only, with no Javascript, trackers or network actions."""
    slug=data["slug"]
    def t(name: str) -> str:
        return escape(data[name], quote=True)
    return (
        '<section class="decision-report" id="decision-report" aria-labelledby="decision-title">'
        '<span class="decision-eyebrow">DECISION FILE / 研究决策卡</span>'
        '<h2 id="decision-title">这门生意值得你怎么研究？</h2>'
        '<p class="decision-intro">先分清原企业过去发生了什么，再判断个人能否以更小范围验证。'
        '以下属于研究判断，不是直接创业、收入或投资建议。</p>'
        f'<div class="decision-verdict" data-solo-fit="{t("fit_status")}">'
        '<span class="decision-verdict__label">一人从零适配判断</span>'
        f'<strong>{t("fit_label")}</strong>'
        '<small>已验证可直接投入创业：0 · 不意味着成功率或预测收益</small></div>'
        '<div class="decision-columns">'
        '<article><h3>启发出的可测试方向</h3>'
        f'<p>{t("test_direction")}</p>'
        f'<small>{t("rationale")}</small></article>'
        '<article><h3>需要什么能力</h3>'
        f'<p>{t("skills")}</p>'
        '<h3>资金与成本边界</h3>'
        f'<p>{t("capital_uncertainty")}</p></article>'
        '</div>'
        '<div class="decision-proof" aria-label="有出处的历史证据">'
        f'<h3>原企业的历史经营证据 · {t("historical_category")}</h3>'
        f'<p>{t("historical_evidence")}</p>'
        f'<p><b>对应时期：</b>{t("historical_period")}</p>'
        f'<p><b>不能证明：</b>{t("historical_limit")}</p>'
        f'<a href="{t("original_source_url")}" rel="noopener noreferrer" '
        'referrerpolicy="no-referrer" target="_blank">打开原始经营来源 ↗</a>'
        '</div>'
        '<div class="decision-action" id="validation-plan">'
        '<h3>个人可以如何推进验证？</h3>'
        '<ol>'
        f'<li><b>先做需求实验</b><p>{t("first_step")}</p></li>'
        f'<li><b>明确继续投入前缺少的证据</b><p>{t("blocking_evidence")}</p></li>'
        f'<li><b>继续核对原企业经营资料</b><p>{t("company_followup")}</p></li>'
        '</ol></div>'
        '<p class="decision-disclaimer">注意：原企业历史营收、收费方案或技术活跃度'
        '均不能证明新进入者能获得付费客户；具体预算、获客成本和可复制性未经独立验证。</p>'
        '</section>'
    )


def render_decision_listing(data: dict) -> str:
    """Short status on only an admitted case's public directory card."""
    return (
        '<span class="decision-mini"><b>一人起步判断：</b>'
        + escape(data["fit_label"],quote=True)
        + '<br><b>待补验证：</b>' + escape(data["blocking_evidence"],quote=True)
        + '</span>'
    )
