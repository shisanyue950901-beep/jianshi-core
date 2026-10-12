"""G2-G: RESTORE is a service-side JWT-authorized operation only.

Positive SQL behavior is tested independently with real Postgres container.
Here we check the Edge/SQL access path, not a successful browser CMS E2E.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
EDGE=(ROOT/"supabase/functions/cms-staging-gateway/index.ts").read_text(encoding="utf-8")
RPC=(ROOT/"db/migrations/0058_jianshi_cms_restore_private_rpc.sql").read_text(encoding="utf-8")
G2F=(ROOT/"scripts/qa/g2f_postgres_real_e2e.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/cms-postgres-isolated.yml").read_text(encoding="utf-8")
PROD=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")

class G2GRestoreSafety(unittest.TestCase):
    def test_restoration_has_exact_client_payload_allowlist(self):
        for marker in (
            'const RESTORE_KEYS = new Set([', '"source_revision","request_id"',
            'limitedKeys(body, RESTORE_KEYS)',
            'Object.keys(body).length === 4',
            'isPositiveInt(body.source_revision)',
            'body.source_revision < body.expected_revision',
            'path.endsWith("/restore") ? "RESTORE"',
        ):
            self.assertIn(marker,EDGE)
        self.assertNotIn('p_actor:payload',EDGE)
        self.assertIn('p_actor:userId, p_payload:payload',EDGE)
        self.assertIn('admin.auth.getUser(jwt)',EDGE)
        self.assertIn('cms_internal_session_v01',EDGE)
        self.assertIn('CMS_SESSION_REVOKED',EDGE)

    def test_service_rpc_is_private_by_grant_and_underlying_gate(self):
        low=RPC.lower()
        for required in (
            'security invoker','set search_path=',
            'perform jianshi_cms.ensure_write_gate(p_actor',
            'jianshi_cms.restore_draft_revision(',
            'cms_invalid_restore_payload',
            'from public, anon, authenticated',
            'to service_role',
        ):
            self.assertIn(required,low)
        self.assertNotIn('security definer',low)
        self.assertNotIn('create policy',low)
        self.assertNotIn('to authenticated;',low)
        self.assertNotIn('alter table',low)
        self.assertNotIn('update public.product_feature_flags',low)
        self.assertNotIn('auth.users',low)
        self.assertNotIn('create table',low)
        self.assertIn("p_payload ?& v_allowed", RPC)
        self.assertIn("RETURN jsonb_build_object('revision',v_new)",RPC)

    def test_no_browser_or_remote_publishing_shortcuts(self):
        self.assertIn('if (req.headers.has("origin")) return response(403',EDGE)
        self.assertIn('url !== "https://" + STAGING_REF + ".supabase.co"',EDGE)
        self.assertIn('JIANSHI_G1E_API_GATE',EDGE)
        self.assertIn('CMS_STAGING_LOCKED',EDGE)
        self.assertNotIn('access-control-allow-origin',EDGE.lower())
        self.assertNotIn('verify_jwt: false',EDGE)
        self.assertNotIn('console.log(',EDGE)
        self.assertNotIn('cms-staging-gateway', (ROOT/"scripts/release/p412_build_public.py").read_text())
        self.assertNotIn('cms_internal_restore_v01',PROD)
        self.assertEqual(PROD.count("cron: '55 0 * * *'"),1)
        self.assertEqual(PROD.count("cron: '55 6,12,18 * * *'"),1)

    def test_real_postgresql_verifies_service_rpc_not_mock_only(self):
        self.assertIn('0058_jianshi_cms_restore_private_rpc.sql',WF)
        self.assertIn('0058_jianshi_cms_restore_private_rpc.sql',G2F)
        self.assertIn('def restore_gateway(',G2F)
        self.assertIn('public.cms_internal_restore_v01(',G2F)
        self.assertIn('CMS_INVALID_RESTORE_PAYLOAD',G2F)
        self.assertIn('CMS_DUPLICATE_REQUEST',G2F)
        self.assertIn('G2F_REAL_POSTGRES_E2E_PASS',G2F)

if __name__=="__main__":
    unittest.main()
