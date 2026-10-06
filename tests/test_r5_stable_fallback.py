import unittest
from pathlib import Path

class TestStableFallback(unittest.TestCase):
    def test_contract(self):
        p=Path("supabase/functions/jianshi-web/index.ts")
        self.assertTrue(p.exists())
        s=p.read_text(encoding="utf-8")
        self.assertIn("看见正在发生的",s)
        self.assertIn('awaitapi("home")',s.replace(" ",""))
        self.assertIn("public-feed",s)
        self.assertIn("cache-control",s)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",s)

if __name__=="__main__":
    unittest.main()
