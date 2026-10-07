import subprocess, sys, unittest
from pathlib import Path

class TestR6ChineseHome(unittest.TestCase):
    def test_first_screen_explains_product(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        for text in [
            "海外商业项目研究",
            "先看证据",
            "公开商业市场中的真实挂牌样本",
            "项目研究库",
            "当前在售样本",
            "独立商业来源",
            "挂牌披露",
            "证据边界",
        ]:
            self.assertIn(text,index)


    def test_primary_ui_is_chinese_first(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        for old in ["BUSINESS SIGNAL INTELLIGENCE","VALIDATED","WATCHLIST","TECH SIGNALS"]:
            self.assertNotIn(old,index)
        self.assertIn("JIANSHI",index)

    def test_signal_scores_are_labeled_as_system_metrics(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        page=Path("web/dist/today/index.html").read_text(encoding="utf-8")
        for text in ["综合指标","系统研究指标","不构成项目推荐"]:
            self.assertIn(text,page)
        self.assertNotIn("值得做",page)
        self.assertNotIn("值得讲",page)


if __name__=="__main__":
    unittest.main()
