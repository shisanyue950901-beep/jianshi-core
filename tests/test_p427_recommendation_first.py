"""P4.27: front page recommends research paths before data, without false startup claims."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases,public_home
from p427_recommendation_first import render_recommendations

class RecommendationFirstTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
        cls.cases=eligible_cases(parse_cases())
        cls.page=public_home(cls.source,cls.cases)

    def test_first_screen_is_an_honest_recommendation_not_an_image_wall(self):
        html=self.page
        self.assertEqual(len(self.cases),3)
        self.assertLess(html.index('id="recommendations"'),html.index('class="hero"'))
        self.assertLess(html.index('id="recommendations"'),html.index('id="archive"'))
        self.assertIn("找到值得你验证的生意",html)
        self.assertIn("不是保证赚钱的项目榜单",html)
        self.assertIn("已验证可直接启动的项目",html)
        self.assertIn("<strong>0</strong>",html)
        self.assertIn("主要导航",html)
        self.assertIn('<a href="#recommendations">发现项目</a>',html)
        self.assertIn("根据我的条件筛选",html)
        self.assertIn("一个人能先测试",html)
        self.assertIn("查看推荐项目",html)
        self.assertIn('href="#pick-list"',html)
        self.assertIn('id="quick-start"',html)
        self.assertIn('href="#case-carrd"',html)
        self.assertEqual(html.count('<article class="rec-card'),3)
        self.assertIn("不建议一人低资金直接照搬",html)

    def test_order_separates_research_from_direct_startup_advice(self):
        html=self.page
        a=html.index('data-case="carrd"')
        b=html.index('data-case="plausible"')
        c=html.index('data-case="nerdwallet"')
        self.assertLess(a,b)
        self.assertLess(b,c)
        for slug in ("carrd","plausible","nerdwallet"):
            self.assertIn('href="/projects/'+slug+'/"',html)
        self.assertIn("历史经营",html)
        self.assertIn("研究计划",html)
        self.assertIn("获客",html)
        self.assertIn("不证明新创业者可以复制",html)
        self.assertIn("先锁定一个更小的客户群",html)

    def test_evidence_is_only_admitted_individual_company_cases(self):
        html=self.page
        self.assertIn("8.366 亿美元",html)
        self.assertIn("10 万美元 MRR",html)
        self.assertIn("7,000 多位",html)
        self.assertIn("未经独立财务审计",html)
        self.assertIn("2025-12-31",html)
        self.assertIn("2022",html)
        self.assertNotIn("Easlo｜",html)
        self.assertNotIn("Louise Lennox",html)
        self.assertNotIn("Tally｜",html)
        self.assertEqual(html.count("data:image/webp;base64,"),8)
        self.assertEqual(html.count("<style>"),1)
        self.assertEqual(html.count("<script>"),1)
        self.assertIn('data-theme="light"',html)
        self.assertLess(len(html.encode("utf-8"))+124,260000)

    def test_no_auto_recommendation_if_admission_sources_missing(self):
        with self.assertRaises(RuntimeError):
            render_recommendations([])
        with self.assertRaises(RuntimeError):
            public_home(self.source,[])
        with self.assertRaises(RuntimeError):
            from p427_recommendation_first import recommendation_first_home
            recommendation_first_home('<main id="top"><style></style>',[{"id":"made-up","evidence_level":1}])

    def test_build_public_release_preserves_all_original_data_safety(self):
        r=subprocess.run([sys.executable,"scripts/release/p412_build_public.py"],
                         cwd=ROOT,capture_output=True,text=True,timeout=45)
        self.assertEqual(r.returncode,0,r.stderr)
        page=(ROOT/"web/dist/index.html").read_text(encoding="utf-8")
        self.assertIn('id="j2"',page)
        self.assertEqual(page.count('<article class="j2-project'),3)
        self.assertNotIn('id="recommendations"',page)
        self.assertNotIn('id="ring"',page)
        self.assertTrue((ROOT/"web/dist/projects/carrd/index.html").exists())
        self.assertFalse((ROOT/"web/dist/projects/easlo/index.html").exists())
        self.assertEqual((ROOT/"web/dist/sitemap.xml").read_text(encoding="utf-8").count("<url>"),19)
        self.assertTrue((ROOT/"web/dist/discover/index.html").is_file())
        self.assertTrue((ROOT/"web/dist/sources/index.html").is_file())

if __name__=="__main__":
    unittest.main()
