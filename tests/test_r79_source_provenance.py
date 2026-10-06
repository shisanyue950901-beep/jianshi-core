import json, unittest
from pathlib import Path

class TestR79SourceProvenance(unittest.TestCase):
    def test_foundersprime_is_not_green(self):
        data=json.loads(Path("config/source_registry.json").read_text(encoding="utf-8"))
        by={x["code"]:x for x in data["sources"]}
        fp=by["foundersprime"]
        self.assertEqual(fp["status"],"YELLOW")
        self.assertFalse(fp["auto_collect"])
        self.assertFalse(fp["redisplay_allowed"])
        self.assertTrue(fp["written_permission_required"])
        self.assertTrue(fp["upstream_provenance_required"])

    def test_provenance_gate_contract(self):
        sql=Path("db/migrations/0028_source_provenance_gate.sql").read_text(encoding="utf-8")
        for token in [
            "source_provenance_rules",
            "source_provenance_audits",
            "assert_aggregated_item_publication_allowed_v01",
            "UNKNOWN_UPSTREAM_PROVENANCE",
            "UPSTREAM_PUBLICATION_BLOCKED",
            "EXPLICIT_ALLOW_REQUIRES_WRITTEN_EVIDENCE",
            "Acquire.com",
            "TrustMRR",
            "1150",
            '"Acquire.com":618',
            '"TrustMRR":532',
            "UPSTREAM_SUBLICENSE_CONFIRMATION",
        ]:
            self.assertIn(token,sql)

    def test_no_aggregator_auto_enable(self):
        sql=Path("db/migrations/0028_source_provenance_gate.sql").read_text(encoding="utf-8")
        self.assertIn("'YELLOW','OFFICIAL_PUBLIC_API_UPSTREAM_RESTRICTED',false,false",sql)
        self.assertNotIn("'foundersprime','FoundersPrime','https://www.foundersprime.com','GREEN'",sql)

if __name__=="__main__":
    unittest.main()
