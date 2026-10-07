import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"web"/"build.py"
PUBLIC_FEED=ROOT/"supabase"/"functions"/"public-feed"/"index.ts"
CONFIG=ROOT/"config"/"p46a_concrete_opportunity_prototypes.json"


class TestP49EvidenceFirstResearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build=BUILD.read_text(encoding="utf-8")
        cls.feed=PUBLIC_FEED.read_text(encoding="utf-8")
        cls.config=json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_public_feed_has_research_view(self):
        self.assertIn('if (view === "research")',self.feed)
        for token in [
            "active_sample_count",
            "priced_sample_count",
            "median_asking_price",
            "median_monthly_gross_revenue",
            "median_monthly_net_profit",
            "median_profit_margin_pct",
            "median_hours_worked_per_week",
            "niche_distribution",
            "samples",
            "evidence_boundary",
        ]:
            self.assertIn(token,self.feed)

    def test_research_endpoint_is_source_backed_not_editorial(self):
        research_block=self.feed.split('if (view === "research")',1)[1].split('if (view === "detail")',1)[0]
        for forbidden in [
            "editorial_judgement",
            "china_screening",
            "first_validation",
            "solo_fit",
            "recommendation_reason",
        ]:
            self.assertNotIn(forbidden,research_block)
        self.assertIn("财务、工时和报价字段来自挂牌方公开披露",research_block)
        self.assertIn("挂牌报价不等于最终成交价",research_block)

    def test_production_build_uses_live_research_endpoint(self):
        self.assertIn('api_get("research",slug=slug)',self.build)
        self.assertEqual(self.config["snapshot_role"],"BUILD_FALLBACK_ONLY")
        self.assertIn("public-feed?view=research",self.config["live_source_of_truth"])

    def test_fixture_public_pages_exclude_unsupported_editorial_copy(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        pages=[
            ROOT/"web"/"dist"/"index.html",
            ROOT/"web"/"dist"/"opportunities"/"index.html",
            ROOT/"web"/"dist"/"opportunity"/"vertical-industry-saas"/"index.html",
        ]
        forbidden=[
            "优先研究",
            "值得研究",
            "一人公司适配",
            "为什么值得中国用户看",
            "适合谁",
            "不太适合谁",
            "可以复制什么",
            "为什么推荐",
            "第一轮怎么验证",
        ]
        for page in pages:
            html=page.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token,html,str(page))

    def test_fixture_research_detail_uses_professional_evidence_terms(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        html=(ROOT/"web"/"dist"/"opportunity"/"vertical-industry-saas"/"index.html").read_text(encoding="utf-8")
        for token in [
            "MARKET EVIDENCE BRIEF",
            "当前在售样本",
            "独立商业来源",
            "样本纳入规则",
            "挂牌样本摘要",
            "挂牌报价中位数",
            "证据边界",
        ]:
            self.assertIn(token,html)
        self.assertIn("noindex,nofollow",html)

    def test_legacy_signal_pages_no_longer_use_action_language(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        for route in ["today","rising","build","content"]:
            html=(ROOT/"web"/"dist"/route/"index.html").read_text(encoding="utf-8")
            self.assertIn("系统",html)
            self.assertNotIn("值得做",html)
            self.assertNotIn("值得讲",html)


    def test_sample_preview_discloses_visible_vs_total(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        html=(ROOT/"web"/"dist"/"opportunity"/"amazon-fba-niche-brand"/"index.html").read_text(encoding="utf-8")
        self.assertIn("展示最近 0 条 / 当前共 70 条",html)


if __name__=="__main__":
    unittest.main()
