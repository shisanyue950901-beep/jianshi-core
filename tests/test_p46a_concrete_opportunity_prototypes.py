import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/"content"/"p46a_concrete_opportunity_prototypes.json"
BUILD=ROOT/"web"/"build.py"


class TestP46AConcreteOpportunityPrototypes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(CONTENT.read_text(encoding="utf-8"))
        cls.build=BUILD.read_text(encoding="utf-8")

    def test_exactly_two_first_prototypes(self):
        items=self.data["opportunities"]
        self.assertEqual(len(items),2)
        self.assertEqual(
            {x["slug"] for x in items},
            {"vertical-industry-saas","amazon-fba-niche-brand"},
        )
        self.assertTrue(all(x["status"]=="值得研究" for x in items))

    def test_chinese_and_global_channels_are_both_considered(self):
        raw=CONTENT.read_text(encoding="utf-8")
        for token in ["抖音","小红书","B站","公众号","YouTube","TikTok","SEO"]:
            self.assertIn(token,raw)

    def test_evidence_and_editorial_judgement_stay_separate(self):
        for item in self.data["opportunities"]:
            self.assertEqual(item["evidence"]["commercial_source_diversity"],1)
            self.assertTrue(item["evidence"]["caveat"])
            self.assertTrue(item["editorial_judgement"])
            self.assertTrue(item["unknowns"])

    def test_prototypes_are_noindex_and_not_added_to_search_index(self):
        self.assertIn('robots="noindex,nofollow"',self.build)
        self.assertIn("prototype_count",self.build)
        self.assertNotIn('search.append({"slug":prototype_slug',self.build)

    def test_fixture_build_renders_both_prototypes(self):
        env=dict(os.environ)
        env.pop("JIANSHI_API_URL",None)
        subprocess.run([sys.executable,str(BUILD)],cwd=ROOT,env=env,check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        for slug in ["vertical-industry-saas","amazon-fba-niche-brand"]:
            page=(ROOT/"web"/"dist"/"opportunity"/slug/"index.html")
            self.assertTrue(page.exists(),slug)
            html=page.read_text(encoding="utf-8")
            self.assertIn("04 · 中国创业者视角",html)
            self.assertIn("05 · 渠道矩阵",html)
            self.assertIn("noindex,nofollow",html)
        saas=(ROOT/"web"/"dist"/"opportunity"/"vertical-industry-saas"/"index.html").read_text(encoding="utf-8")
        fba=(ROOT/"web"/"dist"/"opportunity"/"amazon-fba-niche-brand"/"index.html").read_text(encoding="utf-8")
        self.assertIn("抖音",saas)
        self.assertIn("YouTube",saas)
        self.assertIn("TikTok",fba)
        self.assertIn("Amazon 站内",fba)


if __name__=="__main__":
    unittest.main()
