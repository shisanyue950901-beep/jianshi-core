import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestP45CAutomaticMappingTrigger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql=(ROOT/"db/migrations/0057_child_evidence_mapping_trigger_audit.sql").read_text(encoding="utf-8")
        cls.collector=(ROOT/"supabase/functions/collect-empire-flippers/index.ts").read_text(encoding="utf-8")
        cls.doc=(ROOT/"docs/P45C_AUTOMATIC_MAPPING_TRIGGER_STAGING.md").read_text(encoding="utf-8")

    def test_audit_table_and_hook_exist(self):
        self.assertIn("child_evidence_mapping_runs",self.sql)
        self.assertIn("run_child_evidence_mapping_hook_v01",self.sql)
        self.assertIn("child_evidence_mapping_run_audit_v01",self.sql)

    def test_hook_only_accepts_successful_empire_runs(self):
        lower=self.sql.lower()
        self.assertIn("empire_flippers_collector",lower)
        self.assertIn("empire_flippers",lower)
        self.assertIn("v_run.status <> 'success'",lower)
        self.assertIn("trigger_not_eligible",lower)

    def test_mapping_failure_is_returned_not_raised(self):
        self.assertIn("exception when others",self.sql.lower())
        self.assertIn("'status','FAILED'",self.sql)
        self.assertIn("Fail isolated: return FAILED as data instead of raising",self.sql)
        self.assertIn("MAPPING_FAILURE != COLLECTOR_FAILURE",self.doc)

    def test_collector_triggers_only_after_gate_pass(self):
        self.assertIn('if (gatePass) {',self.collector)
        self.assertIn('"run_child_evidence_mapping_hook_v01"',self.collector)
        self.assertIn("child_evidence_mapping_hook",self.collector)
        self.assertIn('status: "RPC_ERROR"',self.collector)
        self.assertIn('status: "CLIENT_EXCEPTION"',self.collector)

    def test_collector_http_status_still_depends_on_gate_pass(self):
        self.assertIn("status: gatePass ? 200 : 503",self.collector)

    def test_no_cron_or_publication_change(self):
        lower=self.sql.lower()
        self.assertNotIn("cron.schedule",lower)
        self.assertNotIn("update opportunities set",lower)
        self.assertNotIn("public_opportunity_catalog_v01",lower)

    def test_service_role_only(self):
        self.assertIn("from public,anon,authenticated",self.sql)
        self.assertIn("to service_role",self.sql)

if __name__=="__main__":
    unittest.main()
