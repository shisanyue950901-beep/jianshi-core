"""P4.38: public UX counts derived from admitted cases, never raw leads.

No network. Fails closed on unreviewed companies, missing original financial
periods or attempts to treat historical ARR as a proven startup launch.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
UX = ROOT / "config/p438_public_ux_contract.json"
SOLO = ROOT / "config/p428_solo_startup_profile.json"
EVIDENCE = ROOT / "config/p424_project_research_evidence.json"
MODELS = ROOT / "config/p412a_user_product_model.json"
ALLOWED_SOURCE = {
    ("regulatory_filing","US_SEC_10K_AUDITED_CONSOLIDATED","HISTORICAL_REGULATORY_FILING"),
    ("founder_historical","FOUNDER_PUBLIC_INTERVIEW","HISTORICAL_FOUNDER_SELF_REPORT"),
    ("founder_historical","COMPANY_SELF_DISCLOSURE","HISTORICAL_COMPANY_SELF_REPORT"),
}
ALLOWED_QUICK = {"solo":"TEST_IDEA_ONLY","evidence":"EVIDENCE_ONLY","models":"EDUCATIONAL"}


def load(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result,dict):
        raise RuntimeError("Invalid P4.38 source")
    return result


def public_metrics(cases: list[dict]) -> dict:
    contract = load(UX)
    if contract.get("version") != "P438_PUBLIC_DECISION_ENTRY_V1":
        raise RuntimeError("Invalid public UX version")
    head = contract.get("public_home",{})
    if not all(isinstance(head.get(x),str) and len(head[x])>8 for x in ("headline","subhead")):
        raise RuntimeError("Missing public hero copy")
    buttons = [head.get("primary_action"),head.get("secondary_action")]
    if any(not isinstance(b,dict) or not isinstance(b.get("label"),str)
           or not isinstance(b.get("href"),str) or not b["href"].startswith("#")
           for b in buttons):
        raise RuntimeError("Unsafe decision entry link")
    paths = contract.get("quick_paths")
    if (not isinstance(paths,list) or len(paths)!=3
            or {p.get("id"):p.get("fit_status") for p in paths if isinstance(p,dict)}!=ALLOWED_QUICK):
        raise RuntimeError("Quick path contract not explicit")
    for path in paths:
        href=path.get("href")
        if not isinstance(href,str) or href not in ("#case-carrd","/projects/","#models"):
            raise RuntimeError("Quick path crosses reviewed-public boundary")
        if not all(isinstance(path.get(k),str) and len(path[k])>=5
                   for k in ("label","description")):
            raise RuntimeError("Unexplained quick path")
    solo=load(SOLO)
    ledger=load(EVIDENCE)
    models=load(MODELS)
    if (solo.get("version")!="P428_SOLO_LOW_CAPITAL_ZERO_START_V1"
            or ledger.get("version")!="P4.24_RESEARCH_EVIDENCE_V1"
            or models.get("version")!="P4.12A-USER-PRODUCT-V1"):
        raise RuntimeError("Public source schema drift")
    if not isinstance(cases,list) or not cases:
        raise RuntimeError("Missing eligible cases")
    observed = set()
    for c in cases:
        if not isinstance(c,dict) or not isinstance(c.get("id"),str) or c["id"] in observed:
            raise RuntimeError("Public case identity duplicated")
        if type(c.get("evidence_level")) is not int or c["evidence_level"] < 3:
            raise RuntimeError("Unreviewed case in public metrics")
        observed.add(c["id"])
    eligible = set()
    for row in ledger.get("additional_evidence",[]):
        triple=(row.get("tier"),row.get("source_type"),row.get("financial_status"))
        if triple not in ALLOWED_SOURCE:
            continue
        slug=row.get("id")
        period=row.get("period")
        source=row.get("source_url")
        host=urlsplit(source if isinstance(source,str) else "")
        if (not isinstance(slug,str) or slug in eligible
                or not isinstance(period,str) or len(period)<4
                or host.scheme!="https" or not host.hostname or host.username or host.password
                or not isinstance(row.get("claim"),str) or len(row["claim"])<50):
            raise RuntimeError("Original historical evidence attribution incomplete")
        eligible.add(slug)
    if eligible!=observed:
        raise RuntimeError("Public approved cases mismatch original evidence")
    assessments=solo.get("case_assessments")
    if not isinstance(assessments,list) or {a.get("id") for a in assessments} != observed:
        raise RuntimeError("Solo research profile differs from admitted cases")
    for row in assessments:
        if type(row.get("ready_for_launch")) is not bool:
            raise RuntimeError("No independently verified startup launch field")
        if row["ready_for_launch"]:
            # Until independent demand/price/channel/cost proof is represented
            # by a new signed contract, no 'launch verified' promotions.
            raise RuntimeError("Launch status cannot be promoted from founder history")
    categories=models.get("business_models")
    if (not isinstance(categories,list) or len(categories)!=6
            or len({m.get("id") for m in categories if isinstance(m,dict)})!=6):
        raise RuntimeError("Business-model category count drift")
    result={
        "approved_cases":len(eligible),
        "verified_launch":0,
        "business_models":len(categories),
        "case_ids":sorted(eligible),
    }
    if [m.get("key") for m in contract.get("metrics",[])] != [
            "approved_cases","verified_launch","business_models"]:
        raise RuntimeError("Metric mapping changed")
    return result


def entry_contract() -> dict:
    return load(UX)
