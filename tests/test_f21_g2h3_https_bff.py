"""G2-H.3 genuine TLS BFF transport tests with synthetic GoTrue upstream.

This exercises HTTPS, cookies, CSRF and revocation — not live GoTrue credentials
or a production BFF. Never publish the harness to Cloudflare or Supabase.
"""
from pathlib import Path
import os
import shutil
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]

class HttpsBffIsolation(unittest.TestCase):
    def test_openssl_node_tls_e2e(self):
        node=shutil.which("node")
        openssl=shutil.which("openssl")
        self.assertIsNotNone(node,"Node is required; fail closed")
        self.assertIsNotNone(openssl,"OpenSSL is required; fail closed")
        env=dict(os.environ)
        env["JIANSHI_G2H3_SYNTHETIC_ONLY"]="1"
        for v in ("SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY","DATABASE_URL","SUPABASE_DB_URL"):
            env.pop(v,None)
        result=subprocess.run([node,"--test","tests/g2h3_https_bff.test.mjs"],
                              cwd=ROOT,env=env,capture_output=True,text=True,timeout=55)
        self.assertEqual(result.returncode,0,(result.stdout+"\\n"+result.stderr)[-4900:])
        self.assertIn("# fail 0",result.stdout)
        self.assertIn("# pass 5",result.stdout)

    def test_source_isolation_and_no_schedule_change(self):
        source=(ROOT/"scripts/qa/g2h3_https_bff.mjs").read_text()
        build=(ROOT/"scripts/release/p412_build_public.py").read_text()
        workflow=(ROOT/".github/workflows/publish-static.yml").read_text()
        self.assertNotIn("g2h3_https_bff",build)
        self.assertNotIn("g2h3_https_bff",workflow)
        self.assertIn("HttpOnly; SameSite=Strict",source)
        self.assertIn("Strict; Path=/qa",source)
        self.assertIn("CMS_IDENTITY_REVOKED",source)
        self.assertIn("CMS_CSRF_DENIED",source)
        self.assertIn("CMS_REAL_CREDENTIALS_FORBIDDEN",source)
        self.assertNotIn("createServer(",source.replace("https.createServer(",""))
        self.assertNotIn("server.listen(",source)
        self.assertEqual(workflow.count("cron: '55 0 * * *'"),1)
        self.assertEqual(workflow.count("cron: '55 6,12,18 * * *'"),1)

if __name__=="__main__":
    unittest.main()
