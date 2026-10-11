"""F2.1 G1-E: staging-only private verified CMS HTTP gateway contracts.

The regression suite never uses network, real identities, or private content.
Positive login/business E2E remains gated and must NOT be simulated as PASS.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "db/migrations/0056_jianshi_cms_session_guard.sql").read_text(encoding="utf-8")
EDGE = (ROOT / "supabase/functions/cms-staging-gateway/index.ts").read_text(encoding="utf-8")
PUBLISH = (ROOT / "scripts/release/p412_build_public.py").read_text(encoding="utf-8")


class G1EVerifiedGateway(unittest.TestCase):
    def test_session_db_checker_returns_boolean_only_and_is_service_only(self):
        self.assertIn("create or replace function jianshi_cms.session_is_active(", SQL)
        self.assertIn("security definer", SQL.lower())
        self.assertIn("set search_path = ''", SQL)
        self.assertIn("from auth.sessions s", SQL)
        self.assertIn("join auth.users u", SQL)
        self.assertIn("s.id = p_session_id", SQL)
        self.assertIn("s.user_id = p_user_id", SQL)
        self.assertIn("u.deleted_at is null", SQL)
        self.assertIn("s.not_after is null or s.not_after > now()", SQL)
        self.assertIn("revoke all on function jianshi_cms.session_is_active(uuid,uuid)", SQL)
        self.assertIn("from PUBLIC, anon, authenticated;", SQL)
        self.assertIn("to service_role;", SQL)
        self.assertNotIn("returns jsonb", SQL.lower())
        self.assertNotIn("grant select on auth.sessions", SQL.lower())

    def test_public_wrappers_only_available_to_server_key(self):
        self.assertIn("create or replace function public.cms_internal_session_v01(", SQL)
        self.assertIn("create or replace function public.cms_internal_write_v01(", SQL)
        self.assertEqual(SQL.count("security invoker"), 2)
        self.assertIn("perform jianshi_cms.ensure_write_gate", SQL)
        for op in ("CREATE", "EDIT", "STATE"):
            self.assertIn("p_operation='" + op + "'", SQL)
        self.assertIn("revoke all on function public.cms_internal_session_v01(uuid,uuid)", SQL)
        self.assertIn("revoke all on function public.cms_internal_write_v01(uuid,text,jsonb)", SQL)
        self.assertIn("from PUBLIC,anon,authenticated;", SQL)
        self.assertNotIn("grant execute on function public.cms_internal", SQL.split("to authenticated;")[0].lower())
        self.assertIn("to service_role;", SQL)
        self.assertNotIn("create policy", SQL.lower())

    def test_runtime_deploy_is_staging_only_with_platform_jwt(self):
        self.assertIn('const STAGING_REF = "apuibjhxinumxbfnqlkp"', EDGE)
        self.assertIn('url !== "https://" + STAGING_REF + ".supabase.co"', EDGE)
        self.assertIn('JIANSHI_G1E_API_GATE', EDGE)
        self.assertIn('"AUTH_E2E_APPROVED"', EDGE)
        self.assertIn('response(503, "CMS_STAGING_LOCKED")', EDGE)
        self.assertIn('response(503, "CMS_WRITE_DISABLED")', EDGE)
        self.assertIn('response(503, "CMS_AUTH_NOT_READY")', EDGE)
        self.assertIn('if (req.headers.has("origin")) return response(403', EDGE)
        self.assertIn('if (req.method !== "POST") return response(405', EDGE)
        self.assertNotIn('"access-control-allow-origin"', EDGE.lower())
        self.assertNotIn('Deno.env.set(', EDGE)
        self.assertNotIn('console.log(', EDGE)
        self.assertNotIn('console.error(', EDGE)
        self.assertNotIn('verify_jwt: false', EDGE)

    def test_verified_jwt_and_revoked_session_needed_for_every_operation(self):
        self.assertIn("admin.auth.getUser(jwt)", EDGE)
        self.assertIn("claims.sub !== userId", EDGE)
        self.assertIn('claims.role !== "authenticated"', EDGE)
        self.assertIn("claims.is_anonymous === true", EDGE)
        self.assertIn("isUuid(claims.session_id)", EDGE)
        self.assertIn("claims.exp * 1000 <= Date.now()", EDGE)
        self.assertIn('"cms_internal_session_v01"', EDGE)
        self.assertIn("p_user_id:userId, p_session_id:sessionId", EDGE)
        self.assertIn("if (sessionError || active !== true)", EDGE)
        self.assertIn('"cms_internal_write_v01"', EDGE)
        self.assertIn("p_actor:userId, p_operation:operation", EDGE)
        self.assertIn('response(401, "CMS_SESSION_REVOKED")', EDGE)
        self.assertNotIn("user_metadata", EDGE)
        self.assertNotIn("req.headers.get(\"x-user-id\")", EDGE)

    def test_input_limits_and_no_sensitive_data_response(self):
        self.assertIn("const MAX_BODY = 12000", EDGE)
        self.assertIn("MAX_BODY", EDGE)
        self.assertIn("limitedKeys(body, DRAFT_KEYS)", EDGE)
        self.assertIn("limitedKeys(body, EDIT_KEYS)", EDGE)
        self.assertIn("limitedKeys(body, STATE_KEYS)", EDGE)
        self.assertIn("CMS_JSON_REQUIRED", EDGE)
        self.assertIn("CMS_INVALID_PAYLOAD", EDGE)
        self.assertIn("CMS_VERSION_OR_DUPLICATE", EDGE)
        self.assertIn("CMS_ACTION_FORBIDDEN", EDGE)
        self.assertIn("CMS_FAIL_CLOSED", EDGE)
        self.assertIn('cache-control": "no-store', EDGE)
        self.assertNotIn("console.", EDGE)
        self.assertNotIn("serviceKey,", EDGE.split("return new Response(JSON.stringify({status:")[1])

    def test_research_and_public_static_isolation(self):
        self.assertNotIn("cms-staging-gateway", PUBLISH)
        self.assertNotIn("cms_internal_write_v01", PUBLISH)
        self.assertNotIn("session_is_active", PUBLISH)
        self.assertFalse((ROOT / "web/dist/cms-staging-gateway").exists())
        wf = (ROOT / ".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"), 1)
        gate = (ROOT / "db/migrations/0037_auth_launch_gate.sql").read_text(encoding="utf-8")
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY", gate)


if __name__ == "__main__":
    unittest.main()
