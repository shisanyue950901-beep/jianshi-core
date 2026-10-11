"""P4.45: one actual JIANSHI 2.0 homepage, no stacked legacy presentation."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/release"))
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases
from p412_build_public import assert_safe_source
from p445_unified_home import build_home
import p442_jianshi2_live_home as artwork


class UnifiedHome(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = eligible_cases(parse_cases())
        cls.home = build_home(cls.cases)

    def test_one_homepage_and_no_old_gallery(self):
        page = self.home
        self.assertEqual(page.count('<main id="top">'), 1)
        self.assertEqual(page.count("<style>"), 1)
        self.assertEqual(page.count("<script>"), 1)
        self.assertEqual(page.count('data:image/webp;base64,'), 1)
        self.assertEqual(page.count('id="j2"'), 1)
        self.assertEqual(page.count('<article class="j2-project">'), 3)
        self.assertLess(len(page.encode("utf-8")), 200_000)
        assert_safe_source(page)
        for old in ('id="ring"', 'id="lb"', 'id="grid"',
                    'id="splash"', 'id="archive"', 'id="recommendations"',
                    'id="modelList"', '<article class="rec-card'):
            self.assertNotIn(old, page)

    def test_five_navigable_business_modules(self):
        for anchor in ("j2-opportunities", "j2-solutions", "j2-marketplace",
                       "j2-talent", "j2-academy"):
            self.assertEqual(self.home.count('id="' + anchor + '"'), 1)
            self.assertIn('href="#' + anchor + '"', self.home)
        self.assertIn('aria-label="主要导航"', self.home)
        self.assertIn('aria-label="移动导航"', self.home)
        self.assertIn("prefers-reduced-motion:reduce", self.home)
        self.assertIn('href="/research/"', self.home)
        self.assertIn('href="/projects/"', self.home)
        self.assertIn('href="/privacy/"', self.home)

    def test_admitted_evidence_only_and_real_counters(self):
        self.assertEqual(len(self.cases), 3)
        self.assertIn("<strong>3</strong><span>有历史经营证据的具名案例", self.home)
        self.assertIn("<strong>0</strong><span>已验证可直接启动的项目", self.home)
        self.assertIn("<strong>6</strong><span>已整理的商业模式", self.home)
        for slug in ("carrd", "plausible", "nerdwallet"):
            self.assertIn('href="/projects/' + slug + '/"', self.home)
        for token in ("Easlo｜", "Louise Lennox", "Tally｜",
                      "Empire Flippers", "listing_number", "source_url"):
            self.assertNotIn(token, self.home)

    def test_unreleased_modules_are_not_fake_services(self):
        for label in ("尚未开放真实服务采购", "当前不展示虚构企业",
                      "目前未开放真实入驻", "课程由团队后续自主制作并上传"):
            self.assertIn(label, self.home)
        self.assertNotIn("10,000+", self.home)
        self.assertNotIn('type="email"', self.home)
        self.assertNotIn('type="password"', self.home)
        self.assertNotIn("JIANSHI_API_URL", self.home)

    def test_legacy_hash_routes_point_to_standalone_research(self):
        self.assertIn('"#item-saas":"/research/vertical-industry-saas/"', self.home)
        self.assertIn('"#archive":"/#j2-opportunities"', self.home)
        self.assertIn('"#models":"/research/"', self.home)
        self.assertIn("location.replace(to)", self.home)
        self.assertNotIn('href="#item-saas"', self.home)

    def test_original_visual_is_static_and_offline(self):
        image = artwork._get_visual()
        self.assertTrue(image.startswith("data:image/webp;base64,"))
        self.assertIn('AI 生成的见势 2.0 概念主视觉', self.home)
        with patch.object(artwork, "VISUAL_SOURCE", ROOT / "missing.webp"):
            with self.assertRaises(FileNotFoundError):
                build_home(self.cases)

    def test_fail_closed_and_unchanged_collector_budget(self):
        with self.assertRaises(RuntimeError):
            build_home(self.cases[:2])
        source = (ROOT / "scripts/release/p445_unified_home.py").read_text()
        for keyword in ("requests.get", "urlopen(", "TinyFish", "GITHUB_TOKEN"):
            self.assertNotIn(keyword, source)
        workflow = (ROOT / ".github/workflows/publish-static.yml").read_text()
        self.assertEqual(workflow.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(workflow.count("cron: '55 6,12,18 * * *'"), 1)
        self.assertEqual(workflow.count('p437_official_github_repo_probe.py --online'), 1)
        self.assertEqual(workflow.count('p426_daily_leads.py --network --max-companies 6'), 1)


if __name__ == "__main__":
    unittest.main()
