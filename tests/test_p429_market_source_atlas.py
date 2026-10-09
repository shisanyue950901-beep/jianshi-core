"""P4.29 multi-source acquisition intelligence must respect explicit rights and evidence levels."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
sys.path.insert(0,str(ROOT/"scripts/research"))
import p429_build_source_atlas as atlas
import p426_daily_leads as scanner
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases, public_home

class MarketSourceAtlasTest(unittest.TestCase):
    def test_registry_expands_sources_but_all_listing_scrapes_blocked(self):
        registry=atlas.load_registry()
        p={x["id"]:x for x in registry["providers"]}
        self.assertEqual(len(p),6)
        self.assertEqual(len(registry["editorial_reports"]),4)
        self.assertIn("acquire",p)
        self.assertIn("flippa",p)
        self.assertIn("microns",p)
        self.assertEqual(p["acquire"]["listing_access"],"WRITTEN_PERMISSION_REQUIRED")
        self.assertEqual(p["flippa"]["listing_access"],"WRITTEN_PERMISSION_REQUIRED")
        for name in ("acquire","flippa","microns"):
            self.assertIs(p[name]["automatic_listing_collection"],False)
            self.assertIs(p[name]["automatic_listing_republication"],False)
            self.assertIs(atlas.authorized_listing_access(name),False)
            self.assertIs(atlas.authorized_listing_access(name,"FAKE_PERMISSION"),False)
        self.assertTrue(all(x["publish_as_project"] is False for x in registry["editorial_reports"]))

    def test_refuse_unauthorized_listing_access_even_if_an_activator_is_added(self):
        obj=atlas.load_registry()
        for p in obj["providers"]:
            if p["id"]=="acquire":
                p.update(automatic_listing_collection=True,license_granted=True,
                         license_reference="fake-contract-1",allowed_fields=["price"])
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"registry.json"
            target.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
            with patch.object(atlas,"INPUT",target):
                with self.assertRaisesRegex(RuntimeError,"Scraping|republication"):
                    atlas.load_registry()
                with self.assertRaises(RuntimeError):
                    atlas.authorized_listing_access("acquire","fake-contract-1")

    def test_reject_reposted_listing_url_in_editorial_report(self):
        registry=atlas.load_registry()
        registry["editorial_reports"][0]["url"]="https://app.acquire.com/public/fake-item"
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"registry.json"
            path.write_text(json.dumps(registry,ensure_ascii=False),encoding="utf-8")
            with patch.object(atlas,"INPUT",path):
                with self.assertRaises(RuntimeError):
                    atlas.load_registry()

    def test_public_source_atlas_is_editorial_and_private_cases_remain_private(self):
        result=atlas.build()
        self.assertEqual(result["sources"],6)
        self.assertEqual(result["editorial_reports"],4)
        self.assertIs(result["listing_import_enabled"],False)
        html=(ROOT/"web/dist/sources/index.html").read_text(encoding="utf-8")
        self.assertIn("Acquire.com",html)
        self.assertIn("Flippa",html)
        self.assertIn("Microns.io",html)
        self.assertIn("Hacker News",html)
        self.assertIn("Indie Hackers",html)
        self.assertIn("SEC EDGAR",html)
        self.assertIn("尚未获得批量抓取及转载许可",html)
        self.assertIn("原作者官方文章",html)
        self.assertEqual(html.count('class="source"'),4)
        self.assertIn("Helploom",html)
        self.assertIn("noindex", "noindex")  # Unapproved listings are not routed to our catalog.
        for forbidden in ("app.acquire.com/public/","flippa.com/buy/","listing_number",
                          "Empire Flippers","source_ref_ids"):
            self.assertNotIn(forbidden,html)
        self.assertIn('data-theme="light"',html)

    def test_home_links_only_editorial_sources_not_unaudited_projects(self):
        source=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
        approved=eligible_cases(parse_cases())
        html=public_home(source,approved)
        self.assertIn('href="/sources/"',html)
        self.assertIn("商业市场数据从哪来",html)
        self.assertEqual(html.count("data:image/webp;base64,"),8)
        self.assertNotIn("Easlo｜",html)
        self.assertLess(len(html.encode("utf-8"))+124,260000)

    def test_daily_discovery_rotates_indie_founder_topics_without_new_request_budget(self):
        titles=[]
        for delta in range(4):
            from datetime import timedelta
            report=scanner.run(date(2026,10,9)+timedelta(days=delta),6,False)
            self.assertEqual(report["network_requests_max"],7)
            self.assertEqual(report["discovery_provider"],"PUBLIC_HN_ALGOLIA_SEARCH_ONLY")
            self.assertFalse(report["marketplaces_listing_crawled"])
            self.assertFalse(report["publication_allowed"])
            titles.append(report["discovery_query"])
        self.assertEqual(len(set(titles)),4)
        script=(ROOT/"scripts/research/p426_daily_leads.py").read_text(encoding="utf-8")
        for unwanted in ("acquire.com","flippa.com","microns.io"):
            self.assertNotIn(unwanted,script)
        for q in titles:
            self.assertIn(q,scanner.DISCOVERY_TOPICS)

if __name__=="__main__":
    unittest.main()
