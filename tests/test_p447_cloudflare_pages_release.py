"""P4.47: Cloudflare Pages must accept the audited, unified 2.0 homepage."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "web/dist/index.html"
RESEARCH = ROOT / "web/dist/research/index.html"
BUILD = ROOT / "web/build.py"


class CloudflareProductionContract(unittest.TestCase):
    def test_committed_public_snapshot_has_exactly_one_modern_home(self):
        html = HOME.read_text(encoding="utf-8")
        required = (
            'id="j2"', 'id="j2-opportunities"', 'id="j2-solutions"',
            'id="j2-marketplace"', 'id="j2-talent"',
            'id="j2-academy"', 'href="/research/"',
            'href="/projects/"'
        )
        for marker in required:
            self.assertIn(marker, html)
        for obsolete in ('id="ring"', 'id="lb"', 'id="archive"',
                         'id="recommendations"', 'id="splash"'):
            self.assertNotIn(obsolete, html)
        self.assertEqual(html.count("data:image/webp;base64,"), 1)
        self.assertIn('id="category-comparison"', RESEARCH.read_text(encoding="utf-8"))

    def test_real_cloudflare_pages_main_build_environment_succeeds(self):
        env = dict(os.environ)
        env.pop("JIANSHI_API_URL", None)
        env["CF_PAGES"] = "1"
        env["CF_PAGES_BRANCH"] = "main"
        run = subprocess.run(
            [sys.executable, str(BUILD)], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=35
        )
        self.assertEqual(run.returncode, 0, run.stderr[:1200])
        self.assertIn('"api": "audited_committed_public_snapshot"', run.stdout)
        self.assertIn('"no_new_data_requests": true', run.stdout)

    def test_gate_is_not_bypassed_for_missing_critical_public_contract(self):
        source = BUILD.read_text(encoding="utf-8")
        self.assertIn("Committed single JIANSHI2 homepage contract missing", source)
        self.assertIn('home.count("data:image/webp;base64,") != 1', source)
        self.assertIn('id="j2-marketplace"', source)
        self.assertIn('id="j2-academy"', source)
        self.assertIn('id="ring"', source)
        self.assertIn("Published research snapshot mismatch", source)
        self.assertIn("Committed public path protections missing", source)


if __name__ == "__main__":
    unittest.main()
