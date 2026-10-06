import subprocess, sys, unittest
from pathlib import Path

class TestR6ChineseHome(unittest.TestCase):
    def test_first_screen_explains_product(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        for text in [
            "互联网商业机会与趋势情报平台",
            "筛出真正值得行动的机会",
            "什么值得做、什么值得讲、什么值得继续盯",
            "我想找项目",
            "我想找选题",
            "一句话看懂见势",
            "我们怎么判断",
            "正在起势",
            "值得做",
            "值得讲",
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
