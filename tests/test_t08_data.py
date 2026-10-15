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
        if tag == "a" and d.get("data-discover-card") is not None and d.get("data-category") == "projects":
            self.discovered.append(d.get("href"))
    def error(self, message):
        raise AssertionError(message)

class TestT08(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.added = [p for p in cls.data if p["id"] not in OLD]

    def test_exact_counts_unique_and_categories(self):
        self.assertEqual(len(self.data),20)
        self.assertEqual(len(self.added),10)
        self.assertEqual(len({p["id"] for p in self.data}),20)
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
                self.assertLessEqual(len(p["one_liner_cn"]),30)
                self.assertLessEqual(len(p["cn_angle"]),50)
                self.assertLessEqual(len(p["risks"]),50)
                if p in self.added:
                    self.assertFalse(p["reviewed_by_hark"])
                    self.assertEqual(p["publication_status"],"PRIVATE_REVIEW_ONLY")
                    self.assertEqual(p["revenue"]["as_of"],"2026-10-15")
                    self.assertIsNone(p["customers"])

    def test_home_and_discovery_are_exactly_json_top_three(self):
        winners=sorted(self.data,key=lambda p:(-p["total_score"],-p["revenue"]["last_30d"],p["id"]))[:3]
        self.assertEqual([x["id"] for x in winners],[x["id"] for x in featured_projects()])
        index=(WEB/"index.html").read_text(encoding="utf-8")
        discovery=(WEB/"discover"/"index.html").read_text(encoding="utf-8")
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
        self.assertEqual(len(dirs)+1,21)

if __name__=="__main__":
    unittest.main()
