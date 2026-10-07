import subprocess, sys, unittest
from pathlib import Path

class TestR6ChineseHome(unittest.TestCase):
    def test_first_screen_explains_product(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        for text in [
            "海外已验证项目 · 中文筛选",
            "看懂海外已经跑通的项目",
            "找到你值得验证的方向",
            "筛选、中文解释和第一轮低成本验证路径",
            "先看首批项目",
            "见势解决什么问题",
            "海外项目",
            "商业证据",
            "中国适配",
            "低成本验证",
            "我们怎么判断",
        ]:
            self.assertIn(text,index)

    def test_primary_ui_is_chinese_first(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        for old in ["BUSINESS SIGNAL INTELLIGENCE","VALIDATED","WATCHLIST","TECH SIGNALS"]:
            self.assertNotIn(old,index)
        self.assertNotIn(">JIANSHI<",index)

    def test_action_scores_are_explained(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        for text in ["趋势热度","内容价值","可执行性","商业质量"]:
            self.assertIn(text,index)

if __name__=="__main__":
    unittest.main()
