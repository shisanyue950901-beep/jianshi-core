"""Staging-only Auth callback safety contracts; no live Auth tests are implied."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "supabase/functions/jianshi-staging-auth-callback/index.ts"

class StagingAuthCallbackContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = SOURCE.read_text(encoding="utf-8")

    def test_only_staging_project(self):
        self.assertIn("apuibjhxinumxbfnqlkp", self.code)
        self.assertNotIn("dalfvgehosxfyxkptxwx", self.code)
        self.assertIn("STAGING_ONLY", self.code)
        self.assertIn("SUPABASE_URL", self.code)

    def test_private_token_not_rendered_or_logged(self):
        self.assertIn("history.replaceState(null,'',location.pathname)", self.code)
        self.assertIn("cache-control':'no-store", self.code)
        self.assertIn("referrer-policy':'no-referrer", self.code)
        self.assertNotIn("console.log(", self.code)
        self.assertNotIn("JSON.stringify({access_token:", self.code)

    def test_session_requires_verified_identity(self):
        self.assertIn("'/auth/v1/user'", self.code)
        self.assertIn("user?.email===TEST_EMAIL", self.code)
        self.assertIn("email_confirmed_at", self.code)
        self.assertIn("if(!await authenticate(token))", self.code)
        self.assertIn("NO_TOKEN", self.code)
        self.assertIn("ORIGIN_REJECTED", self.code)

    def test_secure_response_headers(self):
        for s in ("content-security-policy", "frame-ancestors 'none'", "default-src 'none'", "x-frame-options", "noindex,nofollow"):
            self.assertIn(s, self.code)

if __name__ == "__main__":
    unittest.main()
