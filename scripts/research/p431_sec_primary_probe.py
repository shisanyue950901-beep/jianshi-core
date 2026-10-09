#!/usr/bin/env python3
"""P4.31 SEC EDGAR public API: on-demand, minimally scoped, private R2 candidate collection.

Two fixed SEC API endpoints for ONE reviewed CIK, or two local fixture files.
No scheduling, auto-admission, model-generated claims, third-party redirects,
marketplace extraction, credentials, Supabase or public writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "config/p430_company_identity_registry.json"
HOST = "data.sec.gov"
MAX_RESPONSE = 16 * 1024 * 1024
TIMEOUT = 8
METRIC_TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues", "SalesRevenueNet", "NetIncomeLoss",
)
CIK_WHITELIST = {"nerdwallet": "0001625278"}


class RefuseRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("SEC API redirected; do not follow")


def load_identity(case_id: str) -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("version") != "P430_PRIVATE_IDENTITY_REVIEW_V1":
        raise ValueError("Unreviewed identity registry")
    company = next((x for x in data.get("companies", []) if x.get("id") == case_id), None)
    cik = CIK_WHITELIST.get(case_id)
    if (not company or not cik or company.get("sec_cik") != cik
            or company.get("official_domain") != "nerdwallet.com"
            or company.get("legal_entity_status") != "UNVERIFIED"):
        raise ValueError("CIK not permitted or editorial/legal identity drift")
    return company


def sec_url(endpoint: str, cik: str) -> str:
    if cik != CIK_WHITELIST["nerdwallet"]:
        raise ValueError("Unapproved CIK")
    if endpoint == "submissions":
        return f"https://{HOST}/submissions/CIK{cik}.json"
    if endpoint == "companyfacts":
        return f"https://{HOST}/api/xbrl/companyfacts/CIK{cik}.json"
    raise ValueError("Unapproved SEC resource")


def validated_contact(raw: str) -> str:
    if not isinstance(raw, str) or not re.fullmatch(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{3,180}\.[A-Za-z]{2,20}", raw):
        raise ValueError("Real contact email is required to identify automated SEC requests")
    return raw


def get_sec_json(url: str, contact: str) -> tuple[dict, str]:
    validated_contact(contact)
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != HOST or parsed.username
            or parsed.password or parsed.port not in (None, 443)
            or parsed.query or parsed.fragment
            or parsed.path not in ("/submissions/CIK0001625278.json",
                                   "/api/xbrl/companyfacts/CIK0001625278.json")):
        raise ValueError("SEC request denied outside fixed allowlist")
    req = Request(url, headers={
        "User-Agent": f"JianShiResearch ({contact})",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
    })
    opener = build_opener(RefuseRedirect())
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            if response.status != 200 or "json" not in response.headers.get("Content-Type", "").lower():
                raise ValueError("Unexpected SEC response")
            if response.geturl() != url:
                raise ValueError("SEC response URL drift")
            raw = response.read(MAX_RESPONSE + 1)
    except HTTPError as exc:
        # Never retry a 403/429 via proxy or alternate identity.
        raise RuntimeError(f"SEC_ACCESS_STOP_{exc.code}") from None
    if len(raw) > MAX_RESPONSE:
        raise ValueError("SEC response size exceeds budget")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Malformed SEC object")
    return data, hashlib.sha256(raw).hexdigest()


def fixture_json(path: Path) -> tuple[dict, str]:
    if not path.is_file() or path.stat().st_size > MAX_RESPONSE:
        raise ValueError("Invalid/off-budget local SEC fixture")
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Invalid SEC fixture document")
    return data, hashlib.sha256(raw).hexdigest()


def _valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _filings(submissions: dict, cik: str, brand: str) -> list[dict]:
    if str(submissions.get("cik", "")).zfill(10) != cik:
        raise ValueError("CIK mismatch in filings")
    name = submissions.get("name")
    if not isinstance(name, str) or brand.lower() not in name.lower():
        raise ValueError("Issuer name does not match reviewed brand")
    recent = (submissions.get("filings") or {}).get("recent") or {}
    keys = ("accessionNumber", "form", "filingDate", "reportDate", "primaryDocument")
    if not all(isinstance(recent.get(key), list) for key in keys):
        raise ValueError("Incomplete SEC filing arrays")
    lengths = [len(recent[k]) for k in keys]
    if len(set(lengths)) != 1 or lengths[0] > 3000:
        raise ValueError("Unsafe/inconsistent SEC submission columns")
    result = []
    for accn, form, filed, period, primary in zip(*(recent[k] for k in keys)):
        if form not in ("10-K", "10-K/A") or not _valid_date(filed) or not _valid_date(period):
            continue
        if (not isinstance(accn, str) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accn)
                or not isinstance(primary, str)
                or not re.fullmatch(r"[A-Za-z0-9._-]{1,140}", primary)):
            continue
        result.append({
            "accession_number": accn, "form": form,
            "filed_on": filed, "period_end": period,
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn.replace('-', '')}/{primary}",
        })
    result.sort(key=lambda row: (row["period_end"], row["filed_on"]), reverse=True)
    return result[:3]


def _observations(companyfacts: dict, cik: str, brand: str, filing: dict) -> list[dict]:
    if str(companyfacts.get("cik", "")).zfill(10) != cik:
        raise ValueError("CIK mismatch in XBRL facts")
    if brand.lower() not in str(companyfacts.get("entityName", "")).lower():
        raise ValueError("XBRL issuer identity mismatch")
    namespace = (companyfacts.get("facts") or {}).get("us-gaap") or {}
    if not isinstance(namespace, dict):
        raise ValueError("Unexpected XBRL namespace")
    results = []
    for tag in METRIC_TAGS:
        obj = namespace.get(tag)
        if not isinstance(obj, dict):
            continue
        units = obj.get("units") or {}
        if not isinstance(units, dict):
            continue
        rows = units.get("USD") or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            start, end = row.get("start"), row.get("end")
            if not (_valid_date(start) and _valid_date(end)):
                continue
            days = (date.fromisoformat(end) - date.fromisoformat(start)).days
            val = row.get("val")
            if (row.get("accn") != filing["accession_number"]
                    or row.get("form") not in ("10-K", "10-K/A")
                    or row.get("fp") != "FY"
                    or end != filing["period_end"]
                    or row.get("filed") != filing["filed_on"]
                    or not 330 <= days <= 390
                    or type(val) not in (int, float)
                    or not -(10**14) < val < 10**14):
                continue
            results.append({
                "taxonomy": "us-gaap", "tag": tag, "val": val, "unit": "USD",
                "period_start": start, "period_end": end,
                "form": row["form"], "accession_number": row["accn"],
                "filed_on": row["filed"],
                "verification": "STRUCTURAL_MATCH_ONLY_NOT_AUDITED_BY_JIANSHI",
            })
            if len(results) >= 24:
                return results
    return results


def triage(case_id: str, submissions: dict, facts: dict, hashes: dict) -> dict:
    identity = load_identity(case_id)
    cik = identity["sec_cik"]
    filings = _filings(submissions, cik, identity["brand"])
    current = filings[0] if filings else None
    observations = _observations(facts, cik, identity["brand"], current) if current else []
    return {
        "contract": "P431_PRIVATE_SEC_RESEARCH_V1",
        "case_id": case_id, "source": "SEC_EDGAR_OFFICIAL_PUBLIC_API",
        "api_documentation": "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        "submissions_url": sec_url("submissions", cik),
        "companyfacts_url": sec_url("companyfacts", cik),
        "cik": cik, "brand": identity["brand"],
        "legal_identity_verified": False,
        "reviewed_company_name": submissions["name"],
        "xbrl_company_name": facts["entityName"],
        "raw_response_sha256": hashes,
        "annual_filings": filings,
        "latest_annual_metric_observations": observations,
        "status": "NEEDS_REVIEW" if observations else "RESEARCH_MORE",
        "historical_regulatory_source": True,
        "financial_claims_verified": 0,
        "eligible_for_publication": False,
        "startup_reproducibility_proven": False,
        "notices": [
            "这只是按已知 CIK 与同一份 10-K accession 过滤的原始 XBRL 候选，未独立财务审计或确认合并范围。",
            "多个收入标签可能重叠：不得求和；比较收入与净利润需人工/受控二次检查。",
            "历史公司级财务不表示当前利润、单产品获利、交易金额或个人创业可复制性。",
        ],
    }


def output_path(value: Path) -> Path:
    path = value.resolve()
    if path.is_relative_to(ROOT.resolve()):
        raise ValueError("Private SEC data cannot be written inside repository/public release")
    return path


def main() -> None:
    p = argparse.ArgumentParser(description="Private SEC evidence collection; NEVER public admission")
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--online", action="store_true")
    modes.add_argument("--fixtures", type=Path, help="Directory with submissions.json and companyfacts.json")
    p.add_argument("--case", default="nerdwallet")
    p.add_argument("--contact", help="Actual operator contact email for SEC fair access, not persisted")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    target = output_path(args.output)
    identity = load_identity(args.case)
    cik = identity["sec_cik"]
    if args.online:
        if not args.contact:
            p.error("--online requires --contact with a real email")
        contact = validated_contact(args.contact)
        a, ah = get_sec_json(sec_url("submissions", cik), contact)
        time.sleep(1.5)  # at most 2 controlled calls, well below SEC fair access
        b, bh = get_sec_json(sec_url("companyfacts", cik), contact)
        mode = "LIVE_OFFICIAL_SEC_API"
    else:
        a, ah = fixture_json(args.fixtures / "submissions.json")
        b, bh = fixture_json(args.fixtures / "companyfacts.json")
        mode = "OFFLINE_FIXTURE_NOT_LIVE"
    result = triage(args.case, a, b, {"submissions": ah, "companyfacts": bh})
    result["mode"] = mode
    result["requests_made"] = 2 if args.online else 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "mode": mode, "case": args.case,
        "filings": len(result["annual_filings"]),
        "metric_candidates": len(result["latest_annual_metric_observations"]),
        "published": 0,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
