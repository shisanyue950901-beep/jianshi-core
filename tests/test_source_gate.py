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
        for code in ("sideprojectors","trustmrr","catchbuys","acquirebase"):
            with self.assertRaises(SourceGateError):
                assert_auto_collect_allowed(SourcePolicy(code,"YELLOW",False,False))

    def test_marketplace_red_sources_fail_closed(self):
        for code in ("acquire","flippa","microns","deal_slide"):
            with self.assertRaises(SourceGateError):
                assert_auto_collect_allowed(SourcePolicy(code,"RED",False,False))

if __name__ == "__main__": unittest.main()
