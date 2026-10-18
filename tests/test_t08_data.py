#!/usr/bin/env python3
"""T08 Hark hard gates: source admission, age, traction, scoring, JSON ranked home.

Uses the project database and generated static files; network access forbidden.
An Hark-pending feature preview is not equivalent to production editorial approval.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from collections import Counter
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from t08_project_selection import featured_projects, usd

DATA = ROOT / "data" / "projects.json"
WEB = ROOT / "web" / "dist"
OLD = {"datafast","shipfast","turbostarter","sonar-aso-tool","search1api",
       "agentskit","opentweet","getebook-ai","mastros","readlens"}
BANNED = {"电商","金融","医疗","成人","代理"}
NEAR = "临界：近30天接近 $1,000 门槛"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.featured = []
        self.discovered = []
        self.in_home_card = None
        self.capture = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "article" and "data-t08-id" in d:
            self.featured.append(d["data-t08-id"])
        if tag == "a" and "data-discover-card" in d and d.get("data-category") == "projects":
            self.discovered.append(d.get("href"))
    def error(self, message):
        raise AssertionError(message)

class TestT08(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.historic = cls.data[:20]
        cls.added = [p for p in cls.historic if p["id"] not in OLD]

    def test_exact_counts_unique_and_categories(self):
        self.assertEqual(len(self.data),30)
        self.assertEqual(len(self.added),10)
        self.assertEqual(len({p["id"] for p in self.data}),30)
        self.assertGreaterEqual(len({p["category"] for p in self.data}),5)
        self.assertLessEqual(max(Counter(p["category"] for p in self.added).values()),4)
        self.assertGreaterEqual(sum(p["total_score"] >= 20 for p in self.added),2)

    def test_all_twenty_have_payment_age_and_traction(self):
        for p in self.data:
            with self.subTest(project=p["id"]):
                age=(date.today()-date.fromisoformat(p["founded_date"])).days
                self.assertGreaterEqual(age,90)
                self.assertGreaterEqual(p["revenue"]["last_30d"],1000)
                self.assertTrue(any(s["level"] in ("A","A-") and s["url"].startswith("https://") for s in p["sources"]))
                self.assertTrue(any(s["level"]=="T" for s in p["sources"]))
                self.assertTrue(p["traction"])
                self.assertTrue(all(t.get("estimated") is True for t in p["traction"]) if p in self.added else True)
                self.assertNotIn(p["category"],BANNED)
                self.assertNotEqual(p["id"],"trustmrr")
                if p in self.added and 1000<=p["revenue"]["last_30d"]<=1500:
                    self.assertIn(NEAR,p["flags"])
                self.assertEqual(p["total_score"],sum(p["scores"].values()))
                self.assertEqual(p["verdict"],"推荐" if p["total_score"]>=20 else "可做" if p["total_score"]>=15 else "不推荐")
                self.assertTrue(all(p["score_reasons"].values()))
                self.assertTrue("竞品：" in p["score_reasons"]["competition"])
                self.assertTrue(p["tech_stack_guess"].startswith("推测：") if p in self.added else True)
                if p in self.added:
                    self.assertLessEqual(len(p["one_liner_cn"]),30)
                    self.assertLessEqual(len(p["cn_angle"]),50)
                    self.assertLessEqual(len(p["risks"]),50)
                    self.assertTrue(p["reviewed_by_hark"])
                    self.assertEqual(p["publication_status"],"PUBLIC")
                    self.assertEqual(p["revenue"]["as_of"],"2026-10-15")
                    self.assertIsNone(p["customers"])

    def test_hark_corrected_revenue_and_approval_contract(self):
        by_id={p["id"]:p for p in self.data}
        for pid in ("3dplotter", "saashunt"):
            self.assertEqual(by_id[pid]["revenue"]["mrr"], 0)
            self.assertIn("MRR 为 $0，近30天收入为一次性付款，非订阅",by_id[pid]["flags"])
        tool=by_id["1devtool"]
        self.assertEqual(tool["revenue"]["mrr"], 2.41)
        self.assertIn("MRR 仅 $2.41，收入几乎全部为一次性买断",tool["flags"])
        self.assertIn("TrustMRR 在售：$50,000（3.4x）",tool["flags"])
        self.assertEqual(tool["for_sale"]["asking_price"],50000)
        sprint=by_id["5-day-sprint"]
        self.assertIn("Skool",sprint["business_model"])
        self.assertIn("人工辅导",sprint["business_model"])
        self.assertIn("MRR $6,272 高于近30天实收 $3,409，可能含年付或未收款，收入结构待查",sprint["flags"])
        plot=by_id["3dplotter"]
        self.assertEqual(plot["scores"]["channel_reach_cn"],3)
        self.assertEqual(plot["total_score"],20)
        self.assertIn("近30天收入 -27.6%",plot["flags"])
        self.assertEqual(by_id["1clickwebsite-ai"]["growth_30d"],15.6)
        self.assertEqual(by_id["1clickwebsite-ai"]["revenue"]["source_last_synced"],"2026-10-15T14:23:04.223Z")
        designer=by_id["ai-designer"]
        self.assertEqual(designer["revenue"]["last_30d"],10578)
        self.assertIn("$10,909",designer["review_notes"])

    def test_main_environment_does_not_need_preview_exception(self):
        import os
        from unittest.mock import patch
        from t08_project_selection import projects
        with patch.dict(os.environ,{
            "CI":"true", "GITHUB_ACTIONS":"true",
            "CF_PAGES_BRANCH":"main", "GITHUB_HEAD_REF":"",
            "GITHUB_REF_NAME":"main",
        }):
            data=projects()
            with self.assertRaisesRegex(ValueError, "Unapproved project records"):
                from t08_project_selection import projects
                projects()
            self.assertEqual(len(self.historic), 20)
            self.assertTrue(all(p["reviewed_by_hark"] and p["publication_status"] == "PUBLIC" for p in self.historic))

    def test_home_and_discovery_are_exactly_json_top_three(self):
        winners=sorted(self.data,key=lambda p:(-p["total_score"],-p["revenue"]["last_30d"],p["id"]))[:3]
        self.assertEqual([x["id"] for x in winners],[x["id"] for x in featured_projects()])
        from p445_unified_home import build_home
        from p423_build_project_proofs import parse_cases
        from p425_public_admission import eligible_cases
        index=build_home(eligible_cases(parse_cases()))  # deterministic release renderer
        from f21_g2_discovery import render as render_discovery
        discovery=render_discovery()  # deterministic build-time HTML; no I/O ordering dependency
        hp=Links(); hp.feed(index)
        dp=Links(); dp.feed(discovery)
        self.assertEqual(hp.featured,[x["id"] for x in winners])
        self.assertEqual(dp.discovered,[f'/projects/{x["id"]}/' for x in winners])
        for p in winners:
            self.assertIn(f'href="/projects/{p["id"]}/"',index)
            self.assertIn(f'href="/projects/{p["id"]}/"',discovery)
            self.assertIn(escape(p["one_liner_cn"],quote=True),index)
            self.assertIn(escape(p["name"],quote=True),index)
            self.assertIn(escape(p["name"],quote=True),discovery)
            self.assertIn(usd(p["revenue"]["last_30d"]),index)
            self.assertIn(usd(p["revenue"]["last_30d"]),discovery)
            self.assertIn(p["verdict"],index)
            self.assertIn(p["verdict"],discovery)
        self.assertEqual(len({p["id"] for p in winners}),3)

    def test_twenty_one_static_pages_exist(self):
        if not (WEB/"projects"/"index.html").exists():
            self.skipTest("Build the release artifact before testing HTML")
        dirs={x.name for x in (WEB/"projects").iterdir() if x.is_dir()}
        self.assertEqual(dirs,{p["id"] for p in self.data})
        self.assertEqual(len(dirs)+1,31)

if __name__=="__main__":
    unittest.main()
