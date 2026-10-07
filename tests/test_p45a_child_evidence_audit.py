import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestP45AChildEvidenceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((ROOT/"config/child_opportunity_evidence_audit_v1.json").read_text(encoding="utf-8"))
        cls.doc=(ROOT/"docs/P45A_CHILD_EVIDENCE_AUDIT.md").read_text(encoding="utf-8")

    def test_audits_exactly_first_eight(self):
        self.assertEqual(len(self.cfg["children"]),8)
        self.assertEqual(self.cfg["publication_summary"]["worth_research"],8)

    def test_sample_count_is_not_source_diversity(self):
        self.assertEqual(self.cfg["commercial_source_diversity"],1)
        self.assertTrue(self.cfg["rules"]["direct_sample_count_is_not_source_diversity"])
        self.assertTrue(self.cfg["rules"]["direct_single_source_can_prove_existence_but_not_multi_source_validation"])

    def test_no_child_is_promoted_to_worth_doing(self):
        self.assertEqual(self.cfg["publication_summary"]["worth_doing"],0)
        self.assertEqual(self.cfg["publication_summary"]["high_confidence_validated"],0)
        self.assertTrue(all(not x["high_confidence_validated"] for x in self.cfg["children"]))

    def test_overclaiming_names_are_flagged(self):
        by_slug={x["slug"]:x for x in self.cfg["children"]}
        self.assertEqual(by_slug["vertical-micro-saas"]["recommended_title"],"垂直行业 SaaS")
        self.assertEqual(by_slug["affiliate-seo-content-site"]["recommended_title"],"联盟营销 / 内容站")
        self.assertEqual(by_slug["crossborder-dtc-brand"]["recommended_title"],"非 Amazon 电商品牌")

    def test_direct_counts_are_frozen(self):
        by_slug={x["slug"]:x for x in self.cfg["children"]}
        expected={
            "vertical-micro-saas":6,
            "affiliate-seo-content-site":11,
            "amazon-fba-niche-brand":77,
            "youtube-niche-media":16,
            "digital-product-business":15,
            "newsletter-media-business":2,
            "amazon-kdp-publishing":11,
            "crossborder-dtc-brand":24,
        }
        self.assertEqual({k:by_slug[k]["direct_marketplace_count"] for k in expected},expected)

    def test_no_production_or_auto_publish(self):
        self.assertFalse(self.cfg["rules"]["auto_publish"])
        self.assertIn("P45A_AUTO_MAPPING = NOT_ENABLED",self.doc)
        self.assertIn("P45A_PRODUCTION_CHANGE = FALSE",self.doc)
        self.assertIn("P45A_PUBLIC_SITE_CHANGE = FALSE",self.doc)

if __name__=="__main__":
    unittest.main()
