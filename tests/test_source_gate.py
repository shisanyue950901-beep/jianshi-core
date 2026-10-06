import sys, unittest
sys.path.insert(0, "src")
from jianshi.source_gate import SourcePolicy, SourceGateError, assert_auto_collect_allowed

class TestGate(unittest.TestCase):
    def test_green_allowed(self):
        assert_auto_collect_allowed(SourcePolicy("empire_flippers","GREEN",True,True))
    def test_red_fails_closed(self):
        with self.assertRaises(SourceGateError):
            assert_auto_collect_allowed(SourcePolicy("acquire","RED",False,False))
    def test_yellow_fails_closed(self):
        with self.assertRaises(SourceGateError):
            assert_auto_collect_allowed(SourcePolicy("sideprojectors","YELLOW",False,False))

if __name__ == "__main__": unittest.main()
