"""G2-H.4 private durable BFF session audit — crypto unit tests and SQL safety.

True PostgreSQL transaction, concurrency, RLS and Auth gate enforcement are
executed separately by cms-postgres-isolated.yml (not faked in this test).
"""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SQL=(ROOT/"db/migrations/0060_jianshi_cms_durable_bff_sessions.sql").read_text()
VAULT=(ROOT/"scripts/qa/g2h4_session_vault.mjs").read_text()
PG=(ROOT/"scripts/qa/g2f_postgres_real_e2e.py").read_text()
LIVE=(ROOT/".github/workflows/publish-static.yml").read_text()

class DurableSessionAudit(unittest.TestCase):
    def test_crypto_executes_node(self):
        node=shutil.which("node")
        self.assertIsNotNone(node,"Crypto testing must run: fail closed if Node is missing")
        result=subprocess.run([node,"--test","tests/g2h4_session_vault.test.mjs"],
                              cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,(result.stdout+"\n"+result.stderr)[-3000:])
        self.assertIn("# pass 6",result.stdout)
        self.assertIn("# fail 0",result.stdout)

    def test_private_sql_grants_and_atomic_db_limits(self):
        for x in ("FORCE ROW LEVEL SECURITY","ENABLE ROW LEVEL SECURITY",
                  "FOR UPDATE","service_role","encrypted_jwt","csrf_digest",
                  "cookie_digest","CMS_RATE_LIMITED","CMS_SESSION_REVOKED",
                  "CMS_CSRF_DENIED","session_is_active","ensure_write_gate",
                  "expires_at","revoked_at","write_count","15 minutes",
                  "CREATE OR REPLACE FUNCTION jianshi_cms.bff_revoke_session"):
            self.assertIn(x,SQL)
        for x in ("FROM PUBLIC, anon, authenticated",
                  "FROM PUBLIC,anon,authenticated","TO service_role",
                  "TO service_role;"):
            self.assertIn(x,SQL)
        lower=SQL.lower()
        self.assertNotIn("security definer",lower)
        self.assertNotIn("update public.product_feature_flags",lower)
        self.assertNotIn("drop table",lower)
        self.assertNotIn("create policy",lower)
        self.assertNotIn("grant select on jianshi_cms.bff_sessions to authenticated",lower)
        self.assertIn("RETURN jsonb_build_object('allowed',false",SQL)

    def test_encryption_and_rotation_are_server_only(self):
        for x in ("aes-256-gcm","createHmac","sha256","setAAD",
                  "CMS_VAULT_KEY_UNAVAILABLE","CMS_VAULT_AUTHENTICATION_FAILED",
                  "activeKeyId","key_id"):
            self.assertIn(x,VAULT)
        self.assertNotIn("console.log",VAULT)
        self.assertNotIn("localStorage",VAULT)
        self.assertNotIn("createServer",VAULT)
        self.assertNotIn("https://",VAULT)
        self.assertIn("0060_jianshi_cms_durable_bff_sessions.sql",PG)
        self.assertIn("G2H4_SQL_DURABLE_SESSION_PASS",PG)

    def test_no_public_files_or_source_collection_changes(self):
        self.assertNotIn("g2h4_session_vault",(ROOT/"scripts/release/p412_build_public.py").read_text())
        self.assertNotIn("g2h4_session_vault",LIVE)
        self.assertNotIn("0060_jianshi_cms_durable_bff_sessions.sql",LIVE)
        self.assertEqual(LIVE.count("cron: '55 0 * * *'"),1)
        self.assertEqual(LIVE.count("cron: '55 6,12,18 * * *'"),1)
        self.assertFalse((ROOT/"web/dist/qa/cms/index.html").exists())

if __name__=="__main__":
    unittest.main()
