"""P4.12 production candidate: rebuild and audit isolated Pages output."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/"web"/"dist"
BUILDER=ROOT/"web"/"build.py"
RELEASE=ROOT/"scripts"/"release"/"p412_build_public.py"
AUDIT=ROOT/"scripts"/"security"/"p411_audit_public_artifacts.py"

class TestP412ProductionCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=subprocess.run([sys.executable,str(BUILDER)],cwd=ROOT,text=True,capture_output=True,timeout=50)
        if build.returncode!=0:raise AssertionError("Base build failed: "+build.stderr)
        build=subprocess.run([sys.executable,str(RELEASE)],cwd=ROOT,text=True,capture_output=True,timeout=40)
        if build.returncode!=0:raise AssertionError("P4.12 release build failed: "+build.stderr)

    def test_release_home_is_public_product_not_engineering_demo(self):
        content=(DIST/"index.html").read_text(encoding="utf-8")
        for expected in ["发现海外项目","Easlo","Louise Lennox","Playfair+Display",
                         "family=Inter","data:image/webp;base64,","3D","/#item-"]:
            if expected=="3D":
                self.assertIn('id="ring"',content)
            elif expected=="/#item-":
                self.assertIn("#item-",content)
            else:self.assertIn(expected,content)
        self.assertNotIn("此文件为独立网站预览",content)
        self.assertIn('href="/privacy/"',content)
        self.assertIn('rel="canonical"',content)
        self.assertIn("见势",content)
        self.assertEqual(content.count("<style>"),1)
        self.assertEqual(content.count("<script>"),1)

    def test_existing_bookmarks_are_compatible(self):
        paths={
            "opportunities/index.html":"/#archive",
            "today/index.html":"/",
            "rising/index.html":"/",
            "build/index.html":"/",
            "content/index.html":"/",
            "account/index.html":"/",
            "opportunity/amazon-kdp-publishing/index.html":"/#item-kdp",
            "opportunity/digital-product-business/index.html":"/#item-digital",
            "opportunity/vertical-industry-saas/index.html":"/#item-saas",
            "opportunity/solo-saas/index.html":"/#item-saas",
        }
        for path,dest in paths.items():
            content=(DIST/path).read_text(encoding="utf-8")
            self.assertIn(dest,content,path)
            self.assertIn("页面已更新",content,path)
            self.assertIn("noindex,follow",content,path)

    def test_public_build_has_no_repository_internal_directories(self):
        for name in [".github","config","db","docs","scripts","src","supabase","tests","fixtures"]:
            self.assertFalse((DIST/name).exists(),name)
        self.assertEqual((DIST/"sitemap.xml").read_text().count("<url>"),3)
        self.assertTrue((DIST/"validation"/"index.html").is_file())
        self.assertIn("商业证据研究",(DIST/"validation"/"index.html").read_text(encoding="utf-8"))
        self.assertFalse((DIST/"search-index.json").exists())
        self.assertTrue((DIST/"privacy"/"index.html").exists())
        self.assertIn("Cache-Control: no-store",(DIST/"_headers").read_text())

    def test_release_passes_source_disclosure_scan(self):
        audit=subprocess.run([sys.executable,str(AUDIT),str(DIST)],
             cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(audit.returncode,0,audit.stderr)

if __name__=="__main__":
    unittest.main()
