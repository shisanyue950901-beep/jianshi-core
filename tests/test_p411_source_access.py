import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"web"/"build.py"
SCANNER=ROOT/"scripts"/"security"/"p411_audit_public_artifacts.py"
ACL=ROOT/"scripts"/"security"/"p411_revoke_source_views.sql"

class TestP411SourceAccess(unittest.TestCase):
    def test_source_revoke_contract_is_versioned(self):
        sql=ACL.read_text(encoding="utf-8")
        for name in [
            "marketplace_listing_history","public_market_evidence_v01",
            "public_github_evidence_v01","source_policy_effective_v01",
            "source_provenance_effective_v01","public_tech_signals_v01",
        ]:
            self.assertIn(name,sql)
        self.assertIn("from anon, authenticated",sql)
        self.assertIn("has_table_privilege('anon'",sql)

    def test_fixture_build_outputs_all_deny_controls(self):
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,check=True,capture_output=True,text=True)
        for parent in [ROOT/"web"/"dist",ROOT/"dist",ROOT/"public",ROOT]:
            self.assertTrue((parent/"_headers").is_file())
            self.assertTrue((parent/"_redirects").is_file())
        scan=subprocess.run([sys.executable,str(SCANNER),str(ROOT/"web"/"dist")],
                            cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(scan.returncode,0,scan.stderr)

    def test_scanner_rejects_raw_provider_and_listing_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            (folder/"_headers").write_text(
                (ROOT/"web"/"static"/"_headers").read_text(encoding="utf-8"),encoding="utf-8")
            (folder/"_redirects").write_text(
                (ROOT/"web"/"static"/"_redirects").read_text(encoding="utf-8"),encoding="utf-8")
            (folder/"index.html").write_text(
                "<html>Provider: Empire Flippers; listing_number=123</html>",encoding="utf-8")
            scan=subprocess.run([sys.executable,str(SCANNER),str(folder)],
                                cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(scan.returncode,0)
            self.assertIn("LEAK",scan.stderr)

if __name__=="__main__":
    unittest.main()
