"""F2.1 G1-D service-only private CMS transaction safety contract tests.

No live DB credentials, no writes, and no real user identities in these tests.
"""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SQL=(ROOT/"db/migrations/0055_jianshi_cms_transaction_gate.sql").read_text(encoding="utf-8")
PUBLISHED=(ROOT/"db/migrations/0054_jianshi_cms_private_foundation.sql").read_text(encoding="utf-8")


class G1DCMSTransaction(unittest.TestCase):
    def test_private_role_table_uses_force_rls_and_browser_denied(self):
        self.assertIn("create table if not exists jianshi_cms.editor_grants",SQL)
        self.assertIn("alter table jianshi_cms.editor_grants enable row level security;",SQL)
        self.assertIn("alter table jianshi_cms.editor_grants force row level security;",SQL)
        self.assertIn("revoke all on jianshi_cms.editor_grants from PUBLIC, anon, authenticated;",SQL)
        self.assertIn("active boolean not null default false",SQL)
        self.assertNotIn("create policy",SQL.lower())
        self.assertNotIn("security definer",SQL.lower())
        self.assertNotIn("grant execute on function jianshi_cms.",SQL.split("to authenticated")[0].lower())
        self.assertNotIn("create table if not exists public.",SQL.lower())
        self.assertNotIn("ALTER ROLE",SQL.upper())

    def test_service_only_write_gates_and_existing_auth_e2e(self):
        for word in ("cms_editor","account_auth","public.auth_launch_ready_v01()",
                     "current_user <> 'service_role'", "'CMS_WRITE_DISABLED'",
                     "permission","active=true","CMS_PERMISSION_DENIED"):
            self.assertIn(word,SQL)
        for name in ("ensure_write_gate","create_draft","edit_draft","change_review_state"):
            self.assertIn("create or replace function jianshi_cms."+name+"(",SQL)
        self.assertEqual(SQL.count("language plpgsql security invoker"),4)
        self.assertEqual(SQL.count("grant execute on function jianshi_cms."),4)
        self.assertEqual(SQL.count("revoke all on function jianshi_cms."),4)

    def test_review_is_atomic_and_rejects_unsafe_actions(self):
        for key in ("for update", "CMS_STALE_REVISION","CMS_INDEPENDENT_REVIEW_REQUIRED",
                    "CMS_OWNER_DENIED","CMS_PUBLISHER_DENIED","CMS_ILLEGAL_TRANSITION",
                    "CMS_REVISION_MISSING","CMS_EVIDENCE_OR_RIGHTS_MISSING",
                    "CMS_MEDIA_RIGHTS_NOT_READY","source_evidence_private",
                    "facts_checked","rights_declared","CMS_SOURCE_UNSAFE",
                    "CMS_INVALID_PUBLIC_PROJECTION","jsonb_build_object(",
                    "public_allowlist_json","source_refs","CMS_DRAFT_LOCKED",
                    "unique(item_id, request_id)"):
            if key == "unique(item_id, request_id)":
                self.assertIn(key,PUBLISHED)
            else:
                self.assertIn(key,SQL)
        self.assertIn("p_actor=v_item.owner_user_id",SQL)
        self.assertIn("v_rev.source_evidence_private='[]'::jsonb",SQL)
        self.assertIn("p_to_state='PUBLISHED'",SQL)
        self.assertIn("p_to_state='UNPUBLISHED'",SQL)
        self.assertIn("lifecycle='RETRACTED'",SQL)
        self.assertIn("v_safe_sources",SQL)
        self.assertIn("(v_src - 'kind' - 'url')<>'{}'::jsonb",SQL)
        self.assertIn("(v_src - 'kind' - 'description')<>'{}'::jsonb",SQL)
        self.assertIn("'title',v_rev.content_private->>'title'",SQL)
        self.assertNotIn("'private_notes',",SQL)

    def test_durable_history_is_append_only(self):
        self.assertIn("grant select, insert on jianshi_cms.content_revisions to service_role;",PUBLISHED)
        self.assertIn("grant select, insert on jianshi_cms.review_events to service_role;",PUBLISHED)
        self.assertNotIn("update jianshi_cms.content_revisions",SQL.lower())
        self.assertNotIn("update jianshi_cms.review_events",SQL.lower())
        self.assertEqual(SQL.count("insert into jianshi_cms.review_events"),3)
        self.assertIn("current_revision=v_new",SQL)
        self.assertEqual(SQL.count("set search_path=''"),3)
        self.assertEqual(SQL.count("set search_path = ''"),1)

    def test_no_public_release_or_private_data_export(self):
        assert (ROOT/"web/dist").exists()
        release=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertNotIn("0055_jianshi_cms_transaction_gate",release)
        self.assertNotIn("jianshi_cms.",release)
        self.assertNotIn("CMS_WRITE_DISABLED",release)
        for p in ("web/dist/f21d","web/dist/api/cms","web/dist/internal/cms"):
            self.assertFalse((ROOT/p).exists())
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"),1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"),1)
        gate=(ROOT/"db/migrations/0037_auth_launch_gate.sql").read_text(encoding="utf-8")
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY",gate)


if __name__=="__main__":
    unittest.main()
