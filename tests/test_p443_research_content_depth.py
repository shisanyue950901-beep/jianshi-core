import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"web"/"build.py"


def builder():
    spec=importlib.util.spec_from_file_location("jianshi_build_p443",BUILD)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class P443EvidenceContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run(
            [sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        )
        cls.home=(ROOT/"web/dist/index.html").read_text(encoding="utf-8")
        cls.catalog=(ROOT/"web/dist/opportunities/index.html").read_text(encoding="utf-8")
        cls.detail=(ROOT/"web/dist/opportunity/vertical-industry-saas/index.html").read_text(encoding="utf-8")

    def test_home_to_six_category_comparison_navigation(self):
        self.assertIn('href="/opportunities/#category-comparison"',self.home)
        self.assertIn('id="category-comparison"',self.catalog)
        self.assertIn("六类商业项目，一张表看清差别",self.catalog)
        self.assertEqual(self.catalog.count('<tr><th scope="row"><a href="/opportunity/'),6)
        self.assertIn("保持原有分类顺序",self.catalog)
        self.assertIn("中位数不可作为收益潜力排名",self.catalog)
        self.assertIn('tabindex="0"',self.catalog)

    def test_fixture_comparison_never_invents_financial_numbers(self):
        self.assertIn("有报价样本",self.catalog)
        self.assertIn("匿名预览",self.catalog)
        self.assertIn("未提供可公开值，不代表零",self.catalog)
        # Offline fallback only has sample counts, no financial medians.
        self.assertIn("—",self.catalog)

    def test_detail_explains_multi_label_chart_and_freshness(self):
        self.assertIn("业务领域分布",self.detail)
        self.assertIn("各项数量不可相加",self.detail)
        self.assertIn("未提供可展示的来源更新时间",self.detail)
        self.assertIn("不按零处理",self.detail)
        self.assertIn("匿名案例",self.detail)
        self.assertIn("不代表全分类缺失率",self.detail) if "不代表全分类缺失率" in self.detail else self.assertIn("没有可公开的匿名案例预览",self.detail)

    def test_synthetic_public_niches_are_bounded_escaped_and_missing_safe(self):
        b=builder()
        s={
            "active_sample_count":4,
            "niche_distribution":[
                {"name":"商业<script>alert(1)</script>","count":9},
                {"name":"科技","count":2},
                {"name":"缺失","count":None},
                {"name":"坏数字","count":"bad"},
                {"name":"","count":3},
            ],
        }
        rendered=b._public_niche_bars(s)
        self.assertNotIn("商业&lt;script&gt;",rendered)
        self.assertNotIn("<script>",rendered)
        self.assertIn("width:50.0%",rendered)
        self.assertNotIn("width:225",rendered)
        self.assertIn("部分领域统计数量超过该分类样本总数",rendered)
        self.assertIn("&lt;敏感字段&gt;",b._sample_rows({"samples":[{"display_name":"<敏感字段>"}]}))
        self.assertIn("坏数字",str(s))
        self.assertNotIn("坏数字",rendered)
        self.assertIn("无法绘制领域分布",b._public_niche_bars({
            "active_sample_count":0,"niche_distribution":[{"name":"科技","count":2}]
        }))

    def test_anonymized_case_missing_fields_are_preview_only(self):
        b=builder()
        cases=[
            {"display_name":"中文样本","monthly_revenue_band":"未披露",
             "monthly_profit_band":"1万—5万美元","asking_price_band":"未披露"},
            {"display_name":"<敏感字段>","monthly_revenue_band":"未披露",
             "monthly_profit_band":"未披露","asking_price_band":"10万—50万美元"},
        ]
        details=b._public_case_completeness({"samples":cases})
        self.assertIn("2",details)
        self.assertIn("月营收未披露",details)
        self.assertIn("月净利润未披露",details)
        self.assertIn("挂牌报价未披露",details)
        rows=b._sample_rows({"samples":cases})
        self.assertIn("匿名案例 01",rows)
        self.assertIn("匿名案例 02",rows)
        self.assertIn("&lt;敏感字段&gt;",rows)
        self.assertNotIn("<敏感字段>",rows)

    def test_do_not_promote_editorial_or_private_source_fields(self):
        for s in (self.home,self.catalog,self.detail):
            for forbidden in (
                "优先研究","值得研究","一人公司适配","第一轮怎么验证",
                "为什么推荐","Empire Flippers","empireflippers.com",
                "listing_number","source_updated_at",
            ):
                self.assertNotIn(forbidden,s)
        self.assertIn("noindex,nofollow",self.detail)

if __name__=="__main__":
    unittest.main()
