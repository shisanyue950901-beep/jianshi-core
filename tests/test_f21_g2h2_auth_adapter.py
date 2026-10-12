"""G2-H.2: Node upstream adapter negative-auth suite + SQL grant checks.

A synthetic GoTrue fetch adapter is used; NOT a real JWT positive E2E.
"""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
ADAPTER=(ROOT/"scripts/qa/g2h2_trusted_auth_adapter.mjs").read_text()
SQL=(ROOT/"db/migrations/0059_jianshi_cms_trusted_role_read.sql").read_text()
WORKFLOW=(ROOT/".github/workflows/cms-bff-isolated.yml").read_text()
SNAPSHOT=(ROOT/".github/workflows/publish-static.yml").read_text()

class StagingTrustedAdapterContract(unittest.TestCase):
    def test_real_node_behavior(self):
        node=shutil.which("node")
        self.assertIsNotNone(node,"Node required for identity boundary tests")
        r=subprocess.run([node,"--test","tests/g2h2_trusted_auth_adapter.test.mjs"],
                         cwd=ROOT,text=True,capture_output=True,timeout=45)
        self.assertEqual(r.returncode,0,(r.stdout+"\n"+r.stderr)[-3500:])
        self.assertIn("# fail 0",r.stdout)
        self.assertIn("# pass 6",r.stdout)

    def test_additive_role_rpc_never_available_to_browser(self):
        for v in ["security invoker","jianshi_cms.ensure_write_gate",
                  "from PUBLIC, anon, authenticated","to service_role"]:
            self.assertIn(v.lower(),SQL.lower())
        self.assertNotIn("security definer",SQL.lower())
        self.assertNotIn("update public.product_feature_flags",SQL.lower())
        self.assertNotIn("grant execute",SQL.lower().split("from public, anon, authenticated")[0])
        self.assertIn("cms_internal_actor_role_v01",ADAPTER)
        self.assertIn("cms_internal_session_v01",ADAPTER)

    def test_not_publicly_deployed_or_scheduled(self):
        self.assertNotIn("g2h2_trusted_auth_adapter",SNAPSHOT)
        self.assertNotIn("g2h2_trusted_auth_adapter",(ROOT/"scripts/release/p412_build_public.py").read_text())
        self.assertEqual(SNAPSHOT.count("cron: '55 0 * * *'"),1)
        self.assertEqual(SNAPSHOT.count("cron: '55 6,12,18 * * *'"),1)
        self.assertNotIn("schedule:",WORKFLOW)
        self.assertIn("tests/g2h2_trusted_auth_adapter.test.mjs",WORKFLOW)

if __name__=="__main__":
    unittest.main()
