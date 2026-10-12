"""Staging-only Cloudflare preview login contracts (no production enable)."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web/staging-auth-preview/index.html"
SCRIPT = ROOT / "web/staging-auth-preview/callback.js"
BUILDER = ROOT / "scripts/release/p412_build_public.py"
EDGE = ROOT / "supabase/functions/jianshi-staging-auth-callback/index.ts"
PREVIEW = "https://staging-auth-callback.jianshi-bua.pages.dev/_qa/staging-auth/"

class StagingPreviewContract(unittest.TestCase):
    def test_preview_branch_gate_is_exact(self):
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('os.getenv("CF_PAGES_BRANCH") == "staging-auth-callback"', source)
        self.assertIn('preview_source = ROOT / "web" / "staging-auth-preview"', source)
        self.assertIn('"index.html", "callback.js"', source)
        self.assertIn('Referrer-Policy: no-referrer', source)
        self.assertIn("X-Robots-Tag: noindex, nofollow", source)
        self.assertIn("connect-src https://apuibjhxinumxbfnqlkp.supabase.co", source)

    def test_staging_only_html(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('<meta charset="utf-8">', html)
        self.assertIn('noindex,nofollow', html)
        self.assertIn('src="./callback.js"', html)
        self.assertNotIn('analytics.js', html)

    def test_credentials_are_not_leaked(self):
        js = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("sb_publishable_", js)
        self.assertNotIn("sb_secret_", js)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", js)
        self.assertNotIn("dalfvgehosxfyxkptxwx", js)
        self.assertIn("history.replaceState", js)
        self.assertIn("sessionStorage", js)
        self.assertIn("/auth/v1/user", js)
        self.assertIn("/auth/v1/token?grant_type=refresh_token", js)
        self.assertIn("/auth/v1/logout", js)
        self.assertNotIn("console.log(", js)

    def test_unsafe_edge_html_replaced_by_http_redirect(self):
        edge = EDGE.read_text(encoding="utf-8")
        self.assertIn("status:302", edge)
        self.assertIn("const DESTINATION = '" + PREVIEW + "'", edge)
        self.assertIn("cache-control':'no-store", edge)
        self.assertIn("req.method !== 'GET'", edge)
        self.assertIn("status:405", edge)

    @unittest.skipUnless(shutil.which("node"), "Node runtime unavailable")
    def test_javascript_parses(self):
        proc = subprocess.run(["node", "--check", str(SCRIPT)],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr[:1000])

if __name__ == "__main__":
    unittest.main()
