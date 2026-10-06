from __future__ import annotations
import hashlib
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Iterable

BASE_URL = "https://api.empireflippers.com/api/v1/listings/list"
PARSER_VERSION = "empire_flippers_v1.0"

@dataclass(frozen=True)
class NormalizedListing:
    source_external_id: str
    listing_number: int | None
    public_title: str | None
    listing_status: str | None
    listing_price: float | None
    unpriced: bool
    average_monthly_net_profit: float | None
    average_monthly_expenses: float | None
    average_monthly_gross_revenue: float | None
    average_annual_net_profit: float | None
    average_annual_expenses: float | None
    average_annual_gross_revenue: float | None
    listing_multiple: float | None
    annual_listing_multiple: float | None
    listing_multiple_type: str | None
    profit_margin: float | None
    mrr: float | None
    churn_percent: float | None
    growth_percent: float | None
    hours_worked_per_week: float | None
    days_on_marketplace: int | None
    country_code: str | None
    countries: list[str]
    monetizations: list[str]
    niches: list[str]
    first_made_money_at: str | None
    first_listed_at: str | None
    reason_for_sale: str | None
    source_updated_at: str | None

def _num(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def normalize(raw: dict[str, Any]) -> NormalizedListing:
    if not raw.get("id"):
        raise ValueError("missing listing id")
    return NormalizedListing(
        source_external_id=str(raw["id"]),
        listing_number=raw.get("listing_number"),
        public_title=raw.get("public_title"),
        listing_status=raw.get("listing_status"),
        listing_price=_num(raw.get("listing_price")),
        unpriced=bool(raw.get("unpriced", False)),
        average_monthly_net_profit=_num(raw.get("average_monthly_net_profit")),
        average_monthly_expenses=_num(raw.get("average_monthly_expenses")),
        average_monthly_gross_revenue=_num(raw.get("average_monthly_gross_revenue")),
        average_annual_net_profit=_num(raw.get("average_annual_net_profit")),
        average_annual_expenses=_num(raw.get("average_annual_expenses")),
        average_annual_gross_revenue=_num(raw.get("average_annual_gross_revenue")),
        listing_multiple=_num(raw.get("listing_multiple")),
        annual_listing_multiple=_num(raw.get("annual_listing_multiple")),
        listing_multiple_type=raw.get("listing_multiple_type"),
        profit_margin=_num(raw.get("profit_margin")),
        mrr=_num(raw.get("mrr")),
        churn_percent=_num(raw.get("churn_percent")),
        growth_percent=_num(raw.get("growth_percent")),
        hours_worked_per_week=_num(raw.get("hours_worked_per_week")),
        days_on_marketplace=raw.get("days_on_marketplace"),
        country_code=raw.get("country"),
        countries=list(raw.get("countries") or []),
        monetizations=[x.get("monetization") for x in (raw.get("monetizations") or []) if x.get("monetization")],
        niches=[x.get("niche") for x in (raw.get("niches") or []) if x.get("niche")],
        first_made_money_at=raw.get("first_made_money_at"),
        first_listed_at=raw.get("first_listed_at"),
        reason_for_sale=raw.get("reason_for_sale"),
        source_updated_at=raw.get("updated_at"),
    )

def snapshot_hash(item: NormalizedListing) -> str:
    payload = json.dumps(asdict(item), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def parse_page(payload: dict[str, Any]) -> list[NormalizedListing]:
    listings = ((payload.get("data") or {}).get("listings") or [])
    return [normalize(x) for x in listings]

def fetch_page(page: int, listing_status: str = "For Sale", timeout: int = 30) -> dict[str, Any]:
    params = urllib.parse.urlencode({"page": page, "listing_status": listing_status})
    url = f"{BASE_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "JianShi/0.1 (+business-intelligence; official-api)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Empire Flippers HTTP {resp.status}")
        return json.loads(resp.read().decode("utf-8"))

def iter_pages(max_pages: int = 100, sleep_seconds: float = 1.05) -> Iterable[tuple[int, dict[str, Any]]]:
    """Rate limited to <=1 req/s. Stops when a page contains no listings."""
    for page in range(1, max_pages + 1):
        payload = fetch_page(page)
        listings = ((payload.get("data") or {}).get("listings") or [])
        if not listings:
            break
        yield page, payload
        time.sleep(sleep_seconds)
