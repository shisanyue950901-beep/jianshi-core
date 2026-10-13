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
        '<span class="decision-eyebrow">适不适合你做？</span>'
        '<h2 id="decision-title">这个方向适合你吗？</h2>'
        '<p class="decision-intro">先分清原企业过去发生了什么，再判断个人能否以更小范围验证。'
        '以下属于研究判断，不是直接创业、收入或投资建议。</p>'
        f'<div class="decision-verdict" data-solo-fit="{t("fit_status")}">'
        '<span class="decision-verdict__label">一个人能试吗？</span>'
        f'<strong>{t("fit_label")}</strong>'
        '<small>已验证可直接投入创业：0 · 不意味着成功率或预测收益</small></div>'
        '<div class="decision-columns">'
        '<article><h3>可以从哪个小方向试起？</h3>'
        f'<p>{t("test_direction")}</p>'
        f'<small>{t("rationale")}</small></article>'
        '<article><h3>需要什么能力</h3>'
        f'<p>{t("skills")}</p>'
        '<h3>可能需要花哪些钱？</h3>'
        f'<p>{t("capital_uncertainty")}</p></article>'
        '</div>'
        '<div class="decision-proof" aria-label="有出处的历史证据">'
        '<h3>这家企业以前公开过什么经营资料？</h3>'
        f'<p>{t("historical_evidence")}</p>'
        f'<p><b>对应时期：</b>{t("historical_period")}</p>'
        f'<p><b>不能证明：</b>{t("historical_limit")}</p>'
        f'<a href="{t("original_source_url")}" rel="noopener noreferrer" '
        'referrerpolicy="no-referrer" target="_blank">打开原始经营来源 ↗</a>'
        '</div>'
        '<div class="decision-action" id="validation-plan">'
        '<h3>第一步可以怎么做？</h3>'
        '<ol>'
        f'<li><b>先做需求实验</b><p>{t("first_step")}</p></li>'
        f'<li><b>明确继续投入前缺少的证据</b><p>{t("blocking_evidence")}</p></li>'
        f'<li><b>继续核对原企业经营资料</b><p>{t("company_followup")}</p></li>'
        '</ol><a class="decision-workbook-link" href="#founder-workbook">填写创业验证工作单 ↓</a></div>'
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


def render_founder_workbook(case: dict) -> str:
    """Editable-by-hand, printable research prompts; never collect user data.

    Each case must pass P4.40 source and fit gates. Buyer/pricing are the
    existing reviewed editorial descriptions, not verified new sales facts.
    """
    data = decision_data(case)
    for field in ("buyer", "revenue"):
        if not isinstance(case.get(field), str) or len(case[field].strip()) < 8:
            raise RuntimeError("B1-A03: incomplete public research workbook: " + field)
    def e(value: str) -> str:
        return escape(value, quote=True)
    # Do not invite a beginner to replicate a mature company merely because
    # its historical consolidated financial statements were available.
    if data["fit_status"] == "NOT_SOLO_STARTUP":
        go_boundary = ("仅研究商业机制，不建议以此大型企业作为一人起步项目；"
                       "先提出一个不同且更小的独立客户问题，再考虑实验。")
    elif data["fit_status"] == "SKILL_GATED":
        go_boundary = ("若没有开发、运维与数据安全能力，不进入产品搭建或付费部署；"
                       "先寻找可评估的客户问题及技术合作条件。")
    else:
        go_boundary = ("仅在真实客户问题、付费意愿与交付能力出现一手证据之后，"
                       "再决定是否投入开发；没有证据就缩小范围或停止。")
    return (
        '<section class="founder-workbook section" id="founder-workbook" '
        'aria-labelledby="founder-workbook-title">'
        '<span class="decision-eyebrow">自己试一试</span>'
        '<h2 id="founder-workbook-title">把项目研究，变成四个可核实的问题</h2>'
        '<p class="workbook-intro">这是一份可直接打印或手动记录的研究工作单。'
        '平台不采集填写内容，也不保存联系人；'
        '案例资料属于历史证据，下面的提问不是实际采访或创业成功证明。</p>'
        '<div class="workbook-steps">'
        '<article class="workbook-step"><span>01 / 用户问题</span>'
        '<h3>谁可能需要这类服务？</h3>'
        f'<p><b>现有编辑研究描述：</b>{e(case["buyer"])}</p>'
        '<p>请写下你能够合法接触到的细分人群，以及他们正在怎样解决问题。</p>'
        '<div class="workbook-blank">我准备采访的客户类型／实际困扰：'
        '<span>________________________________________</span></div></article>'
        '<article class="workbook-step"><span>02 / 付费验证</span>'
        '<h3>有人真实愿意付费吗？</h3>'
        f'<p><b>现有公开收费描述：</b>{e(case["revenue"])}</p>'
        '<p>公开价格不等于成交。区分口头喜欢、愿意试用、正式报价和真实付款。</p>'
        '<div class="workbook-blank">我看到的一手付费证据／尚未知晓：'
        '<span>________________________________________</span></div></article>'
        '<article class="workbook-step"><span>03 / 资源边界</span>'
        '<h3>我是否具备必要能力与交付资源？</h3>'
        f'<p><b>可能需要的技能：</b>{e(data["skills"])}</p>'
        f'<p><b>成本不确定性：</b>{e(data["capital_uncertainty"])}</p>'
        '<p>记录真实的时间、工具费用、获客与维护投入；没有依据就填未知。</p>'
        '<div class="workbook-blank">我能验证的成本／需要补齐的能力：'
        '<span>________________________________________</span></div></article>'
        '<article class="workbook-step"><span>04 / 最小实验</span>'
        '<h3>先验证什么，什么情况下停止？</h3>'
        f'<p><b>已审核的研究第一步：</b>{e(data["first_step"])}</p>'
        f'<p><b>仍缺的关键证据：</b>{e(data["blocking_evidence"])}</p>'
        f'<p><b>继续／暂停边界：</b>{e(go_boundary)}</p>'
        '<div class="workbook-blank">我定义的可否定实验与截止条件：'
        '<span>________________________________________</span></div></article>'
        '</div>'
        '<p class="workbook-fineprint"><b>研究判断：</b>'
        f'{e(data["fit_label"])}。这不是投资建议、收益预测、'
        '平台验证过的市场需求或已完成的客户访谈。'
        '请勿把个人信息或企业敏感资料发布在公开页面。</p>'
        '</section>'
    )
