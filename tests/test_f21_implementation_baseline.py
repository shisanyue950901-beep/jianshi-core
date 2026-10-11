"""F2.1 first runnable G0/G1 contract: design tokens and fail-closed CMS."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/release"))
sys.path.insert(0, str(ROOT / "scripts/content"))

from f21_design_tokens import TOKENS, render_css
from f21_content_contract import (
    ContentContractError, PUBLIC_KEYS, validate_draft,
    transition, public_projection,
)
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases
from p445_unified_home import build_home
from p446_content_hubs import render_pages
from p448_v2_local_drafts import render_one


class F21CMSAndDesign(unittest.TestCase):
    @staticmethod
    def draft():
        return {
            "content_id": "SYNTHETIC_F21_SOLUTION_01",
            "content_type": "SOLUTION_GUIDE",
            "title": "合成数据：企业自动化方案",
            "summary": "本内容仅供测试环境验证审核合同，不构成真实客户案例。",
            "category": "企业数字化",
            "tags": ["自动化", "Agent"],
            "language": "zh-CN",
            "status": "DRAFT",
            "author_id": "TEST_AUTHOR_A",
            "revision": 1,
            "source_refs": [
                {"kind": "AUTHOR_ORIGINAL", "description": "Synthetic source; no real customer"}
            ],
            "source_verified_at": "2026-10-11",
            "license_status": "OWNED",
            "rights_confirmed": True,
            "facts_verified": True,
            "private_notes": "TEST_ONLY_CLIENT_SECRET_DO_NOT_EXPOSE",
            "contact_email": "not-a-real-contact",
        }

    def test_cms_full_editorial_review_and_public_allowlist(self):
        d = self.draft()
        validate_draft(d)
        reviewing = transition(d, "IN_REVIEW", actor_id="TEST_AUTHOR_A", role="AUTHOR")
        approved = transition(reviewing, "APPROVED", actor_id="TEST_REVIEWER_B", role="REVIEWER")
        published = transition(approved, "PUBLISHED", actor_id="TEST_PUBLISHER_C",
                               role="PUBLISHER", timestamp="2026-10-11")
        public = public_projection(published)
        self.assertTrue(set(public).issubset(PUBLIC_KEYS))
        self.assertEqual(public["status"] if "status" in public else published["status"], "PUBLISHED")
        self.assertIn("title", public)
        self.assertIn("published_at", public)
        self.assertNotIn("private_notes", public)
        self.assertNotIn("contact_email", public)
        self.assertNotIn("author_id", public)
        self.assertNotIn("reviewer_id", public)
        self.assertNotIn("TEST_ONLY_CLIENT_SECRET_DO_NOT_EXPOSE", str(public))
        self.assertEqual(d["revision"], 1)
        self.assertEqual(published["revision"], 4)

    def test_cms_rejects_illegal_transitions_and_self_approval(self):
        d = self.draft()
        with self.assertRaises(ContentContractError):
            transition(d, "PUBLISHED", actor_id="TEST_AUTHOR_A", role="AUTHOR")
        with self.assertRaises(ContentContractError):
            public_projection(d)
        reviewing = transition(d, "IN_REVIEW", actor_id="TEST_AUTHOR_A", role="AUTHOR")
        with self.assertRaises(ContentContractError):
            transition(reviewing, "APPROVED", actor_id="TEST_AUTHOR_A", role="REVIEWER")
        with self.assertRaises(ContentContractError):
            transition(reviewing, "APPROVED", actor_id="TEST_RANDOM", role="AUTHOR")
        approved = transition(reviewing, "APPROVED", actor_id="TEST_REVIEWER_B", role="REVIEWER")
        with self.assertRaises(ContentContractError):
            transition(approved, "PUBLISHED", actor_id="TEST_AUTHOR_A", role="AUTHOR",
                       timestamp="2026-10-11")
        with self.assertRaises(ContentContractError):
            transition(approved, "PUBLISHED", actor_id="TEST_PUBLISHER_C", role="PUBLISHER",
                       timestamp="2026-99-99")

    def test_cms_blocks_false_rights_sources_and_malformed_data(self):
        for field, bad in [
            ("license_status", "UNKNOWN"),
            ("rights_confirmed", False),
            ("facts_verified", False),
            ("source_refs", []),
        ]:
            d = self.draft()
            d[field] = bad
            reviewing = transition(d, "IN_REVIEW", actor_id="TEST_AUTHOR_A", role="AUTHOR")
            with self.subTest(field=field):
                with self.assertRaises(ContentContractError):
                    transition(reviewing, "APPROVED", actor_id="TEST_REVIEWER_B", role="REVIEWER")
        for field, bad in [
            ("title", "x" * 141),
            ("source_verified_at", "today"),
            ("revision", 0),
            ("tags", ["x"] * 13),
            ("language", "unsupported"),
        ]:
            d = self.draft()
            d[field] = bad
            with self.subTest(field=field):
                with self.assertRaises(ContentContractError):
                    validate_draft(d)
        d = self.draft()
        d["source_refs"] = [{"kind": "PUBLIC_URL", "url": "http://unsafe.example/private"}]
        with self.assertRaises(ContentContractError):
            validate_draft(d)

    def test_design_tokens_are_one_semantic_source_in_all_g1_layouts(self):
        self.assertEqual(len(TOKENS), 11)
        style = render_css()
        for name, val in TOKENS.items():
            self.assertIn("--js21-" + name + ":" + val, style)
        self.assertIn("prefers-reduced-motion:reduce", style)
        self.assertNotIn("<script", style)
        self.assertNotIn("url(", style)
        pages = [
            build_home(eligible_cases(parse_cases())),
            render_pages()["solutions/"],
            render_pages()["academy/"],
            render_one("marketplace/brief/"),
            render_one("talent/portfolio/"),
        ]
        for html in pages:
            self.assertEqual(html.count("/* F2.1 common brand semantics"), 1)
            self.assertEqual(html.count("<style>"), 1)
            self.assertEqual(html.count("</style>"), 1)
            self.assertIn("--js21-text-muted:", html)
            self.assertIn("prefers-reduced-motion:reduce", html)
        self.assertNotIn('id="ring"', pages[0])
        self.assertEqual(pages[0].count('data:image/webp;base64,'), 1)

    def test_six_documented_frozen_contracts_and_uncorrupted_collectors(self):
        docs = [
            "F21_00_PRODUCT_PAGES_AND_G0_AUDIT_CN.md",
            "F21_01_UI_DESIGN_SYSTEM_MOTION_CN.md",
            "F21_02_BUSINESS_WORKFLOW_RBAC_CN.md",
            "F21_03_DATA_API_CMS_CONTRACT_CN.md",
            "F21_04_CONTENT_FACTORY_QUALITY_CN.md",
            "F21_05_QA_RELEASE_ACCEPTANCE_CN.md",
        ]
        for doc in docs:
            self.assertGreater(len((ROOT / "docs" / doc).read_text(encoding="utf-8")), 1100)
        wf = (ROOT / ".github/workflows/publish-static.yml").read_text()
        self.assertEqual(wf.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"), 1)
        self.assertEqual(wf.count('p426_daily_leads.py --network --max-companies 6'), 1)
        self.assertEqual(wf.count('p437_official_github_repo_probe.py --online'), 1)
        db = (ROOT / "db/migrations/0053_jianshi2_private_matching_foundation.sql").read_text()
        self.assertEqual(db.count("force row level security;"), 6)
        self.assertIn("'v2_matchmaking',false", db)
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY",
                      (ROOT / "db/migrations/0037_auth_launch_gate.sql").read_text())


if __name__ == "__main__":
    unittest.main()
