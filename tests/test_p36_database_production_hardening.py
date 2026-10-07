import json
import unittest
from pathlib import Path


class TestP36DatabaseProductionHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=Path("db/migrations/0046_database_production_hardening.sql").read_text(encoding="utf-8")
        cls.cfg=json.loads(Path("config/database_operations_v1.json").read_text(encoding="utf-8"))
        cls.workflow=Path(".github/workflows/database-backup.yml").read_text(encoding="utf-8")
        cls.backup=Path("ops/db/backup_postgres.sh").read_text(encoding="utf-8")
        cls.restore=Path("ops/db/restore_postgres.sh").read_text(encoding="utf-8")

    def test_four_fk_indexes_are_present(self):
        for token in [
            "idx_opportunity_github_query_map_query_id",
            "idx_saved_opportunities_opportunity_id",
            "idx_source_provenance_audits_aggregator_source_id",
            "idx_source_provenance_rules_upstream_source_id",
        ]:
            self.assertIn(token,self.sql)

    def test_auth_rls_uses_initplan_pattern(self):
        self.assertIn("(select auth.uid())",self.sql)
        self.assertNotIn("using (user_id=auth.uid())",self.sql)
        self.assertNotIn("with check (user_id=auth.uid())",self.sql)
        self.assertIn("user_profiles_select_own",self.sql)
        self.assertIn("user_alert_events_update_own",self.sql)

    def test_capacity_monitor_is_service_role_only(self):
        self.assertIn("database_capacity_health_v01",self.sql)
        self.assertIn("from public,anon,authenticated",self.sql)
        self.assertIn("to service_role",self.sql)
        self.assertEqual(self.cfg["database_warning_pct"],70)
        self.assertEqual(self.cfg["database_critical_pct"],90)

    def test_backup_is_encrypted_and_gated(self):
        self.assertIn("aes-256-cbc",self.backup)
        self.assertIn("pbkdf2",self.backup)
        self.assertIn("JIANSHI_DB_BACKUP_ENABLED",self.workflow)
        self.assertIn("JIANSHI_DATABASE_URL",self.workflow)
        self.assertIn("JIANSHI_BACKUP_PASSPHRASE",self.workflow)
        self.assertEqual(self.cfg["backup_status"],"READY_NOT_ARMED")
        self.assertTrue(self.cfg["backup_encryption_required"])

    def test_restore_is_fail_closed(self):
        self.assertIn('ALLOW_RESTORE',self.restore)
        self.assertIn('TARGET_DATABASE_URL',self.restore)
        self.assertIn('exit 2',self.restore)

    def test_no_business_scoring_or_launch_gate_changes(self):
        lower=self.sql.lower()
        self.assertNotIn("opportunity_scored_v01",lower)
        self.assertNotIn("opportunity_rank_current",lower)
        self.assertNotIn("product_feature_flags",lower)
        self.assertNotIn("newsletter_launch_control",lower)


if __name__=="__main__":
    unittest.main()
