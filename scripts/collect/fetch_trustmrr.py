#!/usr/bin/env python3
"""TrustMRR 私有候选采集（手动运行；禁止接入公开站点、AI 数据集或 CI）。

只允许获授权账号依照 TrustMRR API Acceptable Use Policy 执行内部研究。
官方文档：https://trustmrr.com/docs/api/list-startups
条款：https://trustmrr.com/terms （特别是 §9.2—§9.4）
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://trustmrr.com/api/v1/startups"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_DIR = PROJECT_ROOT / "private" / "trustmrr"
MIN_INTERVAL = 6.5
MAX_PAGES = 3
MAX_LIMIT = 10
MAX_429_RETRIES = 4
QUERIES = (
    ("growth", {"sort": "growth-desc"}),
    ("recently_listed", {"sort": "listed-desc"}),
    ("on_sale", {"onSale": "true"}),
)


class CollectorError(RuntimeError):
    """Expected error without request headers, token, or raw response contents."""


def cents_to_usd(value: Any) -> str | None:
    """Return an exact two-decimal USD string; missing values remain null."""
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            return None
        return format(amount / 100, ".2f")
    except (InvalidOperation, ValueError):
        return None


def usd_json_number(value: Any) -> float | None:
    """Project 4.2 uses numeric USD; keep two-decimal source strings separately."""
    exact = cents_to_usd(value)
    return float(exact) if exact is not None else None


def normalize(item: dict[str, Any], query_name: str) -> dict[str, Any] | None:
    slug = item.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        return None
    slug = slug.strip()
    revenue = item.get("revenue")
    if not isinstance(revenue, dict):
        revenue = {}
    source_url = "https://trustmrr.com/startup/" + slug
    date = datetime.now(timezone.utc).date().isoformat()
    # 4.2 requires many editorial fields that the API cannot establish.
    # Keep them NULL/empty; never fabricate scoring, traction, sync dates,
    # Chinese positioning, acquisition channels, or a validation approval.
    draft_4_2 = {
        "id": slug,
        "name": item.get("name"),
        "url": item.get("website"),
        "category": None,
        "one_liner_cn": None,
        "target_user": None,
        "revenue": {
            "mrr": usd_json_number(revenue.get("mrr")),
            "last_30d": usd_json_number(revenue.get("last30Days")),
            "all_time": usd_json_number(revenue.get("total")),
            "currency": "USD",
            "as_of": None,
            "verified_by": item.get("paymentProvider"),
            "source_last_synced": None,
        },
        "evidence_level": "A" if revenue.get("last30Days") is not None else None,
        "sources": [{"label": "TrustMRR", "level": "A", "url": source_url,
                     "checked_at": date}],
        "traction": [],
        "flags": ["待人工交叉验证", "缺少来源同步时间"],
        "for_sale": {"listed": item.get("onSale") is True,
                     "asking_price": usd_json_number(item.get("askingPrice")),
                     "multiple": item.get("multiple"), "url": source_url},
        "business_model": None,
        "price_point": None,
        "acquisition_channels": [],
        "tech_stack_guess": None,
        "scores": {
            "build_difficulty": None, "channel_reach_cn": None,
            "payment_compliance": None, "competition": None,
            "time_to_mvp": None,
        },
        "total_score": None,
        "cn_angle": None,
        "risks": None,
        "reviewed_by_hark": False,
        "last_verified_at": None,
        "updated_at": date,
    }
    # Keep only limited API fields: no founder identity, customer PII,
    # full profiles, raw API response, or detail-page crawl.
    return {
        "slug": slug,
        "name": item.get("name"),
        "website": item.get("website"),
        "category": item.get("category"),
        "payment_provider": item.get("paymentProvider"),
        "founded_date": item.get("foundedDate"),
        "revenue_last_30d_usd": cents_to_usd(revenue.get("last30Days")),
        "mrr_usd": cents_to_usd(revenue.get("mrr")),
        "revenue_total_usd": cents_to_usd(revenue.get("total")),
        "asking_price_usd": cents_to_usd(item.get("askingPrice")),
        "on_sale": item.get("onSale") is True,
        "growth_30d_raw": item.get("growth30d"),
        "source_url": source_url,
        "matched_queries": [query_name],
        "project_draft_4_2": draft_4_2,
    }


def _request(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], Any]:
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, dict(response.headers), json.load(response)
    except HTTPError as exc:
        # Avoid returning response body or exception (may contain private data).
        return exc.code, dict(exc.headers), None
    except (URLError, TimeoutError, OSError) as exc:
        raise CollectorError("网络请求失败，请检查连接或 API 可用性") from None


def reset_wait_seconds(raw: str | None, now: float) -> float:
    """API reset header is a Unix timestamp (seconds; tolerate milliseconds)."""
    if not raw:
        return 7.0
    try:
        reset = float(raw)
        if reset > 1e12:
            reset /= 1000
        if not (0 < reset < float("inf")):
            return 7.0
        return max(1.0, min(3600.0, reset - now + 0.25))
    except (ValueError, TypeError, OverflowError):
        return 7.0


class RateGate:
    def __init__(
        self,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.sleep = sleep
        self.monotonic = monotonic
        self.last_started: float | None = None

    def before_request(self) -> None:
        if self.last_started is not None:
            remaining = MIN_INTERVAL - (self.monotonic() - self.last_started)
            if remaining > 0:
                self.sleep(remaining)
        self.last_started = self.monotonic()


def collect(
    api_key: str | None,
    *,
    pages: int = MAX_PAGES,
    limit: int = MAX_LIMIT,
    requester: Callable[[str, dict[str, str]], tuple[int, dict[str, str], Any]] = _request,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
) -> dict[str, Any]:
    if not api_key or not api_key.strip():
        raise CollectorError("未设置 TRUSTMRR_API_KEY；不执行网络请求")
    if not (1 <= pages <= MAX_PAGES) or not (1 <= limit <= MAX_LIMIT):
        raise CollectorError("pages 必须为 1–3，limit 必须为 1–10")

    gate = RateGate(sleep=sleep, monotonic=monotonic)
    by_slug: dict[str, dict[str, Any]] = {}
    total_pages = 0
    for query_name, filters in QUERIES:
        for page in range(1, pages + 1):
            params = {"page": page, "limit": limit, **filters}
            url = API_URL + "?" + urlencode(params)
            attempts = 0
            while True:
                gate.before_request()
                status, response_headers, payload = requester(
                    url, {"Authorization": "Bearer " + api_key.strip(), "Accept": "application/json"}
                )
                if status == 429:
                    attempts += 1
                    if attempts > MAX_429_RETRIES:
                        raise CollectorError("API 429 限流，已达到重试次数上限")
                    lowered = {str(k).lower(): str(v) for k, v in response_headers.items()}
                    sleep(reset_wait_seconds(lowered.get("x-ratelimit-reset"), wall_clock()))
                    continue
                if status != 200:
                    raise CollectorError("API 请求失败，HTTP " + str(status))
                if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                    raise CollectorError("API 响应结构不符合预期")
                meta = payload.get("meta")
                if not isinstance(meta, dict):
                    raise CollectorError("API 分页元数据缺失")
                break

            total_pages += 1
            for item in payload["data"]:
                if not isinstance(item, dict):
                    continue
                candidate = normalize(item, query_name)
                if candidate is None:
                    continue
                slug = candidate["slug"].casefold()
                if slug in by_slug:
                    existing = by_slug[slug]
                    if query_name not in existing["matched_queries"]:
                        existing["matched_queries"].append(query_name)
                else:
                    by_slug[slug] = candidate
            if meta.get("hasMore") is False:
                break

    return {
        "schema_version": "T09-private-candidates-v1",
        "source": "TrustMRR",
        "source_api": API_URL,
        "use_restriction": "PRIVATE_AUTHORIZED_ACQUISITION_RESEARCH_ONLY",
        "public_display_allowed": False,
        "ai_dataset_or_recommendation_allowed": False,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "pages_requested_per_query": pages,
        "page_size": limit,
        "pages_fetched": total_pages,
        "candidate_count": len(by_slug),
        "candidates": list(by_slug.values()),
    }


def save_private(payload: dict[str, Any], now: datetime | None = None) -> Path:
    date = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PRIVATE_DIR / ("candidates_" + date + ".json")
    # No raw payloads or credentials; output directory is always git-ignored.
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TrustMRR 授权账号私有研究候选采集，不公开发布")
    parser.add_argument("--pages", type=int, default=MAX_PAGES, help="每种查询页数，1–3")
    parser.add_argument("--limit", type=int, default=MAX_LIMIT, help="每页项目数，1–10")
    args = parser.parse_args(argv)
    try:
        payload = collect(os.environ.get("TRUSTMRR_API_KEY"), pages=args.pages, limit=args.limit)
        output_path = save_private(payload)
    except (CollectorError, OSError) as exc:
        # Never print network error objects or a credential.
        print(str(exc) if isinstance(exc, CollectorError) else "写入私有候选文件失败", file=sys.stderr)
        return 1
    print("私有候选数：" + str(payload["candidate_count"]))
    print("输出目录：private/trustmrr/" + output_path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
