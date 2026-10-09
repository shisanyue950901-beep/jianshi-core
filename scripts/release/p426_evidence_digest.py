"""P4.26: deterministic, provenance-preserving Chinese digests for public cases.

Never ask an LLM to invent a metric. Read approved attributable evidence only.
Extract phrases verbatim and always preserve the report period and source tier.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Digest:
    offer: str
    buyer: str
    revenue: str
    evidence: str
    period: str
    certainty: str
    limitation: str
    next_check: str
    source_url: str


LIMITATION = {
    "regulatory_filing": "这是申报期内的公司合并历史财务；不是本期收入、单一产品利润或可复制性证明。",
    "founder_historical": "这是创始人或公司自行披露的历史经营数据，未经独立财务审计；不是当前收入。",
}


def derive_digest(case: dict) -> Digest:
    """Fail closed if the item lacks case-specific L3/L4 evidence."""
    evidence = case.get("research_evidence")
    if not isinstance(evidence, dict) or evidence.get("tier") not in LIMITATION:
        raise ValueError("不能为缺少 L3/L4 经营证据的项目生成正式摘要")
    claim = evidence.get("claim")
    if not isinstance(claim, str) or len(claim.strip()) < 40:
        raise ValueError("缺少可归属的原始经营证据摘要")
    # Keep source claim's *first clause*, without independently deriving numbers.
    proof = claim.split("；", 1)[0].strip().rstrip("。")
    if not proof:
        raise ValueError("经营依据无可用内容")
    offer, buyer, revenue = (case.get(k) for k in ("offer", "buyer", "revenue"))
    if not all(isinstance(v, str) and v.strip() for v in (offer, buyer, revenue)):
        raise ValueError("产品/客户/收费依据字段不完整")
    period = evidence.get("period")
    if not isinstance(period, str) or not period.strip():
        raise ValueError("不得在缺少报告期时发布经营指标")
    tier = evidence["tier"]
    return Digest(
        offer=offer.strip(),
        buyer=buyer.strip(),
        revenue=revenue.strip(),
        evidence=proof,
        period=period,
        certainty="监管申报（历史公司级）" if tier == "regulatory_filing" else "企业／创始人自述（未独立审计）",
        limitation=LIMITATION[tier],
        next_check=evidence["next_research"],
        source_url=evidence["source_url"],
    )
