from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class OpportunityInputs:
    github_strength: float
    market_listing_count: int
    avg_monthly_profit: float
    avg_profit_margin: float
    avg_listing_multiple: float
    solo_fit: float
    china_fit: float
    content_prior: float
    evidence_count: int

def clamp(v: float) -> float:
    return max(0.0,min(100.0,v))

def score(x: OpportunityInputs) -> dict[str,float]:
    github=clamp(x.github_strength)
    market=clamp(100*math.log(max(0,x.market_listing_count)+1)/math.log(51)) if x.market_listing_count else 0
    money=clamp(100*math.log(max(0,x.avg_monthly_profit)+1)/math.log(50001)) if x.avg_monthly_profit else 0
    margin=clamp(x.avg_profit_margin)
    multiple=clamp(max(0,x.avg_listing_multiple)*2)
    breadth=clamp(max(0,x.evidence_count)*5)
    heat=github*.55+market*.45 if github and market else max(github,market)
    business=(money*.35+margin*.25+multiple*.20+market*.20) if x.market_listing_count else min(45,10+github*.35)
    build=github*.30+clamp(x.solo_fit)*.25+clamp(x.china_fit)*.20+market*.25
    content=heat*.45+clamp(x.content_prior)*.35+breadth*.20
    return {k:round(clamp(v),2) for k,v in {
        "heat":heat,"business":business,"build":build,"content":content
    }.items()}
