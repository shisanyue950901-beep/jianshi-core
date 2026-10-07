import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestP414PyPIStagingValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=(ROOT/"db/migrations/0053_pypi_staging_source.sql").read_text(encoding="utf-8")
        cls.edge=(ROOT/"supabase/functions/collect-pypi-signals/index.ts").read_text(encoding="utf-8")
        cls.doc=(ROOT/"docs/P414_PYPI_STAGING_VALIDATION.md").read_text(encoding="utf-8")

    def test_official_rss_and_json_only(self):
        self.assertIn("OFFICIAL_RSS_PLUS_JSON_API",self.sql)
        self.assertIn("https://pypi.org/rss/packages.xml",self.sql)
        self.assertIn("https://pypi.org/rss/updates.xml",self.sql)
        self.assertIn("https://pypi.org/pypi",self.edge)

    def test_no_bigquery_or_deprecated_downloads(self):
        self.assertIn("bigquery_used:false",self.edge)
        self.assertIn("deprecated_downloads_used:false",self.edge)
        self.assertNotIn("info.downloads",self.edge)
        self.assertIn("本阶段只验证",self.doc)

    def test_content_minimization(self):
        self.assertIn("full_description_stored:false",self.edge)
        self.assertIn("keyword_count",self.edge)
        self.assertNotIn("description:info.description",self.edge.replace(" ",""))
        self.assertIn("LIMITED_PUBLIC_PACKAGE_METADATA_ONLY_NO_PACKAGE_CONTENT",self.sql)

    def test_shadow_only_and_no_scoring_change(self):
        self.assertIn("'PYPI_PACKAGE'",self.sql)
        self.assertIn("'TECHNICAL_SUPPLY'",self.sql)
        self.assertIn("false,",self.sql)
        self.assertIn("scoring_changed:false",self.edge)
        lower=self.sql.lower()
        self.assertNotIn("opportunity_rank_current",lower)
        self.assertNotIn("public_opportunity_catalog_v01",lower)

    def test_quality_filter_prioritizes_business_breadth(self):
        self.assertIn("EXPANSION_CATEGORIES", self.edge)
        self.assertIn("candidateQuality", self.edge)
        self.assertIn("candidate_quality_score", self.edge)
        self.assertIn('priority:"HIGH"|"MEDIUM"|"LOW"', self.edge)
        self.assertIn("score>=4", self.edge)

    def test_github_cross_evidence_is_exact_not_url_presence(self):
        self.assertIn("github_repositories", self.edge)
        self.assertIn("github_overlap_current_corpus", self.edge)
        self.assertIn("TECHNICAL_ECOSYSTEM_CONFIRMATION", self.edge)
        self.assertIn("TECHNICAL_DISCOVERY", self.edge)
        self.assertIn("candidate_github_linked_not_in_current_corpus", self.edge)

    def test_no_cron_in_staging_experiment(self):
        self.assertNotIn("cron.schedule",self.sql.lower())
        self.assertNotIn("cron.schedule",self.edge.lower())


if __name__=="__main__":
    unittest.main()
