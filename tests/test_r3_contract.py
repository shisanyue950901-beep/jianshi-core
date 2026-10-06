import unittest
from pathlib import Path

class TestR3Contract(unittest.TestCase):
    def test_schema_and_runtime_contract(self):
        m8=Path("db/migrations/0008_github_source.sql").read_text(encoding="utf-8")
        m9=Path("db/migrations/0009_github_momentum.sql").read_text(encoding="utf-8")
        fn=Path("supabase/functions/collect-github-trends/index.ts").read_text(encoding="utf-8")
        for token in [
            "github_repositories",
            "github_repository_snapshots",
            "github_discovery_queries",
            "signals",
        ]:
            self.assertIn(token,m8)
        self.assertIn("github_repository_momentum",m9)
        self.assertIn("refresh_github_momentum_signals",m9)
        self.assertIn("SOURCE_GATE_BLOCKED",fn)
        self.assertIn("X-GitHub-Api-Version",fn)
        self.assertIn("min_rate_remaining",fn)

if __name__=="__main__":
    unittest.main()
