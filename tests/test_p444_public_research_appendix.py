"""P4.44 actual release-chain contract for evidence-only research appendix."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"web"/"dist"
SLUGS=(
    "vertical-industry-saas","amazon-fba-niche-brand",
    "digital-product-business","affiliate-content-site",
    "amazon-kdp-publishing","agency-business",
)


class PublicResearchAppendixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        for script in ("web/build.py","scripts/release/p412_build_public.py"):
            proc=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,env=env,
                text=True,capture_output=True,timeout=55)
            if proc.returncode:
                raise AssertionError(f"{script} failed: {proc.stderr[:1500]}")
        cls.home=(DIST/"index.html").read_text(encoding="utf-8")
        cls.index=(DIST/"research/index.html").read_text(encoding="utf-8")

    def test_primary_public_home_preserves_original_interaction(self):
        self.assertIn("JIANSHI",self.home)
        self.assertIn('id="ring"',self.home)
        self.assertIn('id="lb"',self.home)
        # P4.42: preserve eight gallery covers and add one audited AI hero image.\n        self.assertEqual(self.home.count("data:image/webp;base64,"),9)\n        self.assertIn('id="j2"',self.home)\n        self.assertIn('id="ring"',self.home)
        self.assertEqual(self.home.count("<script>"),1)
        self.assertEqual(self.home.count("<style>"),1)
        self.assertIn('href="/research/"',self.home)
        self.assertIn("查看六类商业项目的匿名统计",self.home)

    def test_appendix_index_is_public_aggregate_only(self):
        self.assertIn('id="category-comparison"',self.index)
        self.assertIn('class="compare-table-v2"',self.index)
        self.assertEqual(self.index.count('<tr><th scope="row"><a href="/research/'),6)
        self.assertIn('href="/research/vertical-industry-saas/"',self.index)
        self.assertIn('href="/research/#reading-metrics"',self.index) if 'href="/research/#reading-metrics"' in self.index else self.assertIn('id="reading-metrics"',self.index)
        self.assertIn('<meta name="robots" content="noindex,follow">',self.index)
        self.assertIn('href="https://jianshi-bua.pages.dev/research/"',self.index)

    def test_six_anonymous_category_pages_and_canonicals(self):
        for slug in SLUGS:
            path=DIST/"research"/slug/"index.html"
            self.assertTrue(path.is_file(),slug)
            html=path.read_text(encoding="utf-8")
            for required in (
                "项目研究档案",'id="sample-scope"','id="sample-metrics"',
                'id="sample-examples"','id="sample-boundary"',
                "noindex,nofollow","class=\"data-freshness-v2\"",
            ):
                self.assertIn(required,html,(slug,required))
            self.assertIn(f'href="https://jianshi-bua.pages.dev/research/{slug}/"',html)
            self.assertNotIn('href="/opportunity/',html)

    def test_preserve_old_bookmarks_and_zero_research_collector_expansion(self):
        old=(DIST/"opportunities/index.html").read_text(encoding="utf-8")
        self.assertIn("/#archive",old)
        self.assertIn("页面已更新",old)
        main=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertNotIn("urlopen(",main)
        self.assertNotIn("requests.get(",main)
        self.assertNotIn("mcp__TinyFish",main)
        self.assertIn('anonymous_studies=publish_public_research_appendix()',main)

    def test_repeated_release_uses_pre_release_mirror(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/release/p412_build_public.py")],
                            cwd=ROOT,env=env,text=True,capture_output=True,timeout=50)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn('id="category-comparison"', (DIST/"research/index.html").read_text(encoding="utf-8"))
        self.assertIn("/#archive", (DIST/"opportunities/index.html").read_text(encoding="utf-8"))

    def test_source_privacy_scanner_accepts_final_release(self):
        result=subprocess.run([sys.executable,str(ROOT/"scripts/security/p411_audit_public_artifacts.py"),str(DIST)],
            cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        for page in (self.home,self.index,*(
            (DIST/"research"/slug/"index.html").read_text(encoding="utf-8") for slug in SLUGS
        )):
            for disallowed in (
                "Empire Flippers","empireflippers","listing_number",
                "source_updated_at","source_ref_ids","china_screening",
                "first_validation","editorial_judgement",
            ):
                self.assertNotIn(disallowed,page)

if __name__=="__main__":
    unittest.main()
