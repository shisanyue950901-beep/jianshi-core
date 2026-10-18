#!/usr/bin/env python3
"""T08b: evidence completeness and fail-closed provenance checks, offline only.

This suite does not fetch TrustMRR or any external API. URL availability and
displayed figures require Hark's separate live/manual 5-record spot check.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from t08_project_selection import featured_projects

RECORDS = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
HISTORIC = RECORDS[:20]
T10_NEW = RECORDS[20:]
EXPECTED_TOP = ["1clickwebsite-ai", "sonar-aso-tool", "3dplotter"]
CHECKED_ON = date(2026, 10, 16)
NEW_INDEPENDENT_T = {
    "datafast", "shipfast", "turbostarter", "readlens",
    "1devtool", "3dplotter", "ai-designer", "3d-agent",
}
PENDING_INDEPENDENT_T = {
    "search1api", "advanced-gsc-mcp", "adscriptly",
    "saashunt", "5-day-sprint",
}


class T08bSourcesTest(unittest.TestCase):
    def test_all_twenty_have_source_traction_flag_and_real_check_date(self) -> None:
        self.assertEqual(len(RECORDS), 30)
        self.assertEqual(len(HISTORIC), 20)
        self.assertEqual(len(T10_NEW), 10)
        self.assertEqual(len({p["id"] for p in RECORDS}), 30)
        for p in HISTORIC:
            with self.subTest(project=p["id"]):
                sources = p.get("sources") or []
                traction = p.get("traction") or []
                self.assertTrue(any(
                    s.get("level") in {"A", "A-"}
                    and urlsplit(s.get("url", "")).scheme == "https"
                    and date.fromisoformat(s["checked_at"]) <= CHECKED_ON
                    for s in sources
                ))
                self.assertTrue(any(
                    s.get("level") == "T"
                    and urlsplit(s.get("url", "")).scheme == "https"
                    for s in sources
                ))
                self.assertTrue(traction)
                self.assertTrue(all(
                    urlsplit(t.get("url", "")).scheme == "https"
                    for t in traction
                ))
                self.assertTrue(p.get("flags"))
                self.assertTrue(all(isinstance(f, str) and f.strip() for f in p["flags"]))
                self.assertTrue(any("TrustMRR 同平台" in f for f in p["flags"]))
                self.assertTrue(any("付费客户" in f for f in p["flags"]))
                self.assertLessEqual(date.fromisoformat(p["last_verified_at"]), CHECKED_ON)

    def test_external_sources_not_confused_with_revenue_proof(self) -> None:
        by_id = {p["id"]: p for p in RECORDS}
        for pid in NEW_INDEPENDENT_T:
            with self.subTest(project=pid):
                p = by_id[pid]
                new = [t for t in p["traction"]
                       if t.get("checked_at") == "2026-10-16"
                       and t.get("source_independence") == "INDEPENDENT_OF_REVENUE_PLATFORM"]
                self.assertTrue(new)
                for signal in new:
                    self.assertNotIn("trustmrr.com", urlsplit(signal["url"]).netloc)
                    self.assertTrue(any(
                        s["level"] == "T" and s["url"] == signal["url"]
                        for s in p["sources"]
                    ))
                    self.assertNotEqual(signal.get("type"), "revenue")

    def test_first_party_claims_are_disclosed_and_unverified_items_are_flagged(self) -> None:
        by_id = {p["id"]: p for p in RECORDS}
        for p in RECORDS:
            self.assertTrue(all(t.get("estimated") is True for t in p["traction"])
                            if p["id"] in {
                                "1devtool", "1clickwebsite-ai", "3dplotter",
                                "advanced-gsc-mcp", "aeo-checker", "ai-designer",
                                "adscriptly", "saashunt", "3d-agent", "5-day-sprint",
                            } else True)
            for t in p["traction"]:
                if t.get("source_independence") == "FIRST_PARTY_SELF_REPORT":
                    self.assertTrue(t.get("estimated"))
                    self.assertTrue(any("官网" in f or "官方页面自报" in f for f in p["flags"]))
        for pid in PENDING_INDEPENDENT_T:
            p = by_id[pid]
            self.assertEqual(p["last_verified_at"], "2026-10-15")
            self.assertTrue(any("暂未找到" in f for f in p["flags"]))


    def test_t10_ten_new_records_have_independent_platform_proof(self) -> None:
        """T10: structural proof gate; no external network call; Hark verifies actual page content."""
        from collections import Counter
        from urllib.parse import urlsplit
        current = date(2026, 10, 18)
        old_ids = {p["id"] for p in HISTORIC}
        self.assertEqual(len(T10_NEW), 10)
        self.assertEqual(len({p["id"] for p in RECORDS}), 30)
        cats = Counter(p["category"] for p in T10_NEW)
        self.assertGreaterEqual(cats["浏览器插件"], 2)
        self.assertGreaterEqual(cats["小App"], 2)
        self.assertLessEqual(cats["开发者工具"], 1)
        self.assertLessEqual(max(cats.values()), 3)
        approved_t_hosts = {
            "chromewebstore.google.com", "apps.apple.com",
            "play.google.com", "www.producthunt.com",
            "www.trustpilot.com", "uk.trustpilot.com", "github.com",
        }
        dims = {"build_difficulty", "channel_reach_cn", "payment_compliance",
                "competition", "time_to_mvp"}
        for p in T10_NEW:
            with self.subTest(project=p["id"]):
                self.assertNotIn(p["id"], old_ids)
                self.assertNotEqual(p["id"], "trustmrr")
                self.assertNotIn(p["category"], {"电商", "金融", "医疗", "成人", "代理服务"})
                self.assertGreaterEqual((current - date.fromisoformat(p["founded_date"])).days, 90)
                self.assertGreaterEqual(p["revenue"]["last_30d"], 1000)
                if 1000 <= p["revenue"]["last_30d"] <= 1500:
                    self.assertIn("临界：近30天接近 $1,000 门槛", p["flags"])
                self.assertTrue(any(s["level"] in {"A", "A-"}
                    and urlsplit(s["url"]).scheme == "https" and s["checked_at"] == "2026-10-18"
                    for s in p["sources"]))
                # The App Store may be the product homepage for app-only products.
                # The independent platform must differ from the PAYMENT proof host,
                # not necessarily the vendor-supplied landing URL.
                payment_hosts = {urlsplit(s["url"]).hostname for s in p["sources"] if s["level"] in {"A", "A-"}}
                good = [t for t in p["traction"] if
                    t.get("source_independence") == "INDEPENDENT_OF_REVENUE_PLATFORM"
                    and t.get("checked_at") == "2026-10-18"
                    and t.get("value") not in (None, "")
                    and t.get("estimated") is False
                    and urlsplit(t.get("url", "")).hostname in approved_t_hosts
                    and urlsplit(t.get("url", "")).hostname not in payment_hosts
                    and any(s["level"] == "T" and s["url"] == t["url"]
                            for s in p["sources"])]
                self.assertTrue(good, "缺独立第三方平台原页T证据")
                self.assertEqual(set(p["scores"]), dims)
                self.assertEqual(set(p["score_reasons"]), dims)
                self.assertTrue(all(isinstance(v, int) and 1 <= v <= 5 for v in p["scores"].values()))
                self.assertTrue(all(len(reason) > 14 for reason in p["score_reasons"].values()))
                self.assertEqual(p["total_score"], sum(p["scores"].values()))
                expected = ("推荐" if p["total_score"] >= 20 else
                            "可做" if p["total_score"] >= 15 else "不推荐")
                self.assertEqual(p["verdict"], expected)
                self.assertLessEqual(len(p["one_liner_cn"]), 30)
                self.assertLessEqual(len(p["cn_angle"]), 50)
                self.assertLessEqual(len(p["risks"]), 50)
                self.assertFalse(p["reviewed_by_hark"])
                self.assertEqual(p["publication_status"], "PRIVATE_REVIEW_ONLY")
                self.assertIsNone(p["customers"])
                self.assertIsNone(p["growth_30d"])
                self.assertEqual(p["last_verified_at"], "2026-10-18")
                self.assertTrue(p["flags"])
                self.assertTrue(p["tech_stack_guess"])

    def test_no_private_collection_or_api_endpoint_leaks(self) -> None:
        serialized = json.dumps(RECORDS, ensure_ascii=False).lower()
        self.assertNotIn("trustmrr_api_key", serialized)
        self.assertNotIn("trustmrr.com/api/v1", serialized)
        self.assertNotIn("private/trustmrr", serialized)

    def test_homepage_rank_and_revenue_are_unchanged(self) -> None:
        self.assertEqual([x["id"] for x in featured_projects()], EXPECTED_TOP)
        by_id = {p["id"]: p for p in RECORDS}
        self.assertEqual(by_id["1clickwebsite-ai"]["revenue"]["last_30d"], 15608)
        self.assertEqual(by_id["sonar-aso-tool"]["revenue"]["mrr"], 3744)
        self.assertEqual(by_id["3dplotter"]["revenue"]["mrr"], 0)
        self.assertEqual(by_id["ai-designer"]["revenue"]["last_30d"], 10578)


if __name__ == "__main__":
    unittest.main()
