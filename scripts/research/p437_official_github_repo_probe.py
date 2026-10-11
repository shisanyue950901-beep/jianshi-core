#!/usr/bin/env python3
"""P4.37: two pinned official GitHub public repositories, private-only metadata.

Zero search API, no arbitrary hosts, one GET/repository, no retries. These
engineering signals are NOT verified business revenue or paying subscribers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[2]
SOURCE_MATRIX = ROOT / "config/p432_source_access_matrix.json"
MAX_RESPONSE = 131072
TIMEOUT = 6
TARGETS = (
    ("plausible/analytics", 160427405, "https://plausible.io"),
    ("plausible/docs", 270703311, "https://plausible.io/docs"),
)
API = "https://api.github.com/repos/"
TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("GITHUB_REDIRECT_REJECTED")


def check_policy() -> None:
    data = json.loads(SOURCE_MATRIX.read_text(encoding="utf-8"))
    if data.get("contract") != "P437_PRIVATE_SOURCE_ACCESS_V2" or data.get("publication_allowed") is not False:
        raise ValueError("Unexpected data-source access contract")
    rows = data.get("sources")
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("Source registry count drift")
    gh = [r for r in rows if r.get("id") == "github-official-repos"]
    if len(gh) != 1:
        raise ValueError("Missing or duplicate GitHub source")
    item = gh[0]
    if (item.get("automated_fetch") != "DAILY_EXISTING_SCAN_SLOT_TWO_REQUESTS"
            or item.get("access") != "OFFICIAL_PUBLIC_REST_API"
            or item.get("max_requests_per_run") != 2
            or item.get("source_url") != "https://api.github.com/"
            or item.get("metadata_only") is not True):
        raise ValueError("GitHub policy does not allow this collection")
    for forbidden in ("acquire-listings","flippa-listings","microns-listings","indiehackers-pages"):
        rows_for = [r for r in rows if r.get("id") == forbidden]
        if len(rows_for) != 1 or rows_for[0].get("automated_fetch") != "FORBIDDEN":
            raise ValueError("Restricted platform improperly enabled")


def _valid_date(value: object) -> str | None:
    if not isinstance(value, str) or not TIMESTAMP.fullmatch(value):
        return None
    try:
        datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError:
        return None
    return value


def _count(data: dict, key: str) -> int:
    n = data.get(key)
    if type(n) is not int or not 0 <= n <= 100_000_000:
        raise ValueError("Invalid GitHub counter: " + key)
    return n


def extract_metadata(data: dict, expected_name: str, expected_id: int, homepage: str) -> dict:
    owner = data.get("owner")
    # Preserve strict identity rules; classify failures without persisting
    # external values, repository content, request headers or credentials.
    if type(data.get("id")) is not int or data["id"] != expected_id:
        raise ValueError("GITHUB_PINNED_REPO_ID_MISMATCH")
    if (data.get("full_name") != expected_name
            or data.get("name") != expected_name.split("/")[1]
            or not isinstance(owner,dict)
            or owner.get("login") != "plausible"
            or owner.get("type") != "Organization"
            or data.get("html_url") != "https://github.com/" + expected_name):
        raise ValueError("GITHUB_OWNER_OR_NAME_MISMATCH")
    if data.get("homepage") != homepage:
        raise ValueError("GITHUB_HOMEPAGE_MISMATCH")
    if (data.get("private") is not False
            or data.get("fork") is not False
            or data.get("archived") is not False
            or data.get("disabled") is not False):
        raise ValueError("GITHUB_REPO_POLICY_MISMATCH")
    created = _valid_date(data.get("created_at"))
    updated = _valid_date(data.get("updated_at"))
    pushed = _valid_date(data.get("pushed_at"))
    if not all((created,updated,pushed)):
        raise ValueError("GITHUB_TIMESTAMP_INVALID")
    return {
        "company_id":"plausible",
        "verified_public_repo_identity":True,
        "repo_id":expected_id,
        "repo_name":expected_name,
        "repo_url":"https://github.com/" + expected_name,
        "homepage":homepage,
        "created_at":created,
        "updated_at":updated,
        "pushed_at":pushed,
        "stars":_count(data,"stargazers_count"),
        "forks":_count(data,"forks_count"),
        "open_issue_counter":_count(data,"open_issues_count"),
        "identity_method":"PINNED_GITHUB_REPO_ID_ORG_LOGIN_AND_OFFICIAL_HOMEPAGE",
        "legal_entity_verified":False,
        "financial_evidence_verified":False,
        "customers_verified":False,
        "eligible_for_publication":False,
        "evidence_category":"TECHNICAL_REPOSITORY_ACTIVITY_NOT_BUSINESS_REVENUE",
    }


def fetch_once(repo_name: str, token: str | None) -> tuple[dict, str]:
    url = API + repo_name
    headers = {
        "Accept":"application/vnd.github+json",
        "User-Agent":"JianShiResearch/0.3",
        "X-GitHub-Api-Version":"2022-11-28",
        "Accept-Encoding":"identity",
    }
    if token:
        if not re.fullmatch(r"[^\s\x00-\x1f]{8,300}",token):
            raise ValueError("Invalid GitHub token shape")
        headers["Authorization"] = "Bearer " + token
    req = Request(url, headers=headers)
    try:
        with build_opener(NoRedirect()).open(req, timeout=TIMEOUT) as response:
            if (response.status != 200 or response.geturl() != url
                    or "json" not in response.headers.get("Content-Type","").lower()):
                raise ValueError("GITHUB_RESPONSE_ENVELOPE_REJECTED")
            raw = response.read(MAX_RESPONSE + 1)
    except HTTPError as error:
        raise RuntimeError("GITHUB_HTTP_" + str(error.code)) from None
    except (URLError, TimeoutError):
        raise RuntimeError("GITHUB_NETWORK_UNAVAILABLE") from None
    if len(raw) > MAX_RESPONSE:
        raise ValueError("GITHUB_RESPONSE_OVERSIZED")
    data = json.loads(raw)
    if not isinstance(data,dict):
        raise ValueError("GITHUB_JSON_ROOT_INVALID")
    return data,hashlib.sha256(raw).hexdigest()


def _category(error: Exception) -> str:
    msg = str(error)
    if msg.startswith("GITHUB_HTTP_"):
        return msg if re.fullmatch(r"GITHUB_HTTP_\d{3}",msg) else "GITHUB_HTTP_ERROR"
    if msg == "GITHUB_NETWORK_UNAVAILABLE":
        return msg
    if msg.startswith("Invalid GitHub counter: "):
        return "GITHUB_COUNTER_INVALID"
    allowed = {
        "GITHUB_PINNED_REPO_ID_MISMATCH",
        "GITHUB_OWNER_OR_NAME_MISMATCH",
        "GITHUB_HOMEPAGE_MISMATCH",
        "GITHUB_REPO_POLICY_MISMATCH",
        "GITHUB_TIMESTAMP_INVALID",
        "GITHUB_RESPONSE_ENVELOPE_REJECTED",
        "GITHUB_RESPONSE_OVERSIZED",
        "GITHUB_JSON_ROOT_INVALID",
        "GITHUB_REDIRECT_REJECTED",
        "Invalid GitHub token shape",
    }
    if msg in allowed:
        return "GITHUB_TOKEN_SHAPE_INVALID" if msg == "Invalid GitHub token shape" else msg
    if isinstance(error, json.JSONDecodeError):
        return "GITHUB_JSON_PARSE_FAILED"
    return "SOURCE_SCHEMA_OR_IDENTITY_REJECTED"


def collect(offline: Path | None = None, online: bool = False, token: str | None = None) -> dict:
    if (offline is None) == (not online):
        raise ValueError("Choose exactly one mode: online or fixtures")
    check_policy()
    results,failures = [],[]
    requests_made = 0
    for name,expected_id,homepage in TARGETS:
        try:
            if online:
                requests_made += 1
                raw,sha = fetch_once(name,token)
            else:
                path = offline/(name.replace("/","__") + ".json")
                if not path.is_file() or not 0 < path.stat().st_size <= MAX_RESPONSE:
                    raise ValueError("Missing/oversized source fixture")
                data_bytes=path.read_bytes()
                raw=json.loads(data_bytes)
                sha=hashlib.sha256(data_bytes).hexdigest()
            record=extract_metadata(raw,name,expected_id,homepage)
            record["source_response_sha256"]=sha
            results.append(record)
        except (RuntimeError,ValueError,KeyError,TypeError,json.JSONDecodeError) as error:
            failures.append({"repo_name":name,"reason_code":_category(error)})
            # Fail closed on 403/429. Do not retry through another identity.
            if online and isinstance(error,RuntimeError) and str(error) in ("GITHUB_HTTP_403","GITHUB_HTTP_429"):
                break
    return {
        "contract":"P437_PRIVATE_GITHUB_REPO_METRICS_V1",
        "collected_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode":"LIVE_OFFICIAL_GITHUB_API" if online else "OFFLINE_FIXTURE_NOT_LIVE",
        "source":"GITHUB_PUBLIC_REST_API",
        "source_identity":"plausible",
        "requests_attempted":requests_made,
        "requests_max":2,
        "validated_repos":len(results),
        "rejected_repos":len(failures),
        "records":results,
        "failures":failures,
        "raw_response_archived":False,
        "personal_data_stored":False,
        "legal_entities_verified":0,
        "financial_claims_verified":0,
        "business_revenue_verification":False,
        "publication_allowed":False,
        "notices":["公开GitHub仓库星标、fork、issue、提交更新时间不等于客户、订阅、收入、利润或可复制创业需求。",
                   "仅核对官方组织、固定repo ID、官网及仓库当前状态；不能自动证明公司法律主体。",
                   "HTTP 失败或仓库ID改变不绕过规则，也不把未核验仓库记为成功数据。"],
    }


def private_path(raw: Path) -> Path:
    full=raw.resolve()
    if full.is_relative_to(ROOT.resolve()):
        raise ValueError("Cannot publish or commit private technical research")
    return full


def main() -> None:
    parser=argparse.ArgumentParser(description="Pinned official GitHub repository metadata, private only")
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--online",action="store_true")
    mode.add_argument("--fixtures",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    out=private_path(args.output)
    # GITHUB_TOKEN / GH_TOKEN are runner-provided; never log or persist token.
    token=(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")) if args.online else None
    data=collect(args.fixtures,args.online,token)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if data["mode"] == "LIVE_OFFICIAL_GITHUB_API" and data["validated_repos"] < 2:
        reasons = ",".join(row["reason_code"] for row in data["failures"])
        # Stable public reason codes only; never echo raw GitHub responses.
        print("::warning title=JianShi Official GitHub Source Degraded::" + reasons)
    elif data["mode"] == "LIVE_OFFICIAL_GITHUB_API":
        print("P437_GITHUB_PINNED_IDENTITIES_VERIFIED_2_OF_2")
    print(json.dumps({"source":"GITHUB_PUBLIC_REST_API","mode":data["mode"],
        "attempted":data["requests_attempted"],"validated":data["validated_repos"],
        "rejected":data["rejected_repos"],"published":0},ensure_ascii=False))


if __name__=="__main__":
    main()
