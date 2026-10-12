"""G2-H.5: integration wiring must be executable in disposable PostgreSQL CI.

Do not run real-user login, create production credentials or copy private
research Artifact data. Node TLS/PG E2E runs only in isolated workflow.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
BFF=(ROOT/"scripts/qa/g2h5_durable_https_bff.mjs").read_text()
TEST=(ROOT/"tests/g2h5_durable_https_pg.test.mjs").read_text()
WORK=(ROOT/".github/workflows/cms-postgres-isolated.yml").read_text()
PUBLISH=(ROOT/".github/workflows/publish-static.yml").read_text()

class TestG2H5IntegratedTransport(unittest.TestCase):
 def test_real_pg_https_route_connected(self):
  for x in ("https.createServer(","vault.openEnvelope(", "vault.cookieDigest(",
            "vault.csrfDigest(", "identity.verify(jwt)", "store.consume(",
            "store.issue(", "store.revoke(", "dispatch({kind:'WRITE'",
            "CMS_IDENTITY_BINDING_FAILED","CMS_CSRF_DENIED",
            "CMS_RATE_LIMITED","CMS_EXTERNAL_CREDENTIALS_FORBIDDEN"):
   self.assertIn(x,BFF)
  for x in ("createSessionVault","createStagingAuthAdapter",
            "createDurableHttpsHarness","cms_internal_restore_v01",
            "jianshi_cms.bff_consume_session","jianshi_cms.bff_issue_session",
            "jianshi_cms.bff_revoke_session","CMS_SESSION_REVOKED",
            "G2H5_HTTPS_DURABLE_SQL_CHAIN_PASS"):
   self.assertIn(x,TEST)
  self.assertIn("node --test tests/g2h5_durable_https_pg.test.mjs",WORK)
  self.assertIn("JIANSHI_G2F_EPHEMERAL_ONLY:",WORK)
  self.assertIn("node-version: '22'",WORK)

 def test_public_site_does_not_ship_internal_bff(self):
  self.assertNotIn("g2h5_durable_https_bff",(ROOT/"scripts/release/p412_build_public.py").read_text())
  self.assertNotIn("g2h5_durable_https_bff",PUBLISH)
  self.assertNotIn("g2h5_durable_https_pg",PUBLISH)
  self.assertNotIn("schedule:",WORK)
  self.assertEqual(PUBLISH.count("cron: '55 0 * * *'"),1)
  self.assertEqual(PUBLISH.count("cron: '55 6,12,18 * * *'"),1)
  self.assertNotIn("listen(",BFF)
  self.assertNotIn("console.log",BFF)
  self.assertNotIn("createStagingAuthAdapter(",BFF)

 def test_no_real_secret_or_user_auth_entrypoint(self):
  self.assertNotIn("https://apuibjhxinumxbfnqlkp",BFF)
  self.assertNotIn("https://dalfvgehosxfyxkptxwx",BFF)
  self.assertNotIn("sb_secret_",BFF)
  self.assertNotIn("service_role_key",BFF)
  self.assertIn("issueSyntheticVerifiedSession",BFF)
  self.assertNotIn("url.pathname==='/login'",BFF)
  self.assertNotIn("res.end(jwt)",BFF)

if __name__=="__main__":unittest.main()
