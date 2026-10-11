"""P4.48: private V2 backend schema has no accidental public Data API surface."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "db/migrations/0053_jianshi2_private_matching_foundation.sql").read_text(encoding="utf-8")

TABLES = (
    "organizations", "creator_profiles", "portfolio_items",
    "service_requests", "request_applications", "moderation_events",
)


class V2PrivateFoundationContract(unittest.TestCase):
    def test_all_six_tables_are_private_and_force_rls(self):
        self.assertEqual(SQL.count("create table if not exists jianshi_v2."), 6)
        for name in TABLES:
            self.assertIn("create table if not exists jianshi_v2." + name, SQL)
            self.assertIn("alter table jianshi_v2." + name + " enable row level security;", SQL)
            self.assertIn("alter table jianshi_v2." + name + " force row level security;", SQL)
        self.assertIn("revoke all on schema jianshi_v2 from public, anon, authenticated;", SQL)
        self.assertIn("revoke all on all tables in schema jianshi_v2 from public, anon, authenticated;", SQL)
        self.assertIn("revoke all on all sequences in schema jianshi_v2 from public, anon, authenticated;", SQL)
        self.assertNotIn("grant usage on schema jianshi_v2 to authenticated", SQL.lower())
        self.assertNotIn("grant select on jianshi_v2.", SQL.lower())
        self.assertNotIn("create policy", SQL.lower())

    def test_review_and_publication_are_strictly_separate(self):
        self.assertIn("constraint service_request_publication_guard", SQL)
        self.assertIn("review_status = 'APPROVED'", SQL)
        self.assertIn("rights_confirmed = true", SQL)
        self.assertIn("approved_public_summary is not null", SQL)
        self.assertIn("pitch_private", SQL)
        self.assertIn("verification_note_private", SQL)
        self.assertIn("private_reason", SQL)
        self.assertIn("unique(request_id,creator_user_id)", SQL)

    def test_feature_flags_remain_disabled(self):
        self.assertIn("'v2_matchmaking',false", SQL)
        self.assertIn("on conflict(feature_key) do update set enabled=false", SQL)
        flag_gate = (ROOT / "db/migrations/0037_auth_launch_gate.sql").read_text()
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY", flag_gate)
        self.assertNotIn("service_role", (ROOT / "scripts/release/p448_v2_local_drafts.py").read_text())

    def test_no_production_account_or_source_collector_edits_are_required(self):
        release = (ROOT / "scripts/release/p412_build_public.py").read_text()
        self.assertIn("publish_v2_drafts(OUTPUT)", release)
        wf = (ROOT / ".github/workflows/publish-static.yml").read_text()
        self.assertEqual(wf.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"), 1)


if __name__ == "__main__":
    unittest.main()
