"""P4.14: 两类第一方入口、动画安全边界与编辑档案一致性回归。"""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web/prototypes/p412e/index.html"
CASES = ROOT / "config/p413_public_project_library.json"

class TestP414OfficialLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.editorial = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        match = re.search(r"const EXTRA_CASES=(\[.*?\]);\s*ITEMS\.push\(\.\.\.EXTRA_CASES\)", cls.html, re.S)
        assert match, "站点缺失 P4.13 具名资料"
        cls.site_cases = json.loads(match.group(1))

    def test_all_ten_archive_entries_match_editorial_homepages(self):
        self.assertEqual(len(self.editorial), 10)
        self.assertEqual(len(self.site_cases), 10)
        by_id = {item["id"]: item for item in self.site_cases}
        self.assertEqual(len(by_id), 10)
        for case in self.editorial:
            rendered = by_id[case["id"]]
            self.assertEqual(case["officialHomeUrl"], rendered["officialHomeUrl"])
            self.assertEqual(case["sourceUrl"], rendered["sourceUrl"])
            self.assertEqual(case["officialHomeUrl"], case["officialHomeUrl"].split("?")[0])
            for field in ("officialHomeUrl", "sourceUrl"):
                url = urlsplit(case[field])
                self.assertEqual(url.scheme, "https")
                self.assertTrue(url.hostname)
                self.assertIsNone(url.username)
                self.assertIsNone(url.password)
                self.assertNotIn(url.hostname, {"localhost", "127.0.0.1"})
            self.assertEqual(urlsplit(case["officialHomeUrl"]).path, "/")

    def test_first_two_visual_projects_gain_both_real_links(self):
        self.assertIn(
            "Object.assign(ITEMS[0],{officialHomeUrl:'https://www.easlo.co/',sourceUrl:'https://www.easlo.co/templates'});",
            self.html,
        )
        self.assertIn(
            "Object.assign(ITEMS[1],{officialHomeUrl:'https://www.authorlouiselennox.com/',sourceUrl:'https://www.authorlouiselennox.com/books'});",
            self.html,
        )

    def test_explicit_separate_homepage_and_evidence_navigation(self):
        self.assertIn("官方入口与核对依据", self.html)
        self.assertIn("访问项目官方网站（首页） ↗", self.html)
        self.assertIn("查看核对依据（产品／定价页） ↗", self.html)
        self.assertIn("safePublicUrl(item.officialHomeUrl)", self.html)
        self.assertIn("safePublicUrl(item.sourceUrl)", self.html)
        self.assertIn("if(item.kind==='case')", self.html)
        self.assertIn("link.target='_blank'", self.html)
        self.assertIn("link.rel='noopener noreferrer'", self.html)
        self.assertIn("parsed.protocol!=='https:'", self.html)
        self.assertNotIn("Empire Flippers", self.html)

    def test_single_file_motion_and_safe_release_contract(self):
        self.assertEqual(self.html.count("data:image/webp;base64,"), 8)
        self.assertEqual(self.html.count("<style>"), 1)
        self.assertEqual(self.html.count("<script>"), 1)
        self.assertIn("ITEMS.filter(item=>!item.archiveOnly).forEach", self.html)
        for name in ("prefers-reduced-motion", "viewport-fit=cover", "100dvh", "inert", "id=\"lb\""):
            self.assertIn(name, self.html)
        self.assertLess(len(self.html.encode("utf-8")), 250000)
        script = (ROOT / "scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn('OUTPUT = ROOT / "web" / "dist"', script)

if __name__ == "__main__":
    unittest.main()
