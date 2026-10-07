import subprocess, sys, unittest
from pathlib import Path

class TestR6ChineseDataPresentation(unittest.TestCase):
    def test_schema_has_chinese_summary_contract(self):
        sql=Path("db/migrations/0018_chinese_public_summaries.sql").read_text(encoding="utf-8")
        self.assertIn("summary_zh",sql)
        self.assertIn("display_title_zh",sql)
        self.assertIn("refresh_github_summary_zh_v01",sql)

    def test_fixture_build_hides_raw_english_descriptions(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        detail=Path("web/dist/opportunity/solo-saas/index.html").read_text(encoding="utf-8")
        self.assertNotIn("Agent framework example",index)
        self.assertNotIn("$20K Per Month SaaS Business",detail)
        self.assertIn("技术供给证据",detail)
        self.assertIn("商业验证",detail)
        self.assertIn("互联网商业样本",detail)

if __name__=="__main__":
    unittest.main()
