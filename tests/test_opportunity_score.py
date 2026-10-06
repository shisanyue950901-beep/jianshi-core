import sys, unittest
sys.path.insert(0,"src")
from jianshi.scoring.opportunity_score import OpportunityInputs,score

class TestOpportunityScore(unittest.TestCase):
    def test_bounds(self):
        out=score(OpportunityInputs(90,20,30000,60,35,80,80,85,40))
        for v in out.values():
            self.assertGreaterEqual(v,0)
            self.assertLessEqual(v,100)

    def test_commercial_evidence_raises_business(self):
        no_market=score(OpportunityInputs(90,0,0,0,0,80,80,85,30))["business"]
        with_market=score(OpportunityInputs(90,10,20000,55,30,80,80,85,40))["business"]
        self.assertGreater(with_market,no_market)

    def test_cross_source_heat(self):
        one=score(OpportunityInputs(80,0,0,0,0,80,80,80,20))["heat"]
        both=score(OpportunityInputs(80,20,10000,50,25,80,80,80,40))["heat"]
        self.assertGreater(both,0)
        self.assertGreater(one,0)

if __name__=="__main__":
    unittest.main()
