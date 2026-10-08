import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/"web"/"build.py"
FEED = ROOT/"supabase"/"functions"/"public-feed"/"index.ts"

class TestP410PrivateSourcesAndChineseCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed=FEED.read_text(encoding="utf-8")
        cls.build=BUILD.read_text(encoding="utf-8")

    def test_live_api_has_no_raw_records_in_research_response(self):
        block=self.feed.split('if (view === "research")',1)[1].split('if (view === "detail")',1)[0]
        response=block.split("return json({",1)[1]
        for forbidden in [
            "public_title:", "listing_number:", "country_code:", "niches: row",
            "homepage_url:", "access_method:", "evidence_source:",
            "source_updated_at:", "first_made_money_at:", "listing_price:",
            "average_monthly_gross_revenue:", "source_url:",
        ]:
            self.assertNotIn(forbidden,response,forbidden)
        for required in ["display_name:","monthly_revenue_band:","monthly_profit_band:","asking_price_band:"]:
            self.assertIn(required,block)

    def test_legacy_api_does_not_return_raw_identifiers(self):
        self.assertIn("tech_signals: []",self.feed)
        self.assertIn("github: []",self.feed)
        self.assertIn("marketplace: []",self.feed)
        self.assertIn('"cache-control": "no-store, max-age=0"',self.feed)

    def test_fixture_site_has_no_source_exposure(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        visible=[
            ROOT/"web"/"dist"/"index.html",
            ROOT/"web"/"dist"/"opportunities"/"index.html",
            ROOT/"web"/"dist"/"opportunity"/"amazon-kdp-publishing"/"index.html",
            ROOT/"web"/"dist"/"opportunity"/"vertical-industry-saas"/"index.html",
            ROOT/"web"/"dist"/"opportunity"/"solo-saas"/"index.html",
        ]
        for path in visible:
            html=path.read_text(encoding="utf-8")
            for forbidden in [
                "Empire Flippers","empireflippers.com","官方 API","采集方式",
                "来源分类（原文）","Amazon KDP Business in the",
                "$20K Per Month SaaS Business","源更新时间：","listing_number",
            ]:
                self.assertNotIn(forbidden,html,str(path))
        page=visible[2].read_text(encoding="utf-8")
        self.assertIn("中文案例",page)
        self.assertIn("月营收区间",page)
        self.assertIn("月净利润区间",page)
        self.assertIn("报价区间",page)
        self.assertIn("noindex,nofollow",page)

if __name__=="__main__":
    unittest.main()
