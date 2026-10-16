#!/usr/bin/env python3
"""T09 离线单元测试。不得发起真实 TrustMRR 请求。"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlparse

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "collect" / "fetch_trustmrr.py"
spec = importlib.util.spec_from_file_location("fetch_trustmrr", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Clock:
    def __init__(self) -> None:
        self.current = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.current

    def wall(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds


def sample(slug: str, last30: int = 42500) -> dict:
    return {
        "slug": slug,
        "name": slug,
        "revenue": {"last30Days": last30, "mrr": 1234, "total": 123456},
        "askingPrice": 9999,
        "onSale": True,
    }


class TrustMrrCollectorTests(unittest.TestCase):
    def test_missing_key_is_fail_closed_without_network(self) -> None:
        calls = []
        with self.assertRaisesRegex(module.CollectorError, "TRUSTMRR_API_KEY"):
            module.collect(None, requester=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_cents_conversion_exact_and_null_safe(self) -> None:
        self.assertEqual(module.cents_to_usd(42500), "425.00")
        self.assertEqual(module.cents_to_usd(1), "0.01")
        self.assertEqual(module.cents_to_usd(9999), "99.99")
        self.assertIsNone(module.cents_to_usd(None))
        self.assertIsNone(module.cents_to_usd("NaN"))
        self.assertEqual(module.normalize(sample("demo"), "growth")["mrr_usd"], "12.34")

    def test_project_draft_4_2_has_frozen_fields_and_no_fabrication(self) -> None:
        candidate = module.normalize(sample("demo"), "growth")
        assert candidate is not None
        draft = candidate["project_draft_4_2"]
        required = {
            "id", "name", "url", "category", "one_liner_cn", "target_user",
            "revenue", "evidence_level", "sources", "traction", "flags",
            "for_sale", "business_model", "price_point", "acquisition_channels",
            "tech_stack_guess", "scores", "total_score", "cn_angle",
            "risks", "reviewed_by_hark", "last_verified_at", "updated_at",
        }
        self.assertEqual(set(draft), required)
        self.assertEqual(draft["revenue"]["last_30d"], 425.0)
        self.assertEqual(draft["revenue"]["mrr"], 12.34)
        self.assertEqual(draft["revenue"]["all_time"], 1234.56)
        self.assertIsNone(draft["revenue"]["source_last_synced"])
        self.assertIsNone(draft["total_score"])
        self.assertFalse(draft["reviewed_by_hark"])
        self.assertEqual(draft["traction"], [])
        self.assertIsNone(draft["last_verified_at"])

    def test_three_queries_dedup_slug_and_no_key_in_output(self) -> None:
        clock = Clock()
        calls = []
        key = "test-only-private-value"

        def requester(url, headers):
            calls.append((clock.current, parse_qs(urlparse(url).query), headers))
            data = [sample("Demo"), sample("Other")] if len(calls) == 1 else [sample("demo")]
            return 200, {}, {"data": data, "meta": {"hasMore": False}}

        payload = module.collect(
            key, requester=requester, sleep=clock.sleep,
            monotonic=clock.monotonic, wall_clock=clock.wall,
        )
        self.assertEqual(len(calls), 3)
        self.assertEqual(payload["candidate_count"], 2)
        self.assertEqual(payload["pages_fetched"], 3)
        self.assertEqual(payload["candidates"][0]["matched_queries"], [
            "growth", "recently_listed", "on_sale",
        ])
        self.assertNotIn(key, str(payload))
        for i in range(1, len(calls)):
            self.assertGreaterEqual(calls[i][0] - calls[i - 1][0], 6.5)
        self.assertEqual(calls[0][1]["sort"], ["growth-desc"])
        self.assertEqual(calls[1][1]["sort"], ["listed-desc"])
        self.assertEqual(calls[2][1]["onSale"], ["true"])
        self.assertEqual(calls[0][1]["limit"], ["10"])

    def test_429_reset_header_waits_and_retries_without_short_interval(self) -> None:
        clock = Clock()
        stamps = []

        def requester(url, headers):
            stamps.append(clock.current)
            if len(stamps) == 1:
                return 429, {"X-RateLimit-Reset": str(clock.current + 10)}, None
            return 200, {}, {"data": [], "meta": {"hasMore": False}}

        payload = module.collect(
            "test-only", requester=requester, sleep=clock.sleep,
            monotonic=clock.monotonic, wall_clock=clock.wall,
        )
        self.assertEqual(len(stamps), 4)
        self.assertEqual(payload["pages_fetched"], 3)
        self.assertGreaterEqual(stamps[1] - stamps[0], 10)
        self.assertTrue(all(b - a >= 6.5 for a, b in zip(stamps, stamps[1:])))

    def test_429_retry_cap_fails_closed(self) -> None:
        clock = Clock()

        def requester(url, headers):
            return 429, {}, None

        with self.assertRaisesRegex(module.CollectorError, "重试"):
            module.collect(
                "test-only", requester=requester, sleep=clock.sleep,
                monotonic=clock.monotonic, wall_clock=clock.wall,
            )

    def test_invalid_config_and_bad_schema(self) -> None:
        with self.assertRaises(module.CollectorError):
            module.collect("x", pages=4)
        with self.assertRaises(module.CollectorError):
            module.collect("x", limit=11)
        with self.assertRaisesRegex(module.CollectorError, "结构"):
            module.collect("x", requester=lambda u, h: (200, {}, []))


if __name__ == "__main__":
    unittest.main()
