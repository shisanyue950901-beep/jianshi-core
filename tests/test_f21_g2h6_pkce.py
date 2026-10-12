"""G2-H.6 browser login contract: real TLS test + original SQL single-use race.

This does NOT certify real Supabase GoTrue email login; provider is synthetic.
"""
from pathlib import Path
import shutil
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/"scripts/qa/g2h6_pkce_login_contract.mjs").read_text()
SQL=(ROOT/"db/migrations/0061_jianshi_cms_pkce_one_time_state.sql").read_text()
PG=(ROOT/"scripts/qa/g2f_postgres_real_e2e.py").read_text()
LIVE=(ROOT/".github/workflows/publish-static.yml").read_text()
WF=(ROOT/".github/workflows/cms-postgres-isolated.yml").read_text()

class PKCEContract(unittest.TestCase):
 def test_actual_tls_and_one_time_test(self):
  node=shutil.which("node")
  self.assertIsNotNone(node,"Node required, fail closed")
  self.assertIsNotNone(shutil.which("openssl"),"TLS test requires OpenSSL")
  result=subprocess.run([node,"--test","tests/g2h6_pkce_login.test.mjs"],
                        cwd=ROOT,capture_output=True,text=True,timeout=45)
  self.assertEqual(result.returncode,0,(result.stdout+"\n"+result.stderr)[-4300:])
  self.assertIn("# fail 0",result.stdout)
  self.assertIn("# pass 6",result.stdout)
 def test_sql_rls_and_immutable_one_time_state(self):
  for x in ("FORCE ROW LEVEL SECURITY","ENABLE ROW LEVEL SECURITY",
            "UPDATE jianshi_cms.bff_pkce_challenges",
            "AND consumed_at IS NULL AND expires_at>now()",
            "RETURNING encrypted_verifier",
            "bff_pkce_gate_v01","auth_launch_ready_v01","CMS_WRITE_DISABLED",
            "FROM PUBLIC,anon,authenticated","TO service_role"):
   self.assertIn(x,SQL)
  self.assertNotIn("SECURITY DEFINER",SQL)
  self.assertNotIn("GRANT SELECT ON jianshi_cms.bff_pkce_challenges TO authenticated",SQL)
  self.assertIn("0061_jianshi_cms_pkce_one_time_state.sql",PG)
  self.assertIn("G2H6_SQL_PKCE_SINGLE_USE_PASS",PG)
  self.assertIn("db/migrations/0061_jianshi_cms_pkce_one_time_state.sql",WF)
 def test_no_public_login_route_or_secrets(self):
  for x in ("CMS_PKCE_LIVE_DISABLED","CMS_PKCE_FIXED_TEST_ORIGIN",
            "aes-256-gcm","hkdfSync","SameSite=","__Host-jianshi_cms",
            "pendingStore.consume","provider.exchangeCodeForSession",
            "issueDurableSession","CMS_PKCE_EXPIRED_OR_REPLAYED"):
   self.assertIn(x,JS)
  self.assertNotIn("console.log",JS)
  self.assertNotIn("createServer(",JS)
  self.assertNotIn("server.listen(",JS)
  self.assertNotIn("sb_secret_",JS)
  self.assertNotIn("g2h6_pkce_login_contract",LIVE)
  self.assertNotIn("g2h6_pkce_login_contract",
                   (ROOT/"scripts/release/p412_build_public.py").read_text())
  self.assertEqual(LIVE.count("cron: '55 0 * * *'"),1)
  self.assertEqual(LIVE.count("cron: '55 6,12,18 * * *'"),1)
  self.assertNotIn("schedule:",WF)

if __name__=="__main__":unittest.main()
