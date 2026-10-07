import subprocess, sys, unittest
from pathlib import Path

class TestR6ChineseHome(unittest.TestCase):
    def test_first_screen_explains_product(self):
        subprocess.run([sys.executable,"web/build.py"],check=True,capture_output=True,text=True)
        index=Path("web/dist/index.html").read_text(encoding="utf-8")
        for text in [
            "商业机会发现与决策平台",
            "发现下一个",
            "值得做的项目",
            "项目机会、四维评分和行动判断",
            "发现机会",
            "看今日推荐",
            "我是内容创作者",
            "见势解决什么问题",
            "我们怎么判断",
            "正在起势",
            "内容选题",
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
