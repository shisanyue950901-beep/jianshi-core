import subprocess, sys, unittest
from pathlib import Path

class TestR88OpportunityAcceleration(unittest.TestCase):
    def test_acceleration_view_contract(self):
        sql=Path("db/migrations/0041_opportunity_github_acceleration.sql").read_text(encoding="utf-8")
        for token in [
            "opportunity_github_acceleration_v01",
            "github_rising_current",
            "rising_repo_count",
            "recent_stars_per_day_sum",
            "avg_recent_velocity_score",
            "max_recent_velocity_score",
        ]:
            self.assertIn(token,sql)
        self.assertIn("coalesce(a.rising_repo_count,0) desc",sql)

    def test_core_scores_not_redefined(self):
        sql=Path("db/migrations/0041_opportunity_github_acceleration.sql").read_text(encoding="utf-8")
        self.assertNotIn("opportunity_scored_v01",sql)
        self.assertNotIn("refresh_opportunity_scores_v01",sql)
        self.assertNotIn("OPP_V0.3",sql)

    def test_public_api_and_ui_explain_acceleration(self):
        fn=Path("supabase/functions/public-feed/index.ts").read_text(encoding="utf-8")
        build=Path("web/build.py").read_text(encoding="utf-8")
        self.assertIn("opportunity_github_acceleration_v01",fn)
        self.assertIn("acceleration:",fn)
        self.assertIn("技术加速度",build)
        self.assertIn("不替代真实商业证据",build)
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)

if __name__=="__main__":
    unittest.main()
