"""P4.40: source-grounded decision dossier must never certify revenue replication."""
import copy
import re
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from p423_build_project_proofs import parse_cases,project_page,index_page,build
from p425_public_admission import eligible_cases
from p440_decision_report import decision_data,render_decision_panel,render_decision_listing
from p427_recommendation_first import load_solo_profile


class DecisionReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={x["id"]:x for x in eligible_cases(parse_cases())}
        cls.policy=load_solo_profile()

    def test_exact_three_admitted_research_profiles(self):
        self.assertEqual(set(self.cases),{"carrd","plausible","nerdwallet"})
        expected={"carrd":"TEST_IDEA_ONLY",
                  "plausible":"SKILL_GATED","nerdwallet":"NOT_SOLO_STARTUP"}
        for slug,case in self.cases.items():
            item=decision_data(case)
            self.assertEqual(item["fit_status"],expected[slug])
            self.assertFalse(item["startup_ready"])
            self.assertEqual(item["test_direction"],self.policy["cases"][slug]["prototype"])
            self.assertEqual(item["first_step"],self.policy["cases"][slug]["first_step"])
            self.assertEqual(item["blocking_evidence"],self.policy["cases"][slug]["blocker"])
            self.assertEqual(item["skills"],self.policy["cases"][slug]["skills"])
            self.assertEqual(item["capital_uncertainty"],self.policy["cases"][slug]["capital_logic"])

    def test_original_evidence_period_level_and_no_new_claims(self):
        for slug,case in self.cases.items():
            record=decision_data(case)
            original=case["research_evidence"]
            self.assertEqual(record["original_source_url"],original["source_url"])
            self.assertEqual(record["historical_period"],original["period"])
            self.assertEqual(record["financial_audit_status"],original["financial_status"])
            self.assertIn(record["historical_evidence"],original["claim"])
            if slug=="nerdwallet":
                self.assertIn("L4",record["historical_category"])
                self.assertIn("2025",record["historical_period"])
                self.assertIn("公司合并",record["historical_limit"])
            else:
                self.assertIn("L3",record["historical_category"])
                self.assertIn("未经独立审计",record["historical_category"])

    def test_l1_l2_or_unreviewed_candidate_refused(self):
        fake=copy.deepcopy(self.cases["carrd"])
        fake["id"]="easlo"
        with self.assertRaises(RuntimeError):
            decision_data(fake)
        for level in (1,2):
            fake=copy.deepcopy(self.cases["carrd"])
            fake["evidence_level"]=level
            with self.assertRaises(RuntimeError):
                decision_data(fake)
        fake=copy.deepcopy(self.cases["plausible"])
        fake["research_evidence"]["tier"]="platform_attribution"
        with self.assertRaises(RuntimeError):
            decision_data(fake)

    def test_missing_period_source_or_next_validation_denied(self):
        for key,value in (("period",""),
                          ("source_url","http://not-allowed.example"),
                          ("next_research","")):
            changed=copy.deepcopy(self.cases["carrd"])
            changed["research_evidence"][key]=value
            with self.assertRaises((RuntimeError,ValueError),msg=key):
                decision_data(changed)

    def test_unproven_launch_promotion_denied(self):
        policy=copy.deepcopy(self.policy)
        policy["cases"]["carrd"]["ready_for_launch"]=True
        with self.assertRaisesRegex(RuntimeError,"does not qualify"):
            decision_data(self.cases["carrd"],profile=policy)

    def test_missing_skills_or_capital_is_fail_closed(self):
        for field in ("skills","capital_logic","blocker","first_step"):
            policy=copy.deepcopy(self.policy)
            policy["cases"]["carrd"][field]=""
            with self.assertRaisesRegex(RuntimeError,"field missing"):
                decision_data(self.cases["carrd"],profile=policy)

    def test_render_is_static_accessible_and_all_fields_escaped(self):
        d=decision_data(self.cases["carrd"])
        d["skills"]='<script>alert("x")</script>'
        html=render_decision_panel(d)
        self.assertNotIn('<script>alert',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('aria-labelledby="decision-title"',html)
        self.assertIn('id="validation-plan"',html)
        self.assertIn('referrerpolicy="no-referrer"',html)
        self.assertIn('rel="noopener noreferrer"',html)
        self.assertIn('data-solo-fit="TEST_IDEA_ONLY"',html)
        self.assertEqual(html.count("<li>"),3)
        self.assertIn("已验证可直接投入创业：0",html)
        self.assertIn("具体预算、获客成本和可复制性未经独立验证",html)
        self.assertNotIn("保证盈利",html)

    def test_all_three_pages_have_decision_card_and_existing_evidence_sections(self):
        for slug,case in self.cases.items():
            html=project_page(case)
            self.assertEqual(html.count('id="decision-report"'),1)
            self.assertLess(html.index('id="decision-report"'),html.index('aria-label="证据提炼摘要"'))
            self.assertIn("30 秒看懂这门生意",html)
            self.assertIn("01｜这个项目卖什么",html)
            self.assertIn("05｜下一步研究",html)
            self.assertIn("打开原始经营来源",html)
            self.assertIn("查看可归属的原始经营证据",html)
            self.assertIn("返回 3 个已审项目档案",html)
            self.assertIn("可能发生哪些成本",html)
            self.assertIn("需要什么能力",html)
            self.assertIn("继续投入前缺少的证据",html)
            self.assertNotIn("返回 20 个具名项目档案",html)
            self.assertNotIn("listing_number",html)
            self.assertNotIn("Empire Flippers",html)

    def test_project_list_only_shows_three_decision_briefs(self):
        html=index_page(list(self.cases.values()))
        self.assertEqual(html.count('class="decision-mini"'),3)
        self.assertEqual(len(re.findall(r'href="/projects/[a-z0-9-]+/"',html)),3)
        self.assertIn("一人起步判断：",html)
        self.assertIn("待补验证：",html)
        for slug in self.cases:
            self.assertIn('/projects/'+slug+'/',html)
        self.assertNotIn("Easlo｜",html)
        self.assertNotIn("Tally｜",html)

    def test_actual_build_preserves_existing_three_public_dossiers_only(self):
        report=build()
        self.assertEqual((report["cases"],report["public_pages"],report["held_for_research"]),
                         (3,4,17))
        paths=ROOT/"web/dist/projects"
        self.assertEqual({p.name for p in paths.iterdir() if p.is_dir()},
                         {"carrd","plausible","nerdwallet"})
        for slug in self.cases:
            html=(paths/slug/"index.html").read_text(encoding="utf-8")
            self.assertIn('id="decision-report"',html)
            self.assertIn("证据的历史经营",html.replace("原企业的历史经营证据","证据的历史经营"))
            self.assertNotIn("source_ref_ids",html)
            self.assertIn("id=\"themeToggle\"",html)
            self.assertIn("@media(max-width:720px)",html)

    def test_no_external_actions_or_additional_billed_collectors(self):
        source=(ROOT/"scripts/release/p440_decision_report.py").read_text(encoding="utf-8")
        for bad in ("urlopen","requests.get","supabase.co","TinyFish","github.com/api",
                    "analytics.js","fetch("):
            self.assertNotIn(bad,source)
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"),1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"),1)
        self.assertEqual(wf.count("- cron:"),2)
        self.assertIn("github.event_name == 'schedule' && (github.event.schedule == '55 0 * * *'",wf)
        self.assertIn("steps.daily_scan_claim_upload.outcome == 'success'",wf)
        self.assertIn("research-scan-claim-",wf)


if __name__=="__main__":
    unittest.main()
