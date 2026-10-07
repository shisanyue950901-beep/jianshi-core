import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SQL=ROOT/"scripts"/"p48b_user_test_report.sql"


class TestP48BUserTestReporting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=SQL.read_text(encoding="utf-8")

    def test_report_is_strictly_read_only(self):
        scrubbed=re.sub(r"--.*?$","",self.sql,flags=re.MULTILINE)
        for token in [
            r"\binsert\b",r"\bupdate\b",r"\bdelete\b",r"\bcreate\b",
            r"\balter\b",r"\bdrop\b",r"\btruncate\b",r"\bgrant\b",
            r"\brevoke\b",r"\bcall\b"
        ]:
            self.assertIsNone(re.search(token,scrubbed,re.IGNORECASE),token)

    def test_epoch_and_sample_gate_are_frozen(self):
        self.assertIn("2026-10-07T15:49:06Z",self.sql)
        self.assertIn("30::integer",self.sql)
        self.assertIn("ENOUGH_FOR_FIRST_REVIEW",self.sql)
        self.assertIn("ACCUMULATING",self.sql)

    def test_all_six_target_projects_are_locked(self):
        for slug in [
            "vertical-industry-saas",
            "amazon-fba-niche-brand",
            "digital-product-business",
            "affiliate-content-site",
            "amazon-kdp-publishing",
            "agency-business",
        ]:
            self.assertIn(slug,self.sql)

    def test_four_primary_metrics_are_present(self):
        for metric in [
            "entry_click_rate_pct",
            "engaged_30s_rate_pct",
            "scroll_90_rate_pct",
            "second_target_project_rate_pct",
        ]:
            self.assertIn(metric,self.sql)

    def test_second_project_metric_is_target_scoped(self):
        self.assertIn("distinct_target_projects_viewed",self.sql)
        self.assertIn("count(distinct e.opportunity_slug)",self.sql)


    def test_acquisition_uses_session_entry_not_detail_event(self):
        self.assertIn("target_session_acquisition",self.sql)
        self.assertIn("from epoch_events e",self.sql)
        self.assertIn("join target_detail_sessions d using(session_id)",self.sql)
        self.assertIn("FIRST_EVENT_IN_TARGET_DETAIL_SESSION",self.sql)
        self.assertNotIn("target_first_detail",self.sql)


if __name__=="__main__":
    unittest.main()
