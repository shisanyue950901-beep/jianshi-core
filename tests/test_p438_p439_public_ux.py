"""P4.38/P4.39: source-governed UX numbers, task-first public hero, legacy motion."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
import p438_public_ux_contract as ux
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases, public_home


class ProductFirstUXTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=eligible_cases(parse_cases())
        cls.proto=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
        cls.home=public_home(cls.proto,cls.cases)

    def test_metrics_require_original_evidence_and_standalone_launch_gate(self):
        result=ux.public_metrics(self.cases)
        self.assertEqual(result,{"approved_cases":3,"verified_launch":0,
                                 "business_models":6,
                                 "case_ids":["carrd","nerdwallet","plausible"]})
        self.assertEqual(len(ux.entry_contract()["metrics"]),3)

    def test_unreviewed_or_duplicated_cases_cannot_be_counted(self):
        with self.assertRaises(RuntimeError):
            ux.public_metrics(self.cases + [dict(self.cases[0],id="unreviewed",evidence_level=1)])
        with self.assertRaises(RuntimeError):
            ux.public_metrics(self.cases + [dict(self.cases[0])])
        with self.assertRaises(RuntimeError):
            ux.public_metrics(self.cases[:2])

    def test_explicit_original_period_and_url_must_survive(self):
        original=ux.load
        def substituted(path):
            data=copy.deepcopy(original(path))
            if path==ux.EVIDENCE:
                case=next(x for x in data["additional_evidence"] if x["id"]=="carrd")
                case["period"]=""
            return data
        with patch.object(ux,"load",side_effect=substituted):
            with self.assertRaisesRegex(RuntimeError,"attribution"):
                ux.public_metrics(self.cases)

    def test_historical_mrr_never_upgrades_to_proven_launch(self):
        original=ux.load
        def substituted(path):
            data=copy.deepcopy(original(path))
            if path==ux.SOLO:
                data["case_assessments"][0]["ready_for_launch"]=True
            return data
        with patch.object(ux,"load",side_effect=substituted):
            with self.assertRaisesRegex(RuntimeError,"cannot be promoted"):
                ux.public_metrics(self.cases)

    def test_public_hero_two_actions_three_source_bounded_stats(self):
        html=self.home
        self.assertLess(html.index('id="recommendations"'),html.index('class="hero"'))
        self.assertIn('id="rec-title">找到值得你验证的生意。',html)
        self.assertIn('href="#pick-list">查看推荐项目',html)
        self.assertIn('href="#quick-start">根据我的条件筛选',html)
        self.assertEqual(html.count('class="rec-stat"'),3)
        self.assertIn('<strong>3</strong><span>有历史经营证据的案例</span>',html)
        self.assertIn('<strong>0</strong><span>已验证可直接启动的项目</span>',html)
        self.assertIn('<strong>6</strong><span>已整理的商业模式</span>',html)
        self.assertNotIn("每5分钟",html)
        self.assertNotIn("18991",html)
        self.assertIn('id="case-carrd"',html)

    def test_three_navigation_paths_and_real_task_destinations(self):
        html=self.home
        head=html[html.index('<nav aria-label="主要导航">'):html.index("</nav>",html.index('<nav aria-label="主要导航">'))]
        self.assertEqual(head.count("<a "),3)
        self.assertIn('<a href="#recommendations">发现项目</a>',head)
        self.assertIn('<a href="#models">商业模式</a>',head)
        self.assertIn('<a href="#about">方法说明</a>',head)
        self.assertIn('href="#case-carrd"',html)
        self.assertIn('href="/projects/"',html)
        self.assertIn('href="#models"',html)
        self.assertIn('id="pick-list"',html)
        self.assertEqual(html.count('<article id="case-'),3)

    def test_legacy_3d_theme_accessibility_and_no_private_leads(self):
        html=self.home
        for marker in ('id="ring"','id="lb"','id="grid"',
                       'id="skipSplash"','id="themeToggle"',
                       'prefers-reduced-motion','data:image/webp;base64,'):
            self.assertIn(marker,html)
        self.assertEqual(html.count("data:image/webp;base64,"),8)
        self.assertEqual(html.count("<style>"),1)
        self.assertEqual(html.count("<script>"),1)
        self.assertIn("@media(max-width:450px)",html)
        self.assertIn("rec-quick__list",html)
        for forbidden in ("Easlo｜","Louise Lennox","Tally｜","listing_number","OFFICIAL_API"):
            self.assertNotIn(forbidden,html)

    def test_public_metrics_never_use_private_source_inventory(self):
        source=(ROOT/"scripts/release/p438_public_ux_contract.py").read_text(encoding="utf-8")
        for forbidden in ("p432_source_access_matrix","p426_research_leads",
                          "github_metrics","artifacts?","TinyFish","supabase.co"):
            self.assertNotIn(forbidden,source)


if __name__=="__main__":
    unittest.main()
