"""B0 strategy freeze: tests run with existing JianShi CI unittest discovery.

Does not access Staging, Production, Cloudflare or real users.
Actual usability/customer validation remains separate and NOT_TESTED.
"""
import copy
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "b0_dual_track_strategy_20261013.json"
STRATEGY = ROOT / "docs" / "JIANSHI2_B0_DUAL_TRACK_POSITIONING_CN.md"
EXECUTION = ROOT / "docs" / "JIANSHI2_B0_90DAY_EXECUTION_CN.md"
F1 = ROOT / "docs" / "JIANSHI2_F1_PRODUCT_UI_FREEZE_20261011.md"
P35 = ROOT / "docs" / "P35_BUSINESS_MODEL_AUDIT_AND_5Y_ROADMAP.md"
INDEX = ROOT / "docs" / "F21_IMPLEMENTATION_INDEX_CN.md"
BASE = ROOT / "config" / "product_framework_v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "publish-static.yml"
RELEASE = ROOT / "scripts" / "release" / "p412_build_public.py"


def validate(c):
    problems = []
    if c.get("version") != "B0-2026-10-13":
        problems.append("wrong version")
    if c.get("status") != "STRATEGY_APPROVED_VALIDATION_PENDING":
        problems.append("false product-validated status")
    if c.get("positioning") != "面向中国个人创业者的商业机会发现与决策平台":
        problems.append("lost primary positioning")
    a = c.get("primary_business", {})
    b = c.get("secondary_business", {})
    s = c.get("shared_foundation", {})
    if a.get("id") != "opportunity_intelligence" or a.get("priority") != 1:
        problems.append("founder discovery no longer first")
    if a.get("core_entities") != ["OPPORTUNITY", "EVIDENCE", "CASE", "TOPIC", "SIGNAL"]:
        problems.append("opportunity evidence model drift")
    if a.get("real_users_confirmed") is not False:
        problems.append("invented live user validation")
    if b.get("id") != "sme_ai_adoption" or b.get("priority") != 2:
        problems.append("SME validation no longer secondary")
    if b.get("trial_mode") != "MANUAL_DIAGNOSIS_AND_SCOPED_POC":
        problems.append("SME service prematurely operational")
    if b.get("enterprise_revenue_assumed") is not False:
        problems.append("assumed enterprise revenue")
    if [a.get("ratio_target_pct"), b.get("ratio_target_pct"),
        s.get("ratio_target_pct")] != [65, 25, 10]:
        problems.append("resource proposal silently changed")
    if s.get("new_features") != "ONLY_WHEN_USER_VALUE_REQUIRES":
        problems.append("unbounded infra expansion")
    goals = c.get("stage_goals", {})
    if goals.get("all_goals_are") != "EXPERIMENT_ASSUMPTIONS_NOT_RESULTS":
        problems.append("experiments presented as results")
    if goals.get("window_days") != 90:
        problems.append("90d experiment plan missing")
    forbidden = c.get("delivery_constraints", {})
    required = ["new_live_auth", "staging_flags_change", "production_writes",
                "cloudflare_worker_deploy", "open_marketplace",
                "self_custody_payments", "unverified_supplier_publication",
                "fictional_reviews_or_cases", "private_user_data_from_static_pages",
                "third_party_listing_mirror", "p441_schedule_change"]
    if sorted(forbidden) != sorted(required) or any(forbidden.get(k) is not False for k in required):
        problems.append("one or more safety boundaries changed")
    if c.get("release_gate") != "NO_PRODUCT_DEPLOYMENT_IN_B0":
        problems.append("B0 falsely authorizes release")
    if c.get("strategy_revision_requires") != "EXPLICIT_USER_DECISION":
        problems.append("founder priority is unprotected")
    return problems


class TestB0DualTrackStrategy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.docs = {
            x.name: x.read_text(encoding="utf-8")
            for x in [STRATEGY, EXECUTION, F1, P35, INDEX]
        }

    def test_contract_frozen(self):
        self.assertEqual(validate(self.contract), [])

    def test_old_p33_founder_identity_stays_frozen(self):
        old = json.loads(BASE.read_text(encoding="utf-8"))
        self.assertEqual(old["product_category"], "商业机会发现与决策平台")
        self.assertEqual(old["primary_user"], "中国个人创业者")
        self.assertTrue(old["opportunity_is_product"])
        self.assertFalse(old["raw_source_is_product"])
        self.assertEqual(old["score_model"], "OPP_V0.2")
        self.assertFalse(old["full_listing_mirror_allowed"])

    def test_new_strategy_does_not_claim_revenue_or_real_customers(self):
        strategy = self.docs[STRATEGY.name]
        self.assertIn("没有经独立核实的真实产品市场匹配", strategy)
        self.assertIn("第二业务线", strategy)
        self.assertIn("真实付费证据验证", strategy)
        self.assertIn("唯一主定位", strategy)
        self.assertIn("不局限于 AI", strategy)

    def test_enterprise_workstream_is_staged_with_real_business_gates(self):
        execution = self.docs[EXECUTION.name]
        for term in ("B0-A01", "B0-A02", "B0-B01", "B0-B02",
                     "B0-B03", "B0-B04", "B0-C01",
                     "真实付费", "客户同意", "NOT_TESTED", "7天回访"):
            self.assertIn(term, execution)

    def test_existing_freezes_explicitly_reconcile_new_priority(self):
        f1 = self.docs[F1.name]
        p35 = self.docs[P35.name]
        idx = self.docs[INDEX.name]
        self.assertIn("2026-10-13 B0 用户确认", f1)
        self.assertIn("个人创业机会发现", f1)
        self.assertIn("B0 2026-10-13", p35)
        self.assertIn("尚无真实收入与付费试点证明", p35)
        self.assertIn("B0 双线定位冻结", idx)
        self.assertIn("JIANSHI2_B0_90DAY_EXECUTION_CN.md", idx)

    def test_static_build_freeze_and_source_gates_preserved(self):
        w = WORKFLOW.read_text(encoding="utf-8")
        release = RELEASE.read_text(encoding="utf-8")
        self.assertIn("cron: '55 0 * * *'", w)
        self.assertIn("cron: '55 6,12,18 * * *'", w)
        self.assertIn('JIANSHI_AUTH_ENABLED: "0"', w)
        self.assertIn("github.event_name == 'schedule'", w)
        self.assertNotIn("b0_dual_track_strategy", w)
        self.assertNotIn("b0_dual_track_strategy", release)
        self.assertIn("Only web/dist is a valid deploy output", release)

    def test_adversarial_mutations_are_rejected(self):
        mutate = (
            lambda c: c["primary_business"].update(priority=2),
            lambda c: c["secondary_business"].update(priority=1),
            lambda c: c["primary_business"].update(real_users_confirmed=True),
            lambda c: c["secondary_business"].update(enterprise_revenue_assumed=True),
            lambda c: c["delivery_constraints"].update(new_live_auth=True),
            lambda c: c["delivery_constraints"].update(production_writes=True),
            lambda c: c["delivery_constraints"].update(open_marketplace=True),
            lambda c: c["delivery_constraints"].update(p441_schedule_change=True),
            lambda c: c.update(release_gate="B0_DEPLOY"),
            lambda c: c["stage_goals"].update(all_goals_are="REAL_USER_RESULTS"),
        )
        for fn in mutate:
            with self.subTest(fn=str(fn)):
                x = copy.deepcopy(self.contract)
                fn(x)
                self.assertTrue(validate(x), msg="an unsafe strategy mutation was accepted")

    def test_only_internal_docs_and_contract_not_public_release(self):
        for p in (CONFIG, STRATEGY, EXECUTION):
            self.assertTrue(p.exists())
        text = self.docs[STRATEGY.name]
        self.assertIn("不能", text)
        self.assertIn("不强制注册", text)
        self.assertIn("不得通过本战略补充自动开启", self.docs[F1.name])


if __name__ == "__main__":
    unittest.main()
