import subprocess, sys, unittest
from pathlib import Path

class TestR78SoldBusinessSignal(unittest.TestCase):
    def test_score_contract(self):
        sql=Path("db/migrations/0027_sold_status_business_signal.sql").read_text(encoding="utf-8")
        for token in [
            "OPP_V0.2",
            "opportunity_sold_status_metrics_v01",
            "sold_status_count>=5",
            "sold_activity_score*0.05",
            "least(5.0",
            "sold_status_is_not_transaction_price",
        ]:
            self.assertIn(token,sql)
        self.assertIn("(m.source_count>=2 and m.evidence_count>=5)",sql)

    def test_public_feed_uses_v02(self):
        fn=Path("supabase/functions/public-feed/index.ts").read_text(encoding="utf-8")
        self.assertIn('engine_version: "OPP_V0.2"',fn)
        self.assertIn('.eq("score_version", "OPP_V0.2")',fn)

    def test_detail_explains_sold_semantics(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        build=Path("web/build.py").read_text(encoding="utf-8")
        self.assertIn("退出活跃度 · 辅助证据",build)
        self.assertIn("样本还不足 5 个",build)
        self.assertIn("最多只影响 +5 分",build)
        self.assertIn("没有把最后挂牌价当作真实成交价",build)
        self.assertIn("不会把 Sold 样本数解释为成交率",build)

if __name__=="__main__":
    unittest.main()
