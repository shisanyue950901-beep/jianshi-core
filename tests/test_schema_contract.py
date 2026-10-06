import re, unittest
from pathlib import Path

class TestSchema(unittest.TestCase):
    def test_contract(self):
        sql = "\n".join(p.read_text(encoding="utf-8") for p in sorted(Path("db/migrations").glob("*.sql")))
        for table in ["data_sources","source_policies","raw_items","marketplace_listings","marketplace_listing_snapshots","pipeline_runs","audit_events"]:
            self.assertRegex(sql.lower(), rf"create table if not exists {table}")
        self.assertIn("AUTO_COLLECT_FORBIDDEN_FOR_NON_GREEN_SOURCE", sql)
        self.assertIn("APPEND-ONLY", sql)

if __name__ == "__main__": unittest.main()
