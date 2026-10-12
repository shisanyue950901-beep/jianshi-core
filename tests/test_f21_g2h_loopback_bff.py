"""G2-H: execute real loopback HTTP test suite in default Python CI.

No Supabase, no external browser, no paid services. The synthetic server binds
127.0.0.1 only and cannot run with actual database credentials.
"""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

class G2HLoopback(unittest.TestCase):
    def test_node_http_integration_not_just_static_contracts(self):
        node=shutil.which("node")
        self.assertIsNotNone(node,"G2-H requires Node for HTTP E2E; fail closed")
        r=subprocess.run([node,"--test","tests/g2h_loopback_bff.test.mjs"],
                         cwd=ROOT,text=True,capture_output=True,timeout=50)
        self.assertEqual(r.returncode,0,(r.stdout+"\n"+r.stderr)[-4500:])
        self.assertIn("# fail 0",r.stdout)
        self.assertIn("# pass 5",r.stdout)

    def test_public_release_does_not_import_qa_server(self):
        builder=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        publish=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        test=(ROOT/"tests/g2h_loopback_bff.test.mjs").read_text(encoding="utf-8")
        self.assertNotIn("g2h_loopback_bff",builder)
        self.assertNotIn("g2h_loopback_bff",publish)
        self.assertIn("CMS_CSRF_DENIED",test)
        self.assertIn("CMS_ORIGIN_DENIED",test)
        self.assertIn("CMS_SESSION_INVALID",test)
        self.assertIn("CMS_RATE_LIMITED",test)
        self.assertNotIn("workflow_dispatch",test)
        self.assertEqual(publish.count("cron: '55 0 * * *'"),1)
        self.assertEqual(publish.count("cron: '55 6,12,18 * * *'"),1)

if __name__=="__main__":
    unittest.main()
