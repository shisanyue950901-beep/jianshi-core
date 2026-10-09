"""P4.33 private ETL from bounded HN/RSS source reports, never public admission."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/research"))
import p433_private_evidence_etl as etl
import p426_daily_leads as scanner

DAY = date(2026, 10, 9)


def hit(n, title="Fathom Analytics shares revenue", url="https://usefathom.com/blog/finances"):
    return {
        "headline": title,
        "discussion_url": f"https://news.ycombinator.com/item?id={n}",
        "external_url": url,
        "published_at": "2026-09-20T12:00:00Z",
        "status": "UNVERIFIED_DISCOVERY_LEAD",
        "financial_evidence": False,
        "source_kind": "HN_SEARCH_INDEX_METADATA_ONLY",
    }


def hn():
    return {
        "contract": "P4.26_PRIVATE_RESEARCH_LEADS_V1",
        "publication_allowed": False, "marketplaces_listing_crawled": False,
        "network_requests_max": 7, "mode": "READ_ONLY_ONLINE",
        "source_scope": "PUBLIC_SEARCH_INDEX_ONLY",
        "candidate_count": 2,
        "candidates": [
            {"slug": "fathom", "name": "Fathom Analytics",
             "error": None, "stories": [
                 hit(123), hit(123),
                 hit(124, "Unknown business sale", "https://app.acquire.com/public/123"),
             ]},
            {"slug": "kit", "name": "Kit",
             "error": "TimeoutError", "stories": [
                 hit(125, "Kit has paying customers", "https://example.com/blog/kit")
             ]},
        ],
        "unmatched_new_project_leads": [hit(126, "Bootstrapped founder news", "https://news.example.org/founder")],
    }


def rss():
    return {
        "contract": "P432_PRIVATE_RSS_LEADS_V1",
        "eligible_for_publication": False, "financial_claims_verified": 0,
        "source_fulltext_stored": False,
        "source_url": "https://usefathom.com/blog/feed.xml",
        "mode": "LIVE_RSS_HTTP", "network_requests": 1, "records_count": 2,
        "records": [
            {
                "company_id": "fathom", "candidate_company": "Fathom Analytics",
                "title": "Fathom company finances", "source_url": "https://usefathom.com/blog/finances",
                "published_on": "2026-09-20",
                "source_kind": "FIRST_PARTY_RSS_METADATA_ONLY",
                "eligible_for_publication": False, "financial_evidence_verified": False,
                "review_status": "UNVERIFIED_DISCOVERY_LEAD",
            },
            {
                "company_id": "fathom", "candidate_company": "Fathom Analytics",
                "title": "Fathom expands analytics", "source_url": "https://usefathom.com/blog/expands",
                "published_on": "2026-09-21",
                "source_kind": "FIRST_PARTY_RSS_METADATA_ONLY",
                "eligible_for_publication": False, "financial_evidence_verified": False,
                "review_status": "UNVERIFIED_DISCOVERY_LEAD",
            },
        ],
    }


class PrivateETL(unittest.TestCase):
    def test_cleans_merges_duplicates_and_preserves_source_boundaries(self):
        result = etl.clean_pipeline(hn(), rss(), today=DAY)
        self.assertEqual(result["raw_candidate_count"], 5)
        self.assertEqual(result["accepted_unique_count"], 4)
        self.assertEqual(result["duplicate_reference_count"], 1)
        self.assertEqual(result["rejection_count"], 1)
        self.assertEqual(result["quarantine"], [{"channel": "HN", "reason": "RESTRICTED_MARKETPLACE_LINK"}])
        self.assertEqual(result["network_requests_added"], 0)
        self.assertFalse(result["publication_allowed"])
        self.assertEqual(result["financial_claims_verified"], 0)
        self.assertEqual(result["legal_entities_verified"], 0)
        self.assertFalse(result["source_health"]["HN"]["successful_requests_confirmed"])
        self.assertEqual(result["source_health"]["HN"]["reported_candidate_errors"], 1)
        record = next(row for row in result["records"] if row["canonical_url"].endswith("/blog/finances"))
        self.assertEqual(set(record["channels"]), {"HN_PUBLIC_INDEX","OFFICIAL_PUBLISHER_RSS"})
        self.assertEqual(len(record["reference_urls"]), 2)
        self.assertEqual(record["searched_case_ids"], ["fathom"])
        self.assertEqual(record["published_on"], "2026-09-20")
        self.assertEqual(record["status"], "NEEDS_ORIGINAL_SOURCE_REVIEW")

    def test_duplicate_across_two_searches_is_not_independent_confirmation(self):
        document=hn()
        document["candidates"][1]["stories"] = [hit(123)]
        result=etl.clean_pipeline(document,None,today=DAY)
        match=next(r for r in result["records"] if r["canonical_url"].endswith("/blog/finances"))
        self.assertEqual(set(match["searched_case_ids"]), {"fathom","kit"})
        self.assertIn("MULTIPLE_SEARCH_QUERIES_NOT_INDEPENDENT_CONFIRMATION",match["identity_hints"])
        self.assertFalse(match["company_identity_verified"])

    def test_short_brand_or_search_only_never_proves_identity(self):
        result=etl.clean_pipeline(hn(),None,today=DAY)
        kit=next(r for r in result["records"] if "kit" in r["searched_case_ids"])
        self.assertIn("AMBIGUOUS_SHORT_BRAND",kit["identity_hints"])
        self.assertFalse(kit["financial_evidence_verified"])
        self.assertEqual(result["source_health"]["HN"]["mode"], "READ_ONLY_ONLINE")

    def test_safe_urls_drop_queries_and_block_private_targets(self):
        url, issue=etl.safe_external_url("https://example.org/blog?a=b&utm_source=x#private")
        self.assertEqual(url,"https://example.org/blog")
        self.assertIsNone(issue)
        for url in (
            "https://app.acquire.com/public/123",
            "https://flippa.com/buy/something",
            "https://www.microns.io/listing",
            "https://empireflippers.com/listing"):
            _, reason=etl.safe_external_url(url)
            self.assertEqual(reason,"RESTRICTED_MARKETPLACE_LINK")
        for url in (
            "http://example.org/foo", "https://u:p@example.org/foo",
            "https://127.0.0.1/foo", "https://host.internal/p",
            "https://example.org:8443/page", "https://example.org/../secrets",
            "https://example.org\\@127.0.0.1", "https://192.168.0.1/meta"):
            _, reason=etl.safe_external_url(url)
            self.assertEqual(reason,"UNSAFE_EXTERNAL_URL",url)

    def test_reject_pretend_financial_evidence_or_bad_policy(self):
        report=hn()
        report["candidates"][0]["stories"][0]["financial_evidence"]=True
        with self.assertRaisesRegex(ValueError,"elevated"):
            etl.clean_pipeline(report,None,today=DAY)
        report=hn()
        report["network_requests_max"]=100
        with self.assertRaises(ValueError):
            etl.clean_pipeline(report,None,today=DAY)
        report=hn()
        report["candidates"][0]["name"]="Another Company"
        with self.assertRaisesRegex(ValueError,"brand"):
            etl.clean_pipeline(report,None,today=DAY)
        report=rss()
        report["records"][0]["financial_evidence_verified"]=True
        with self.assertRaisesRegex(ValueError,"proof"):
            etl.clean_pipeline(None,report,today=DAY)

    def test_date_requires_real_calendar_and_utc_temporal_checks(self):
        self.assertEqual(etl.published_day("2026-09-20T12:30:00Z",DAY),"2026-09-20")
        self.assertEqual(etl.published_day("2026-10-20",DAY),None)
        self.assertEqual(etl.published_day("2026-01-01T12:30:00",DAY),None)
        self.assertEqual(etl.published_day("2026-02-30",DAY),None)

    def test_prior_report_allows_incremental_delta_with_no_network(self):
        first=etl.clean_pipeline(hn(),None,today=DAY)
        next_report=etl.clean_pipeline(hn(),None,previous=first,today=DAY)
        self.assertEqual(next_report["new_to_private_review_count"],0)
        self.assertTrue(all(row["novelty"]=="ALREADY_IN_PRIOR_PRIVATE_REPORT" for row in next_report["records"]))
        bad=dict(first,publication_allowed=True)
        with self.assertRaises(ValueError):
            etl.clean_pipeline(hn(),None,previous=bad,today=DAY)

    def test_cli_output_private_and_fixture_not_live_without_second_source(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            source=folder/"hn.json"
            target=folder/"clean.json"
            source.write_text(json.dumps(hn()),encoding="utf-8")
            proc=subprocess.run([sys.executable,str(ROOT/"scripts/research/p433_private_evidence_etl.py"),
                "--hn",str(source),"--output",str(target)],
                cwd=ROOT, capture_output=True, text=True,timeout=12)
            self.assertEqual(proc.returncode,0,proc.stderr)
            data=json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["mode"],"OFFLINE_DETERMINISTIC_CLEANING")
            self.assertEqual(data["accepted_unique_count"],3)
            self.assertEqual(data["network_requests_added"],0)
            self.assertFalse(data["publication_allowed"])

    def test_all_repo_public_destination_prohibited(self):
        for path in (
            ROOT/"config/p424_project_research_evidence.json",
            ROOT/"web/dist/something.json",
            ROOT/"docs/private.json",
            ROOT/"scripts/private.json",
        ):
            with self.assertRaises(ValueError):
                etl.private_path(path)

    def test_bounded_http_receipts_detect_total_and_partial_failure(self):
        with patch.object(scanner, "lookup", side_effect=[TimeoutError()] * 7) as mocked:
            failed = scanner.run(DAY, 6, True)
        self.assertEqual(mocked.call_count, 7)
        self.assertEqual(failed["network_requests_attempted"], 7)
        self.assertEqual(failed["network_requests_successful"], 0)
        self.assertEqual(failed["network_requests_failed"], 7)
        self.assertEqual(failed["scan_health"], "ALL_REQUESTS_FAILED")
        cleaned = etl.clean_pipeline(failed, None, today=DAY)
        self.assertFalse(cleaned["source_health"]["HN"]["successful_requests_confirmed"])
        self.assertEqual(cleaned["source_health"]["HN"]["scan_health"], "ALL_REQUESTS_FAILED")
        with patch.object(scanner, "lookup",
                          side_effect=[[], [], [], TimeoutError(), [], [], []]):
            partial = scanner.run(DAY, 6, True)
        self.assertEqual(partial["network_requests_successful"], 6)
        self.assertEqual(partial["network_requests_failed"], 1)
        self.assertEqual(partial["scan_health"], "PARTIAL_HTTP_SUCCESS")
        cleaned = etl.clean_pipeline(partial, None, today=DAY)
        self.assertTrue(cleaned["source_health"]["HN"]["successful_requests_confirmed"])
        forged = dict(partial, network_requests_successful=7)
        with self.assertRaisesRegex(ValueError, "Contradictory"):
            etl.clean_pipeline(forged, None, today=DAY)

    def test_existing_dedicated_daily_slot_not_expanded(self):
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 */6 * * *'"),1)
        self.assertIn("p433_private_evidence_etl.py --hn",wf)
        self.assertIn("p433_clean_review.json",wf)
        self.assertNotIn("p432_publisher_rss_probe.py --online",wf)
        source=(ROOT/"scripts/research/p433_private_evidence_etl.py").read_text(encoding="utf-8")
        for prohibited in ("urlopen(","requests.get(", "supabase.co","TinyFish","playwright"):
            self.assertNotIn(prohibited,source)


if __name__=="__main__":
    unittest.main()
