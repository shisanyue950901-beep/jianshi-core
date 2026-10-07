import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"config"/"p46a_concrete_opportunity_prototypes.json"
BUILD=ROOT/"web"/"build.py"


class TestP46AConcreteOpportunityPrototypes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(CONTENT.read_text(encoding="utf-8"))
        cls.raw=CONTENT.read_text(encoding="utf-8")
        cls.build=BUILD.read_text(encoding="utf-8")

    def test_product_core_is_simple_and_explicit(self):
        self.assertEqual(
            self.data["product_core"],
            "海外已验证的一人公司 / 小团队项目 → 筛选 → 中文解释 → 推荐给中国用户",
        )
        self.assertEqual(self.data["audience"],"寻找创业项目与方向的中国中文用户")

    def test_first_four_prototypes(self):
        items=self.data["opportunities"]
        self.assertEqual(len(items),4)
        self.assertEqual(
            {x["slug"] for x in items},
            {
                "vertical-industry-saas",
                "amazon-fba-niche-brand",
                "digital-product-business",
                "affiliate-content-site",
            },
        )
        by_slug={x["slug"]:x for x in items}
        self.assertEqual(by_slug["vertical-industry-saas"]["status"],"值得研究")
        self.assertEqual(by_slug["amazon-fba-niche-brand"]["status"],"值得研究")
        self.assertEqual(by_slug["digital-product-business"]["status"],"优先研究")
        self.assertEqual(by_slug["affiliate-content-site"]["status"],"优先研究")

    def test_default_channel_matrix_is_removed(self):
        for item in self.data["opportunities"]:
            self.assertNotIn("channel_matrix",item)
            self.assertIn("overseas_validation",item)
            self.assertIn("china_screening",item)
        for token in ["抖音","小红书","B站","YouTube","TikTok"]:
            self.assertNotIn(token,self.raw)

    def test_evidence_and_recommendation_stay_separate(self):
        for item in self.data["opportunities"]:
            ev=item["overseas_validation"]
            self.assertEqual(ev["commercial_source_diversity"],1)
            self.assertTrue(ev["caveat"])
            self.assertTrue(item["editorial_judgement"])
            self.assertTrue(item["china_screening"]["copy_path"])
            self.assertTrue(item["unknowns"])

    def test_vertical_saas_direct_sample_count_is_deduped(self):
        by_slug={x["slug"]:x for x in self.data["opportunities"]}
        self.assertEqual(by_slug["vertical-industry-saas"]["overseas_validation"]["direct_samples"],4)
        self.assertIn("listing 去重计数",by_slug["vertical-industry-saas"]["overseas_validation"]["evidence_scope"])

    def test_prototypes_are_noindex_and_not_added_to_search_index(self):
        self.assertIn('robots="noindex,nofollow"',self.build)
        self.assertIn("prototype_count",self.build)
        self.assertNotIn('search.append({"slug":prototype_slug',self.build)

    def test_fixture_build_renders_simplified_six_section_template(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        for slug in [
            "vertical-industry-saas",
            "amazon-fba-niche-brand",
            "digital-product-business",
            "affiliate-content-site",
        ]:
            page=ROOT/"web"/"dist"/"opportunity"/slug/"index.html"
            self.assertTrue(page.exists(),slug)
            html=page.read_text(encoding="utf-8")
            self.assertIn("海外已验证项目 · 中文筛选",html)
            self.assertIn("03 · 海外真实验证",html)
            self.assertIn("04 · 对中国用户有没有参考价值",html)
            self.assertIn("05 · 第一轮怎么验证",html)
            self.assertIn("06 · 风险与未知",html)
            self.assertNotIn("渠道矩阵",html)
            self.assertIn("noindex,nofollow",html)
        digital=(ROOT/"web"/"dist"/"opportunity"/"digital-product-business"/"index.html").read_text(encoding="utf-8")
        affiliate=(ROOT/"web"/"dist"/"opportunity"/"affiliate-content-site"/"index.html").read_text(encoding="utf-8")
        self.assertIn("数字产品业务",digital)
        self.assertIn("9",digital)
        self.assertIn("联盟营销 / 内容站",affiliate)
        self.assertIn("11",affiliate)


if __name__=="__main__":
    unittest.main()
