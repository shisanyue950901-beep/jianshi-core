"""P4.28: Default to one-person, low-capital, starting from zero."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases, public_home
import p427_recommendation_first as policy

class TestP428SoloLowCapital(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=eligible_cases(parse_cases())
        cls.src=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")

    def test_default_solo_low_capital_no_inventory_and_no_made_up_budget(self):
        p=policy.load_solo_profile()
        self.assertEqual(p["audience"]["team_size"],1)
        self.assertEqual(p["audience"]["starting_stage"],"从零启动")
        self.assertIn("未指定人民币上限",p["audience"]["capital_profile"])
        self.assertIn("无需囤货",p["audience"]["preferred_model"])
        statuses={key:value["status"] for key,value in p["cases"].items()}
        self.assertEqual(statuses,{"carrd":"TEST_IDEA_ONLY","plausible":"SKILL_GATED",
                                   "nerdwallet":"NOT_SOLO_STARTUP"})
        self.assertTrue(all(not x["ready_for_launch"] for x in p["cases"].values()))
        self.assertEqual(sum(x["status"]=="TEST_IDEA_ONLY" for x in p["cases"].values()),1)

    def test_starts_with_low_capital_validation_not_technically_hard_saas(self):
        page=public_home(self.src,self.cases)
        self.assertIn("一个人 · 小资金 · 从零启动",page)
        self.assertIn("不假定会编程",page)
        self.assertIn("资金预算仍待确认",page)
        self.assertIn("无库存优先",page)
        self.assertIn("可以先用现成建站工具",page.replace("可先用现成建站工具","可以先用现成建站工具"))
        self.assertIn('data-solo-fit="TEST_IDEA_ONLY"',page)
        self.assertIn('data-solo-fit="SKILL_GATED"',page)
        self.assertIn('data-solo-fit="NOT_SOLO_STARTUP"',page)
        self.assertLess(page.index('data-case="carrd"'),page.index('data-case="plausible"'))
        self.assertLess(page.index('data-case="plausible"'),page.index('data-case="nerdwallet"'))
        self.assertIn("可先小成本测试的方向（未证实盈利）",page)
        self.assertIn("试单",page)
        self.assertIn("工具订阅、域名、时间成本及获客费用尚未核实",page)
        self.assertIn("已证明适合直接投入创业的项目",page)
        self.assertIn("<strong>0</strong>",page)
        self.assertNotIn("低于 1000",page)
        self.assertNotIn("保证盈利",page)
        self.assertLess(len(page.encode("utf-8"))+124,260000)

    def test_no_evidence_downgrade_and_no_unproven_recommendation(self):
        page=public_home(self.src,self.cases)
        self.assertEqual(page.count('<article class="rec-card'),3)
        self.assertIn("来自 Carrd",page.replace("启发自 Carrd","来自 Carrd"))
        self.assertIn("不等同于 Carrd 的 SaaS 收入模式",page)
        self.assertIn("未经独立财务审计",page)
        self.assertIn("监管历史财务",page)
        self.assertIn("L3 · 历史经营自述",page)
        self.assertIn("缺少",page)
        self.assertNotIn("Easlo｜",page)
        self.assertEqual(page.count("data:image/webp;base64,"),8)

    def test_policy_fails_closed_if_unproven_project_is_marked_launch_ready(self):
        cfg=json.loads(policy.PROFILE_FILE.read_text(encoding="utf-8"))
        cfg["case_assessments"][0]["ready_for_launch"]=True
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"profile.json"
            path.write_text(json.dumps(cfg,ensure_ascii=False),encoding="utf-8")
            with patch.object(policy,"PROFILE_FILE",path),self.assertRaisesRegex(RuntimeError,"不能宣称"):
                policy.load_solo_profile()

    def test_policy_fails_closed_without_target_founder_or_with_invalid_status(self):
        cfg=json.loads(policy.PROFILE_FILE.read_text(encoding="utf-8"))
        cfg["default_audience"]["team_size"]=3
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"profile.json"
            path.write_text(json.dumps(cfg,ensure_ascii=False),encoding="utf-8")
            with patch.object(policy,"PROFILE_FILE",path),self.assertRaises(RuntimeError):
                policy.load_solo_profile()
        cfg["default_audience"]["team_size"]=1
        cfg["case_assessments"][0]["status"]="GUARANTEED_INCOME"
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"profile.json"
            path.write_text(json.dumps(cfg,ensure_ascii=False),encoding="utf-8")
            with patch.object(policy,"PROFILE_FILE",path),self.assertRaises(RuntimeError):
                policy.load_solo_profile()

if __name__=="__main__":
    unittest.main()
