import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestP44OpportunityCatalogExpansionDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((ROOT/"config/opportunity_catalog_candidates_v1.json").read_text(encoding="utf-8"))
        cls.doc=(ROOT/"docs/P44_OPPORTUNITY_CATALOG_EXPANSION_DESIGN.md").read_text(encoding="utf-8")

    def test_existing_six_are_parent_tracks(self):
        self.assertEqual(
            self.cfg["model"]["parent_tracks"],
            "EXISTING_6_OPPORTUNITIES_RETAINED_AS_EVIDENCE_AGGREGATION_LAYER",
        )
        self.assertEqual(self.cfg["model"]["user_facing_unit"],"CONCRETE_OPPORTUNITY")

    def test_parent_evidence_cannot_auto_validate_child(self):
        self.assertEqual(
            self.cfg["model"]["parent_evidence_inheritance"],
            "CONTEXT_ONLY_NOT_VALIDATION",
        )
        self.assertEqual(
            self.cfg["model"]["child_public_validation"],
            "REQUIRES_CHILD_SPECIFIC_EVIDENCE",
        )
        self.assertIn("INHERIT_PARENT_PUBLIC_READY_TO_CHILD",self.cfg["forbidden"])

    def test_first_batch_is_small_and_commercially_grounded(self):
        self.assertEqual(len(self.cfg["candidates"]),16)
        self.assertEqual(len(self.cfg["first_editorial_batch"]),8)
        stages={x["slug"]:x["stage"] for x in self.cfg["candidates"]}
        for slug in self.cfg["first_editorial_batch"]:
            self.assertEqual(stages[slug],"EDITORIAL_PRIORITY")

    def test_ai_only_candidates_are_not_promoted_as_validated(self):
        by_slug={x["slug"]:x for x in self.cfg["candidates"]}
        for slug in [
            "ai-ecommerce-video-tool",
            "ai-job-search-assistant",
            "ai-web-research-data-tool",
            "smb-agent-workflow-automation",
        ]:
            self.assertEqual(by_slug[slug]["stage"],"RESEARCH_CANDIDATE")
            self.assertIn("TECH_ONLY",by_slug[slug]["commercial_status"])

    def test_no_production_change(self):
        self.assertIn("PRODUCTION_CHANGE = FALSE",self.doc)
        self.assertIn("PUBLIC_SITE_CHANGE = FALSE",self.doc)
        self.assertIn("NEW_SOURCE_EXPANSION = PAUSED",self.doc)


if __name__=="__main__":
    unittest.main()
