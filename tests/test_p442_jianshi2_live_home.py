"""P4.42 release portal: preserve audited source admission and legacy safety."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/release"))
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases, public_home
import p442_jianshi2_live_home as portal
from p412_build_public import assert_safe_source


class Jianshi2ProductionPortal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "web/prototypes/p412e/index.html").read_text(encoding="utf-8")
        cls.cases = eligible_cases(parse_cases())
        cls.base = public_home(cls.source, cls.cases)
        cls.result = portal.integrate(cls.base, cls.cases)

    def test_release_build_single_published_layout_and_source_safe(self):
        self.assertEqual(len(self.cases), 3)
        self.assertEqual(self.result.count('<main id="top">'), 1)
        self.assertEqual(self.result.count('<style>'), 1)
        self.assertEqual(self.result.count('<script>'), 1)
        self.assertEqual(self.result.count('data:image/webp;base64,'), 9)
        assert_safe_source(self.source)
        assert_safe_source(self.result, source_prototype=False)
        self.assertLess(len(self.result.encode("utf-8")), 400_000)
        self.assertLess(self.result.index('id="j2"'), self.result.index('id="recommendations"'))

    def test_five_live_navigation_targets_and_empty_states(self):
        for anchor in ("j2-opportunities","j2-solutions","j2-marketplace",
                       "j2-talent","j2-academy"):
            self.assertEqual(self.result.count('id="' + anchor + '"'), 1)
            self.assertIn('href="#' + anchor + '"', self.result)
        self.assertIn('href="/research/"', self.result)
        self.assertIn('href="/projects/"', self.result)
        self.assertIn('当前不展示虚构企业', self.result)
        self.assertIn('尚未开放真实服务采购', self.result)
        self.assertIn('课程由团队后续自主制作并上传', self.result)
        self.assertNotIn('JIANSHI_API_URL', self.result)
        self.assertNotIn('GH_TOKEN', self.result)

    def test_only_admitted_cases_and_attested_counts(self):
        for slug in ("carrd","plausible","nerdwallet"):
            self.assertIn('href="/projects/' + slug + '/"', self.result)
        for unsafe in ("Easlo｜","Louise Lennox","Tally｜","Empire Flippers"):
            self.assertNotIn(unsafe, self.result)
        self.assertIn('<strong>3</strong><span>有历史经营证据的具名案例', self.result)
        self.assertIn('<strong>0</strong><span>已验证可直接启动的项目', self.result)
        self.assertIn('<strong>6</strong><span>已整理的商业模式', self.result)
        for marker in ('id="ring"','id="lb"','id="grid"',
                       'id="skipSplash"','id="themeToggle"',
                       'id="recommendations"','id="models"'):
            self.assertIn(marker, self.result)

    def test_artwork_read_from_reviewed_local_preview_no_network(self):
        image = portal._get_visual()
        self.assertTrue(image.startswith("data:image/webp;base64,"))
        self.assertIn('概念主视觉', self.result)
        self.assertIn('prefers-reduced-motion:reduce', self.result)
        with patch.object(portal, "VISUAL_SOURCE", ROOT / "missing.webp"):
            with self.assertRaises(FileNotFoundError):
                portal.integrate(self.base, self.cases)

    def test_fail_closed_for_unapproved_or_malformed_inputs(self):
        with self.assertRaises(RuntimeError):
            portal.render_portal(self.cases[:2])
        with self.assertRaises(RuntimeError):
            portal.integrate("<html></html>", self.cases)
        with self.assertRaises(RuntimeError):
            portal.integrate(self.result, self.cases)

    def test_all_public_source_files_and_cron_remain_unchanged(self):
        wf = (ROOT / ".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"), 1)
        self.assertIn("p441_schedule_claim.py", wf)
        self.assertEqual(wf.count('p437_official_github_repo_probe.py --online'), 1)
        self.assertEqual(wf.count('p426_daily_leads.py --network --max-companies 6'), 1)
        self.assertNotIn('requests.get(', (ROOT / "scripts/release/p442_jianshi2_live_home.py").read_text())
        self.assertNotIn('urllib', (ROOT / "scripts/release/p442_jianshi2_live_home.py").read_text())


if __name__ == "__main__":
    unittest.main()
