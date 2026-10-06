import sys, unittest
sys.path.insert(0,"src")
from jianshi.scoring.github_heat import GithubHeatInput, score_github_heat

class TestGithubHeat(unittest.TestCase):
    def test_bounds(self):
        s=score_github_heat(GithubHeatInput(1000,100,30,1,50))
        for v in s.values():
            self.assertGreaterEqual(v,0)
            self.assertLessEqual(v,100)

    def test_recent_growth_increases_heat(self):
        base=score_github_heat(GithubHeatInput(5000,500,100,1,None))["heat"]
        hot=score_github_heat(GithubHeatInput(5000,500,100,1,500))["heat"]
        self.assertGreater(hot,base)

    def test_stale_repo_penalty(self):
        fresh=score_github_heat(GithubHeatInput(1000,100,100,1,None))["heat"]
        stale=score_github_heat(GithubHeatInput(1000,100,100,100,None))["heat"]
        self.assertGreater(fresh,stale)

if __name__=="__main__":
    unittest.main()
