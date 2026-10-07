import unittest
from pathlib import Path

class TestR87EvidenceClassGate(unittest.TestCase):
    def test_evidence_class_schema(self):
        sql=Path("db/migrations/0038_evidence_class_validation_gate.sql").read_text(encoding="utf-8")
        for token in [
            "evidence_class_rules",
            "TECHNICAL_SUPPLY",
            "COMMERCIAL_PROOF",
            "opportunity_evidence_class_counts_v01",
            "technical_evidence_count",
            "commercial_evidence_count",
            "TECH_PLUS_COMMERCIAL",
        ]:
            self.assertIn(token,sql)
        self.assertIn("m.evidence_count>=5",sql)

    def test_public_ready_is_not_raw_source_count(self):
        sql=Path("db/migrations/0038_evidence_class_validation_gate.sql").read_text(encoding="utf-8")
        public_ready_block=sql[sql.index("create or replace view opportunity_rank_current"):]
        self.assertIn("technical_evidence_count",public_ready_block)
        self.assertIn("commercial_evidence_count",public_ready_block)
        self.assertNotIn("source_count>=2 and m.evidence_count>=5",public_ready_block)

    def test_user_copy_explains_two_required_classes(self):
        build=Path("web/build.py").read_text(encoding="utf-8")
        self.assertIn("技术供给证据与真实商业证据",build)
        self.assertNotIn("至少两类独立数据源同时支持",build)

if __name__=="__main__":
    unittest.main()
