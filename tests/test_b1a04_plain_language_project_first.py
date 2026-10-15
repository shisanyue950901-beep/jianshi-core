"""B1-A04: everyday language, real projects before internal research architecture.

This is a static-source acceptance test, not a simulated human user.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from p423_build_project_proofs import parse_cases, index_page
from p425_public_admission import eligible_cases
from p445_unified_home import build_home
import p442_jianshi2_live_home as portal


class TestB1A04ProjectFirst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = eligible_cases(parse_cases())
        cls.home = build_home(cls.cases)
        cls.listing = index_page(cls.cases)

    def test_first_screen_starts_with_workable_business_intent(self):
        html = self.home
        self.assertIn("想找个项目做？", html)
        self.assertIn("直接看项目 ↓", html)
        self.assertIn("现在可以看的创业案例", html)
        self.assertIn("先看模式，再看风险", html)
        self.assertIn("<title>见势｜找创业项目，看懂怎么赚钱</title>", html)
        self.assertLess(html.index("现在可以看的创业案例"),
                        html.index("还想看看其他方向？"))
        self.assertLess(html.index('class="j2-projects"'),
                        html.index('class="j2-metrics"'))
        self.assertLess(html.index('class="j2-projects"'),
                        html.index('class="j2-shortcuts"'))
        self.assertLess(html.index('class="j2-projects"'),
                        html.index('id="j2-solutions"'))

    def test_every_project_previews_revenue_buyer_and_difficulty(self):
        # Build the 3 cards from the reviewed JSON score ranking, not old cases.
        from t08_project_selection import featured_projects, usd
        winners=featured_projects()
        self.assertEqual(len(winners),3)
        self.assertEqual(self.home.count('class="j2-project-facts"'),3)
        for project in winners:
            with self.subTest(project=project["id"]):
                self.assertIn(project["name"],self.home)
                self.assertIn(project["one_liner_cn"],self.home)
                self.assertIn(usd(project["revenue"]["last_30d"]),self.home)
                self.assertIn(project["verdict"],self.home)
                self.assertIn('href="/projects/' + project["id"] + '/"',self.home)
        for label in ("近30天收入","研究结论","总分"):
            self.assertEqual(self.home.count('<dt>'+label+'</dt>'),3)
        for stale in ("carrd","plausible","nerdwallet"):
            self.assertNotIn('href="/projects/'+stale+'/"',self.home)

    def test_below_the_fold_keeps_current_risk_not_fake_business(self):
        for fragment in ("有历史经营证据的具名案例",
                         "已验证可直接启动的项目",
                         "已整理的商业模式",
                         "尚未开放真实服务采购",
                         "当前不展示虚构企业",
                         "目前未开放真实入驻",
                         "课程由团队后续自主制作并上传"):
            self.assertIn(fragment, self.home)
        self.assertIn("<strong>0</strong><span>已验证可直接启动的项目", self.home)
        for bad in ("100%成功率", "保证赚钱", "真实客户 500 家", "已完成融资"):
            self.assertNotIn(bad, self.home)

    def test_directory_starts_with_plain_offer_instead_of_evidence_preamble(self):
        page = self.listing
        self.assertIn("看看它们怎么赚钱", page)
        self.assertIn("怎么赚钱：", page)
        self.assertIn("谁在用：", page)
        self.assertIn("谁付钱：", page)
        self.assertIn("广告合作伙伴；读者不等于广告付款方", page)
        self.assertIn("<details class=\"notice\"><summary>资料来源和风险说明</summary>", page)
        self.assertIn("只找到官网或标价", page)  # clear limitation preserved
        self.assertEqual(len(re.findall(r'href="/projects/[a-z0-9-]+/"', page)), 3)
        self.assertIn("想看更多生意方向？去找项目", page)
        self.assertNotIn('data-sort=', page)
        self.assertNotIn('id="projectSearch"', page)
        self.assertIn("上手门槛：", page)
        self.assertNotIn("直接复制就能赚到钱", page)

    def test_security_and_page_count_stay_frozen(self):
        self.assertEqual(len(self.cases), 3)
        self.assertEqual(self.home.count("<script>"), 1)
        self.assertEqual(self.home.count("data:image/webp;base64,"), 1)
        self.assertLess(len(self.home.encode("utf-8")), 200000)
        for x in ("j2-opportunities","j2-solutions","j2-marketplace",
                  "j2-talent","j2-academy"):
            self.assertEqual(self.home.count('id="'+x+'"'),1)
        for banned in ('type="email"', 'type="password"', "<form",
                       "navigator.sendBeacon", "XMLHttpRequest("):
            self.assertNotIn(banned,self.home)
        wf = (ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"),1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"),1)


if __name__ == "__main__":
    unittest.main()
