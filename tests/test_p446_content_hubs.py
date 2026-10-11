"""P4.46: substantive editorial pages without fake deals or data exfiltration."""
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/release"))
sys.path.insert(0, str(ROOT / "scripts/security"))
import p446_content_hubs as hubs
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases
from p445_unified_home import build_home


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.forms = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "form":
            self.forms += 1
        if attrs.get("id"):
            self.ids.add(attrs["id"])


class P446ContentHubs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = hubs.render_pages()
        cls.home = build_home(eligible_cases(parse_cases()))

    def test_eight_real_pages_have_one_semantic_layout(self):
        self.assertEqual(len(self.pages), 8)
        self.assertEqual(set(self.pages), set(hubs.PAGES))
        self.assertEqual(len(hubs.SOLUTIONS), 4)
        for route, html in self.pages.items():
            with self.subTest(route=route):
                self.assertIn("JIANSHI 2.0", html)
                self.assertEqual(html.count("<main>"), 1)
                self.assertEqual(html.count("</main>"), 1)
                self.assertEqual(html.count("<style>"), 1)
                self.assertEqual(html.count('rel="canonical"'), 1)
                self.assertIn("https://jianshi-bua.pages.dev/" + route, html)
                self.assertEqual(html.count("<script>"), 1 if route == "solutions/" else 0)
                self.assertNotIn("<form", html)
                self.assertIn('href="/privacy/"', html)
                self.assertIn("prefers-reduced-motion:reduce", html)
                self.assertIn("尚未开放在线委托", html)
                self.assertLess(len(html.encode("utf-8")), 80_000)
                tags = Links()
                tags.feed(html)
                self.assertEqual(tags.forms, 0)
                self.assertIn("/", tags.links)

    def test_solution_directory_all_four_details_and_deliverables(self):
        main = self.pages["solutions/"]
        self.assertIn("先找到问题", main)
        self.assertEqual(main.count('class="card link"'), 4)
        self.assertIn('id="catalog"', main)
        for row in hubs.SOLUTIONS:
            path = "solutions/" + row["slug"] + "/"
            detail = self.pages[path]
            self.assertIn('href="/solutions/' + row["slug"] + '/"', main)
            for fragment in ("典型业务问题", "企业需要准备", "建议实施流程",
                             "参考交付清单", "验收与质量检查",
                             "使用与责任边界", row["boundary"]):
                self.assertIn(fragment, detail)
            self.assertEqual(detail.count('id="delivery"'), 1)

    def test_marketplace_has_a_real_preparation_template_not_fake_jobs(self):
        page = self.pages["marketplace/"]
        for x in ("需求说明应包含的字段", "期望完成时间", "质量验收与修改标准",
                  "企业身份与联系人授权", "商机列表尚未开放"):
            self.assertIn(x, page)
        self.assertIn('id="request-brief"', page)
        self.assertNotIn('name="company-phone"', page)
        self.assertNotIn("立即竞标", page)

    def test_talent_protects_contact_information(self):
        page = self.pages["talent/"]
        for x in ("作品集参考结构", "演示作品明确标注",
                  "没有授权就不公开", "尚未开放创作者入驻"):
            self.assertIn(x, page)
        self.assertIn('id="portfolio"', page)
        self.assertNotIn("立即申请", page)

    def test_academy_is_a_course_plan_not_fake_videos(self):
        page = self.pages["academy/"]
        self.assertEqual(page.count("CURRICULUM PLAN"), len(hubs.COURSE_PATHS))
        self.assertIn('id="learning-paths"', page)
        self.assertIn("课程正式上线前需要完成什么", page)
        self.assertIn("没有已上线的可播放课程", page)
        self.assertNotIn('<video', page)
        self.assertNotIn("付款购买", page)

    def test_home_to_deep_content_paths(self):
        for path in ("/solutions/", "/marketplace/", "/talent/", "/academy/"):
            self.assertIn('href="' + path + '"', self.home)
        for row in hubs.SOLUTIONS:
            self.assertIn('href="/solutions/' + row["slug"] + '/"', self.home)
        for anchor in ("j2-opportunities", "j2-solutions", "j2-marketplace",
                       "j2-talent", "j2-academy"):
            self.assertIn('id="' + anchor + '"', self.home)
        self.assertEqual(self.home.count('data:image/webp;base64,'), 1)

    def test_offline_write_and_privacy_scanner(self):
        from p411_audit_public_artifacts import PATTERNS
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(hubs.publish(root), 8)
            for route in hubs.PAGES:
                file = root / route / "index.html"
                self.assertTrue(file.is_file())
                content = file.read_text(encoding="utf-8")
                for name, pattern in PATTERNS.items():
                    self.assertIsNone(pattern.search(content), (route, name))
            for private in ("config", "db", "supabase", "docs", "scripts"):
                self.assertFalse((root / private).exists())

    def test_source_admission_and_daily_collector_boundaries(self):
        s = (ROOT / "scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn("eligible_cases(parse_cases())", s)
        self.assertIn("publish_content_hubs(OUTPUT)", s)
        self.assertIn("for route in CONTENT_PAGES", s)
        for path in ("scripts/release/p446_content_hubs.py",
                     "scripts/release/p445_unified_home.py"):
            file = (ROOT / path).read_text(encoding="utf-8")
            for marker in ("requests.get(", "urlopen(", "GH_TOKEN", "GITHUB_TOKEN"):
                self.assertNotIn(marker, file)
        wf = (ROOT / ".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"), 1)


if __name__ == "__main__":
    unittest.main()
