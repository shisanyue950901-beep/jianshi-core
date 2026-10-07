import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"p48c_test_links.py"
DOC=ROOT/"docs"/"P48C_FIRST_USER_TEST.md"
ANALYTICS=ROOT/"web"/"static"/"analytics.js"


class TestP48CControlledTestTraffic(unittest.TestCase):
    def test_link_generator_has_one_primary_campaign(self):
        out=subprocess.run(
            [sys.executable,str(SCRIPT)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn("utm_source=manual_invite",out)
        self.assertIn("utm_medium=private_share",out)
        self.assertIn("utm_campaign=p48_first100",out)
        self.assertEqual(out.count("utm_campaign=p48_first100"),1)

    def test_all_six_interview_links_exist(self):
        out=subprocess.run(
            [sys.executable,str(SCRIPT)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        for slug in [
            "vertical-industry-saas",
            "amazon-fba-niche-brand",
            "digital-product-business",
            "affiliate-content-site",
            "amazon-kdp-publishing",
            "agency-business",
        ]:
            self.assertIn(f"/opportunity/{slug}/?",out)
        self.assertIn("utm_campaign=p48_project_interview",out)

    def test_internal_qa_links_are_untagged_and_suppressed(self):
        out=subprocess.run(
            [sys.executable,str(SCRIPT)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn("/?qa=1",out)
        client=ANALYTICS.read_text(encoding="utf-8")
        self.assertIn("jianshi_analytics_qa_session",client)
        self.assertIn('qa==="1"',client)

    def test_distribution_plan_stays_platform_neutral(self):
        text=DOC.read_text(encoding="utf-8")
        for token in ["抖音","小红书","B站","TikTok","YouTube"]:
            self.assertNotIn(token,text)
        self.assertIn("不选择具体平台渠道",text)

    def test_no_outreach_is_claimed(self):
        text=DOC.read_text(encoding="utf-8")
        self.assertIn("P48C_OUTREACH_SENT = FALSE",text)
        self.assertIn("不主动发送任何邀请",text)


if __name__=="__main__":
    unittest.main()
