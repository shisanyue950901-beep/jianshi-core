"""P4.32 source-use licensing gates and publisher RSS private intake."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/research"))
import p432_publisher_rss_probe as probe

EXAMPLE = b"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>Fathom Analytics Blog</title>
<item><title>Fathom business revenue growth</title>
<link>https://usefathom.com/blog/revenue-growth</link>
<pubDate>Mon, 20 Apr 2026 10:00:00 +0000</pubDate>
<description>Secret article body not for archival</description></item>
<item><title>Duplicate</title>
<link>https://usefathom.com/blog/revenue-growth</link></item>
<item><title>Outside provider</title>
<link>https://app.acquire.com/public/listing</link></item>
<item><title>Tracking link</title>
<link>https://usefathom.com/blog/tracking?token=private</link></item>
</channel></rss>"""


class RightsGatedFeedTest(unittest.TestCase):
    def test_registry_is_explicit_and_restricted_providers_remain_blocked(self):
        p = probe.load_policy()
        self.assertEqual(len(p), 9)
        self.assertEqual(p["fathom-rss"]["max_requests_per_run"], 1)
        self.assertEqual(p["fathom-rss"]["max_items_per_run"], 10)
        self.assertEqual(p["hn-algolia"]["daily_budget_shared"], 7)
        for source in ("acquire-listings", "flippa-listings", "microns-listings", "indiehackers-pages"):
            self.assertEqual(p[source]["automated_fetch"], "FORBIDDEN")
        self.assertEqual(p["buffer-open"]["automated_fetch"],"DISABLED_TERMS_NOT_VERIFIED_FOR_BULK")

    def test_metadata_only_drops_fulltext_and_deduplicates(self):
        items = probe.parse_feed(EXAMPLE)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source_url"],"https://usefathom.com/blog/revenue-growth")
        self.assertEqual(items[0]["published_on"],"2026-04-20")
        self.assertEqual(items[0]["review_status"],"UNVERIFIED_DISCOVERY_LEAD")
        self.assertFalse(items[0]["eligible_for_publication"])
        self.assertNotIn("Secret article body",json.dumps(items))

    def test_unsafe_urls_and_marketplace_urls_rejected(self):
        for u in ("http://usefathom.com/blog/growth",
                  "https://usefathom.com.evil.org/blog/growth",
                  "https://u:p@usefathom.com/blog/growth",
                  "https://usefathom.com:8443/blog/growth",
                  "https://usefathom.com/blog/growth?a=1",
                  "https://app.acquire.com/public/123",
                  "https://flippa.com/buy/123",
                  "https://usefathom.com/blog/../config"):
            self.assertIsNone(probe.safe_post_link(u),u)

    def test_reject_arbitrary_xml_entity_and_overbudget(self):
        with self.assertRaises(ValueError):
            probe.parse_feed(b'<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///etc/passwd">]>' + EXAMPLE)
        with self.assertRaises(ValueError):
            probe.parse_feed(b"x" * (probe.MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            probe.parse_feed(b"<html><body>irrelevant</body></html>")
        self.assertEqual(probe.safe_date("not a date"),None)

    def test_unknown_publisher_identity_is_rejected(self):
        wrong=EXAMPLE.replace(b"Fathom Analytics Blog",b"Unauthorized Publisher")
        with self.assertRaises(ValueError):
            probe.parse_feed(wrong)

    def test_offline_cli_does_not_claim_network_request_or_admit(self):
        with tempfile.TemporaryDirectory() as d:
            tmp=Path(d)
            feed=tmp/"feed.xml"
            out=tmp/"private.json"
            feed.write_bytes(EXAMPLE)
            proc=subprocess.run([
                sys.executable,str(ROOT/"scripts/research/p432_publisher_rss_probe.py"),
                "--fixture",str(feed),"--output",str(out)
            ],cwd=ROOT,capture_output=True,text=True,timeout=12)
            self.assertEqual(proc.returncode,0,proc.stderr)
            result=json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result["mode"],"OFFLINE_FIXTURE_NOT_LIVE")
            self.assertEqual(result["network_requests"],0)
            self.assertEqual(result["records_count"],1)
            self.assertFalse(result["eligible_for_publication"])
            self.assertEqual(result["financial_claims_verified"],0)
            self.assertFalse(result["source_fulltext_stored"])
            self.assertEqual(len(result["source_sha256"]),64)

    def test_never_write_to_public_paths_or_repo(self):
        for dest in ("web/dist/private.json", "config/p424_project_research_evidence.json",
                     "docs/collected-source.xml"):
            with self.assertRaises(ValueError):
                probe.private_destination(ROOT/dest)

    def test_safe_failure_on_redirect_without_following(self):
        with self.assertRaises(ValueError):
            probe.NoRedirect().redirect_request(None,None,302,"redirect",{},
                                                "https://elsewhere.example/rss")

    def test_editorial_snapshot_preserves_period_and_never_auto_admits(self):
        obs=json.loads((ROOT/"config/p432_private_editorial_observations.json").read_text(encoding="utf-8"))
        self.assertFalse(obs["publication_allowed"])
        self.assertFalse(obs["automatic_admission_allowed"])
        self.assertFalse(obs["source_text_copied"])
        self.assertIsNone(obs["raw_response_sha256"])
        self.assertEqual(len(obs["items"]),4)
        plausible=next(x for x in obs["items"] if x["case_id"]=="plausible")
        self.assertEqual(plausible["period"],"2026-01_to_2026-04")
        self.assertEqual(next(x["value"] for x in plausible["numeric_observations"]
                              if x["metric"]=="new_paid_subscribers_april"),1156)
        buffer_case=next(x for x in obs["items"] if x["case_id"]=="buffer")
        self.assertEqual(buffer_case["period"],"UNDATED_DYNAMIC_PAGE_VIEW")
        self.assertIsNone(buffer_case["published_on"])
        for row in obs["items"]:
            self.assertEqual(row["status"],"NEEDS_REVIEW")
            self.assertFalse(row["verified_revenue"])
            self.assertFalse(row["legal_entity_verified"])
        admitted=json.loads((ROOT/"config/p424_project_research_evidence.json").read_text(encoding="utf-8"))
        self.assertNotIn("buffer",{x["id"] for x in admitted["additional_evidence"]})

    def test_not_new_cron_paid_proxy_or_prod_database_writer(self):
        script=(ROOT/"scripts/research/p432_publisher_rss_probe.py").read_text(encoding="utf-8")
        for bad in ("TinyFish", "supabase.co", "requests.get(", "selenium",
                    "app.acquire.com/public","Cloudflare"):
            self.assertNotIn(bad,script)
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '55 */6 * * *'",wf)
        self.assertNotIn("p432_publisher_rss_probe.py",wf)


if __name__ == "__main__":
    unittest.main()
