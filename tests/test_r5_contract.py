import json, subprocess, sys, unittest
from pathlib import Path

class TestR5Contract(unittest.TestCase):
    def test_public_projection_and_api_contract(self):
        sql=Path("db/migrations/0016_public_projection.sql").read_text(encoding="utf-8")
        fn=Path("supabase/functions/public-feed/index.ts").read_text(encoding="utf-8")
        for token in ["public_opportunity_catalog_v01","public_github_evidence_v01","public_market_evidence_v01","public_system_stats_v01"]:
            self.assertIn(token,sql)
        self.assertIn("security_invoker=true",sql.replace(" ",""))
        self.assertNotIn("raw_items",fn)
        self.assertIn('view === "detail"',fn)
        self.assertIn("cache-control",fn)
        wrangler=Path("wrangler.toml").read_text(encoding="utf-8")
        self.assertIn('pages_build_output_dir = "./web/dist"',wrangler)

    def test_static_build_fixture(self):
        p=subprocess.run([sys.executable,"web/build.py"],capture_output=True,text=True,check=True)
        result=json.loads(p.stdout.strip())
        self.assertEqual(result["status"],"PASS")
        self.assertTrue(Path("web/dist/index.html").exists())
        self.assertTrue(Path("web/dist/opportunity/solo-saas/index.html").exists())
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        self.assertIn("多源验证",index)
        self.assertIn("单源观察",index)

if __name__=="__main__":
    unittest.main()
