"""Staging-only Auth redirect safety contracts; no live session E2E implied."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "supabase/functions/jianshi-staging-auth-callback/index.ts"
PREVIEW = "https://staging-auth-callback.jianshi-bua.pages.dev/_qa/staging-auth/"

class StagingAuthCallbackContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = SOURCE.read_text(encoding="utf-8")

    def test_only_staging_project(self):
        self.assertIn("apuibjhxinumxbfnqlkp", self.code)
        self.assertNotIn("dalfvgehosxfyxkptxwx", self.code)
        self.assertIn("if (u.hostname !== STAGING_REF", self.code)

    def test_private_tokens_not_handled_at_server(self):
        self.assertIn("cache-control", self.code)
        self.assertIn("no-store", self.code)
        self.assertIn("referrer-policy", self.code)
        self.assertNotIn("console.log(", self.code)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", self.code)
        self.assertNotIn("sb_secret_", self.code)
        self.assertNotIn("access_token", self.code)

    def test_only_get_redirects_to_preview(self):
        self.assertIn(PREVIEW, self.code)
        self.assertIn("status:302", self.code)
        self.assertIn("req.method !== 'GET'", self.code)
        self.assertIn("status:405", self.code)
        self.assertNotIn("text/html", self.code.split("Deno.serve",1)[1])

    def test_safe_response_headers(self):
        for item in ("x-content-type-options","x-frame-options","no-referrer","no-store"):
            self.assertIn(item, self.code)

if __name__ == "__main__":
    unittest.main()
