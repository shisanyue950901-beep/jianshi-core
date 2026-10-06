import subprocess, sys, unittest
from pathlib import Path

class TestR7DailyProduct(unittest.TestCase):
    def test_daily_schema_contract(self):
        sql=Path("db/migrations/0019_daily_opportunity_snapshots.sql").read_text(encoding="utf-8")
        for token in [
            "opportunity_daily_snapshots",
            "refresh_opportunity_daily_snapshots_v01",
            "public_opportunity_changes_v01",
            "public_daily_brief_v01",
            "Asia/Shanghai",
            "ACCUMULATING",
            "NEWLY_VALIDATED",
        ]:
            self.assertIn(token,sql)

    def test_public_feed_daily_contract(self):
        fn=Path("supabase/functions/public-feed/index.ts").read_text(encoding="utf-8")
        self.assertIn('view === "daily"',fn)
        self.assertIn("history_ready",fn)
        self.assertIn("public_daily_brief_v01",fn)

    def test_static_daily_pages_and_seo(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        for path in [
            "web/dist/today/index.html",
            "web/dist/rising/index.html",
            "web/dist/build/index.html",
            "web/dist/content/index.html",
            "web/dist/sitemap.xml",
            "web/dist/robots.txt",
        ]:
            self.assertTrue(Path(path).exists(),path)
        today=Path("web/dist/today/index.html").read_text(encoding="utf-8")
        self.assertIn("今日机会",today)
        self.assertIn("历史正在积累",today)
        home=Path("web/dist/index.html").read_text(encoding="utf-8")
        self.assertIn('/build/',home)
        self.assertIn('/content/',home)
        self.assertIn('/rising/',home)

if __name__=="__main__":
    unittest.main()
