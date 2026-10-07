import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"config"/"p47a_overseas_project_candidate_pool.json"

class TestP47AOverseasProjectCandidatePool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(CFG.read_text(encoding="utf-8"))

    def test_product_core_is_original_simple_flow(self):
        self.assertEqual(
            self.data["product_core"],
            "海外已验证的一人公司 / 小团队项目 → 筛选 → 中文解释 → 推荐给中国用户",
        )

    def test_exactly_twelve_candidates(self):
        self.assertEqual(len(self.data["candidates"]),12)
        self.assertEqual(
            [x["rank"] for x in self.data["candidates"]],
            list(range(1,13)),
        )

    def test_direct_counts_use_primary_business_rules(self):
        by_slug={x["slug"]:x for x in self.data["candidates"]}
        expected={
            "vertical-industry-saas":4,
            "digital-product-business":9,
            "affiliate-content-site":11,
            "amazon-kdp-publishing":8,
            "agency-business":4,
            "application-business":3,
            "youtube-channel-business":16,
            "amazon-merch-business":4,
            "non-amazon-ecommerce-brand":22,
            "amazon-fba-niche-brand":69,
            "dropshipping-niche-store":4,
            "newsletter-business":1,
        }
        self.assertEqual({k:by_slug[k]["direct_samples"] for k in expected},expected)

    def test_candidate_titles_are_chinese_first(self):
        by_slug={x["slug"]:x for x in self.data["candidates"]}
        self.assertEqual(by_slug["vertical-industry-saas"]["title"],"垂直行业软件订阅服务（SaaS）")
        self.assertEqual(by_slug["amazon-fba-niche-brand"]["title"],"亚马逊物流（FBA）细分品牌")
        self.assertEqual(by_slug["agency-business"]["title"],"垂直服务型业务")
        self.assertEqual(by_slug["newsletter-business"]["title"],"垂直邮件订阅媒体（Newsletter）")
        self.assertIn("language_policy",self.data)
        self.assertIn("中文优先",self.data["language_policy"]["default"])

    def test_one_person_is_editorial_not_source_fact(self):
        self.assertIn("仅为见势编辑筛选",self.data["one_person_rule"])
        self.assertEqual(self.data["evidence_source_diversity"],1)

    def test_next_detail_batch_is_bounded(self):
        self.assertEqual(
            self.data["detail_page_next_batch"],
            [
                "digital-product-business",
                "affiliate-content-site",
                "amazon-kdp-publishing",
                "agency-business",
                "non-amazon-ecommerce-brand",
            ],
        )

    def test_no_channel_matrix_or_platform_marketing_framework(self):
        raw=CFG.read_text(encoding="utf-8")
        self.assertNotIn("channel_matrix",raw)
        self.assertNotIn("TikTok",raw)
        self.assertNotIn("抖音",raw)

if __name__=="__main__":
    unittest.main()
