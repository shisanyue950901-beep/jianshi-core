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
        self.assertIn("综合指标快照",today)
        self.assertIn("历史序列仍在积累",today)
        rising=Path("web/dist/rising/index.html").read_text(encoding="utf-8")
        build=Path("web/dist/build/index.html").read_text(encoding="utf-8")
        content=Path("web/dist/content/index.html").read_text(encoding="utf-8")
        self.assertIn("近期信号变化",rising)
        self.assertIn("执行条件信号",build)
        self.assertIn("内容传播信号",content)
        sitemap=Path("web/dist/sitemap.xml").read_text(encoding="utf-8")
        for route in ["/today/","/rising/","/build/","/content/"]:
            self.assertIn(route,sitemap)
        rank_sql=Path("db/migrations/0020_r7_rank_policy.sql").read_text(encoding="utf-8")
        self.assertIn("c.public_ready desc,c.overall_score desc",rank_sql)

if __name__=="__main__":
    unittest.main()
