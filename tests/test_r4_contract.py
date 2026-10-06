import unittest
from pathlib import Path

class TestR4Contract(unittest.TestCase):
    def test_r4_contract(self):
        m13=Path("db/migrations/0013_opportunity_foundation.sql").read_text(encoding="utf-8")
        m14=Path("db/migrations/0014_opportunity_engine_v01.sql").read_text(encoding="utf-8")
        m15=Path("db/migrations/0015_opportunity_refresh_fix.sql").read_text(encoding="utf-8")
        self.assertIn("opportunity_evidence",m13)
        self.assertIn("solo-saas",m13)
        self.assertIn("refresh_opportunity_evidence_v01",m14)
        self.assertIn("opportunity_scored_v01",m14)
        self.assertIn("public_ready",m14)
        self.assertIn("active_evidence_total",m15)

if __name__=="__main__":
    unittest.main()
