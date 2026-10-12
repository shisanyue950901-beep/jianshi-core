"""F2.1 staging A/B private schema contract without private data access."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
AUDIT=(ROOT/"scripts/security/f21_staging_ab_permission_audit.sql").read_text(encoding="utf-8").lower()
SCHEMAS=[
 (ROOT/"db/migrations/0053_jianshi2_private_matching_foundation.sql").read_text(encoding="utf-8").lower(),
 (ROOT/"db/migrations/0054_jianshi_cms_private_foundation.sql").read_text(encoding="utf-8").lower(),
 (ROOT/"db/migrations/0055_jianshi_cms_transaction_gate.sql").read_text(encoding="utf-8").lower(),
 (ROOT/"db/migrations/0056_jianshi_cms_session_guard.sql").read_text(encoding="utf-8").lower(),
]

class PrivateSchemaFailClosed(unittest.TestCase):
    def test_audit_queries_catalogs_only(self):
        self.assertIn("pg_class",AUDIT)
        self.assertIn("pg_policies",AUDIT)
        self.assertIn("has_schema_privilege",AUDIT)
        self.assertIn("has_table_privilege",AUDIT)
        self.assertIn("has_function_privilege",AUDIT)
        self.assertIn("pass_deny_by_default",AUDIT)
        for marker in ["select *", "auth.users", "auth.sessions", "insert into", "update ", "delete from", "drop ", "alter table", "service_role_key", "curl "]:
            self.assertNotIn(marker,AUDIT)

    def test_six_matching_tables_are_force_rls(self):
        v2,cms=SCHEMAS[:2]
        for table in ["organizations","creator_profiles","portfolio_items","service_requests","request_applications","moderation_events"]:
            self.assertIn("create table if not exists jianshi_v2."+table,v2)
            self.assertIn("alter table jianshi_v2."+table+" force row level security",v2)
        for table in ["content_items","content_revisions","media_rights","review_events","publication_snapshots"]:
            self.assertIn("create table if not exists jianshi_cms."+table,cms)
            self.assertIn("alter table jianshi_cms."+table+" force row level security",cms)
        self.assertIn("alter table jianshi_cms.editor_grants force row level security",SCHEMAS[2])

    def test_no_browser_rpc_grants(self):
        guard=SCHEMAS[3]
        for rpc in ["cms_internal_session_v01(uuid,uuid)","cms_internal_write_v01(uuid,text,jsonb)"]:
            self.assertIn("revoke all on function public."+rpc,guard)
            self.assertIn("grant execute on function public."+rpc,guard)
        self.assertIn("has_function_privilege('anon',p.oid,'execute')", AUDIT)
        self.assertIn("has_function_privilege('authenticated',p.oid,'execute')", AUDIT)
        self.assertIn("internal_rpc_closed", AUDIT)

if __name__=="__main__":
    unittest.main()
