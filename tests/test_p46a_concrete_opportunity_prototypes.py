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

    def test_first_six_prototypes(self):
        items=self.data["opportunities"]
        self.assertEqual(len(items),6)
        self.assertEqual(
            {x["slug"] for x in items},
            {
                "vertical-industry-saas",
                "amazon-fba-niche-brand",
                "digital-product-business",
                "affiliate-content-site",
                "amazon-kdp-publishing",
                "agency-business",
            },
        )
        by_slug={x["slug"]:x for x in items}
        expected_status={
            "vertical-industry-saas":"优先研究",
            "amazon-fba-niche-brand":"值得研究",
            "digital-product-business":"优先研究",
            "affiliate-content-site":"优先研究",
            "amazon-kdp-publishing":"优先研究",
            "agency-business":"优先研究",
        }
        for slug,status in expected_status.items():
            self.assertEqual(by_slug[slug]["status"],status,slug)

    def test_default_channel_matrix_is_removed(self):
        for item in self.data["opportunities"]:
            self.assertNotIn("channel_matrix",item)
            self.assertIn("overseas_validation",item)
            self.assertIn("china_screening",item)
        for token in ["抖音","小红书","B站","YouTube","TikTok"]:
            self.assertNotIn(token,self.raw)

    def test_user_facing_language_is_chinese_first(self):
        self.assertIn("language_policy",self.data)
        self.assertIn("中文优先",self.data["language_policy"]["default"])
        by_slug={x["slug"]:x for x in self.data["opportunities"]}
        self.assertEqual(by_slug["vertical-industry-saas"]["title"],"垂直行业软件订阅服务（SaaS）")
        self.assertEqual(by_slug["amazon-fba-niche-brand"]["title"],"亚马逊物流（FBA）细分品牌")
        self.assertEqual(by_slug["amazon-kdp-publishing"]["title"],"亚马逊 KDP 数字出版")
        self.assertEqual(by_slug["agency-business"]["title"],"专业服务业务（Agency）")
        titles="\n".join(x["title"] for x in self.data["opportunities"])
        self.assertNotIn("Agency Business",titles)
        self.assertNotIn("Amazon FBA",titles)

    def test_public_display_is_evidence_only(self):
        policy=self.data["public_display_policy"]
        self.assertEqual(policy["mode"],"EVIDENCE_ONLY")
        self.assertIn("china_screening",policy["excluded_editorial_fields"])
        self.assertIn("editorial_judgement",policy["excluded_editorial_fields"])
        self.assertIn("first_validation",policy["excluded_editorial_fields"])
        for item in self.data["opportunities"]:
            ev=item["overseas_validation"]
            self.assertEqual(ev["commercial_source_diversity"],1)
            self.assertTrue(ev["caveat"])

    def test_direct_sample_counts_match_frozen_strict_rules(self):
        by_slug={x["slug"]:x for x in self.data["opportunities"]}
        expected={
            "vertical-industry-saas":4,
            "amazon-fba-niche-brand":70,
            "digital-product-business":9,
            "affiliate-content-site":11,
            "amazon-kdp-publishing":9,
            "agency-business":4,
        }
        for slug,count in expected.items():
            self.assertEqual(by_slug[slug]["overseas_validation"]["direct_samples"],count,slug)
        self.assertEqual(
            by_slug["amazon-fba-niche-brand"]["overseas_validation"]["observed_niche_count"],
            33,
        )
        self.assertEqual(
            by_slug["amazon-kdp-publishing"]["overseas_validation"]["observed_niche_count"],
            16,
        )
        self.assertIn(
            "挂牌项目去重计数",
            by_slug["vertical-industry-saas"]["overseas_validation"]["evidence_scope"],
        )

    def test_user_facing_evidence_copy_has_no_internal_engineering_terms(self):
        forbidden=[
            "Production",
            "active listing",
            "SaaS Business",
            "Amazon FBA Business",
            "Digital Product Business",
            "Affiliate Site",
            "Amazon Associates Site",
            "Display Advertising Site",
            "Amazon KDP Business",
            "Agency Business",
        ]
        forbidden.append("listing")
        for item in self.data["opportunities"]:
            ev=item["overseas_validation"]
            visible=json.dumps(item,ensure_ascii=False)
            for token in forbidden:
                self.assertNotIn(token,visible,item["slug"])
            for niche in ev.get("observed_niches") or []:
                self.assertRegex(niche,r"[\u4e00-\u9fff]",item["slug"])

    def test_prototypes_are_noindex_and_not_added_to_search_index(self):
        self.assertIn('robots="noindex,nofollow"',self.build)
        self.assertIn("prototype_count",self.build)
        self.assertNotIn('search.append({"slug":prototype_slug',self.build)

    def test_fixture_build_renders_evidence_first_template(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        forbidden=[
            "优先研究","值得研究","一人公司适配","适合谁","不太适合谁",
            "可以复制什么","为什么推荐","第一轮怎么验证","风险与未知",
        ]
        for slug in [
            "vertical-industry-saas",
            "amazon-fba-niche-brand",
            "digital-product-business",
            "affiliate-content-site",
            "amazon-kdp-publishing",
            "agency-business",
        ]:
            page=ROOT/"web"/"dist"/"opportunity"/slug/"index.html"
            self.assertTrue(page.exists(),slug)
            html=page.read_text(encoding="utf-8")
            self.assertIn("项目研究档案",html)
            self.assertIn("样本纳入规则",html)
            self.assertIn("挂牌样本摘要",html)
            self.assertIn("证据边界",html)
            self.assertIn("noindex,nofollow",html)
            for token in forbidden:
                self.assertNotIn(token,html,slug)
        fba=(ROOT/"web"/"dist"/"opportunity"/"amazon-fba-niche-brand"/"index.html").read_text(encoding="utf-8")
        self.assertIn("亚马逊物流（FBA）细分品牌",fba)
        self.assertIn(">70<",fba)
        kdp=(ROOT/"web"/"dist"/"opportunity"/"amazon-kdp-publishing"/"index.html").read_text(encoding="utf-8")
        self.assertIn("亚马逊 KDP 数字出版",kdp)
        self.assertIn(">9<",kdp)
        agency=(ROOT/"web"/"dist"/"opportunity"/"agency-business"/"index.html").read_text(encoding="utf-8")
        self.assertIn("专业服务业务（Agency）",agency)


    def test_controlled_user_path_surfaces_projects_without_indexing_them(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        home=(ROOT/"web"/"dist"/"index.html").read_text(encoding="utf-8")
        catalog=(ROOT/"web"/"dist"/"opportunities"/"index.html").read_text(encoding="utf-8")
        prototype_slugs=[x["slug"] for x in self.data["opportunities"]]

        self.assertIn("先看证据",home)
        self.assertIn("项目研究库",catalog)
        self.assertIn("中文整理的海外项目类别",catalog)
        for slug in prototype_slugs:
            href=f'/opportunity/{slug}/'
            self.assertIn(href,home,slug)
            self.assertIn(href,catalog,slug)

        saas=(ROOT/"web"/"dist"/"opportunity"/"vertical-industry-saas"/"index.html").read_text(encoding="utf-8")
        self.assertIn("其他研究分类",saas)
        self.assertIn("/opportunities/",saas)
        self.assertIn("/opportunity/digital-product-business/",saas)

        search=json.loads((ROOT/"web"/"dist"/"search-index.json").read_text(encoding="utf-8"))
        indexed_slugs={x["slug"] for x in search}
        sitemap=(ROOT/"web"/"dist"/"sitemap.xml").read_text(encoding="utf-8")
        for slug in prototype_slugs:
            self.assertNotIn(slug,indexed_slugs)
            self.assertNotIn(f"/opportunity/{slug}/",sitemap)


    def test_signal_layer_is_separate_from_market_evidence(self):
        self.assertIn("趋势信号与商业样本分开看",self.build)
        self.assertIn("技术热度、内容传播和系统评分保留在独立模块",self.build)
        self.assertNotIn("AUTO_OPPORTUNITY_VALIDATION",self.build)


if __name__=="__main__":
    unittest.main()
