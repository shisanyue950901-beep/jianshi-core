"""No unknown nested CMS evidence fields enter the static public projection."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/content"))

from f21_content_contract import (
    ContentContractError, validate_draft, transition, public_projection,
)


def record():
    return dict(
        content_id="SYNTHETIC_F21_EVIDENCE",
        content_type="SOLUTION_GUIDE",
        title="合成测试：企业需求梳理",
        summary="仅用于不接触真实客户的离线内容审核测试。",
        category="业务验证",
        tags=["TEST"],
        language="zh-CN",
        status="DRAFT",
        author_id="TEST_AUTHOR",
        revision=1,
        source_refs=[{"kind": "PUBLIC_URL", "url": "https://example.org/research"}],
        source_verified_at="2026-10-11",
        license_status="OWNED",
        rights_confirmed=True,
        facts_verified=True,
        private_notes="SYNTHETIC_ONLY",
    )


class F21NestedSourceSafety(unittest.TestCase):
    def test_only_pinned_source_keys_survive_projection(self):
        d = record()
        validate_draft(d)
        d = transition(d, "IN_REVIEW", actor_id="TEST_AUTHOR", role="AUTHOR")
        d = transition(d, "APPROVED", actor_id="TEST_REVIEWER", role="REVIEWER")
        d = transition(d, "PUBLISHED", actor_id="TEST_PUBLISHER", role="PUBLISHER",
                       timestamp="2026-10-11")
        public = public_projection(d)
        self.assertEqual(public["source_refs"], [
            {"kind": "PUBLIC_URL", "url": "https://example.org/research"}])
        self.assertNotIn("SYNTHETIC_ONLY", str(public))
        self.assertNotIn("private_notes", public)

    def test_no_nested_customer_or_credential_fields(self):
        for bad in (
            {"kind": "PUBLIC_URL", "url": "https://example.org/report", "private_note": "TEST_SECRET"},
            {"kind": "AUTHOR_ORIGINAL", "description": "原创样例", "raw_company_brief": "TEST_SECRET"},
            {"kind": "PUBLIC_URL", "url": "https://user:secret@example.org/report"},
            {"kind": "PUBLIC_URL", "url": "https://example.org/report?token=TEST_SECRET"},
            {"kind": "PUBLIC_URL", "url": "https://example.org/report#section"},
            {"kind": "PUBLIC_URL", "url": "http://example.org/report"},
            {"kind": "PUBLIC_URL", "url": "https://[broken"},
        ):
            r = record()
            r["source_refs"] = [bad]
            with self.subTest(bad=bad):
                with self.assertRaises(ContentContractError):
                    validate_draft(r)

    def test_wrong_types_raise_contract_errors(self):
        for key, value in (
            ("content_type", []), ("status", {}), ("language", []),
        ):
            r = record()
            r[key] = value
            with self.subTest(key=key):
                with self.assertRaises(ContentContractError):
                    validate_draft(r)


if __name__ == "__main__":
    unittest.main()
