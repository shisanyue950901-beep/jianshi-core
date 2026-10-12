"""G2-D offline state-machine regression: synthetic only, NOT a live DB E2E."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/qa"))
from f21_g2d_cms_offline_model import OfflineCms, Rejected, PUBLIC_FIELDS

EDITOR = "SYNTHETIC_EDITOR_A"
EDITOR_B = "SYNTHETIC_EDITOR_B"
REVIEWER = "SYNTHETIC_REVIEWER_A"
PUBLISHER = "SYNTHETIC_PUBLISHER_A"
KEY = "SYNTHETIC_CMS_GUIDE_A"


def rid(i: int) -> str:
    return "SYNTHETIC_REQUEST_" + str(i)


def example() -> dict:
    return {
        "title": "合成 CMS 发布练习",
        "summary": "仅供独立事务模型验证的公开摘要，未连接真实数据库。",
        "category": "人工模拟",
        "language": "zh-CN",
        "tags": ["模型", "审核"],
        "source_verified_at": "2026-10-12",
        "source_refs": [{"kind": "AUTHOR_ORIGINAL", "description": "合成示例原创文字"}],
        "private_notes": "SYNTHETIC_SECRET_MUST_NOT_LEAK",
        "internal_reviewer": "SYNTHETIC_PRIVATE_FIELD",
    }


def ready() -> OfflineCms:
    m = OfflineCms(simulated_gates_ready=True)
    for a, role in ((EDITOR, "EDITOR"), (EDITOR_B, "EDITOR"),
                    (REVIEWER, "REVIEWER"), (PUBLISHER, "PUBLISHER")):
        m.grant_synthetic(a, role)
    return m


def prepare() -> OfflineCms:
    m = ready()
    m.create(EDITOR, KEY, "SOLUTION_GUIDE", example(), ["SYNTHETIC_EVIDENCE"], rid(1))
    m.edit(EDITOR, KEY, 1, example(), ["SYNTHETIC_EVIDENCE"], True, True, rid(2))
    return m


def expect_block(test: unittest.TestCase, m: OfflineCms, code: str, fun):
    before = deepcopy(m.items)
    with test.assertRaises(Rejected) as caught:
        fun()
    test.assertEqual(caught.exception.code, code)
    test.assertEqual(m.items, before, "Rejected operation must not mutate any row")


class CmsOfflineContract(unittest.TestCase):
    def test_closed_by_default_and_no_public_side_effects(self):
        m = OfflineCms()
        m.grant_synthetic(EDITOR, "EDITOR")
        expect_block(self, m, "CMS_WRITE_DISABLED",
                     lambda: m.create(EDITOR, KEY, "SOLUTION_GUIDE",
                                      example(), ["SYNTHETIC_EVIDENCE"], rid(1)))
        self.assertEqual(m.items, {})

    def test_valid_lifecycle_and_private_projection_redaction(self):
        m = prepare()
        self.assertEqual(m.transition(EDITOR, KEY, 2, "IN_REVIEW", rid(3)), 3)
        self.assertEqual(m.transition(REVIEWER, KEY, 3, "APPROVED", rid(4)), 4)
        self.assertEqual(m.transition(PUBLISHER, KEY, 4, "PUBLISHED", rid(5)), 5)
        item = m.items[KEY]
        self.assertEqual(item.state, "PUBLISHED")
        self.assertEqual(len(item.snapshots), 1)
        snap = item.snapshots[0]
        self.assertEqual(snap["lifecycle"], "STAGED")
        self.assertEqual(set(snap["public"]), PUBLIC_FIELDS)
        self.assertNotIn("private_notes", snap["public"])
        self.assertNotIn("SYNTHETIC_SECRET_MUST_NOT_LEAK", repr(snap["public"]))
        self.assertEqual(snap["public"]["revision"], 5)
        self.assertEqual(m.transition(PUBLISHER, KEY, 5, "UNPUBLISHED", rid(6)), 6)
        self.assertEqual(m.items[KEY].snapshots[0]["lifecycle"], "RETRACTED")
        self.assertEqual(m.transition(EDITOR, KEY, 6, "IN_REVIEW", rid(7)), 7)
        self.assertEqual(m.transition(REVIEWER, KEY, 7, "APPROVED", rid(8)), 8)
        self.assertEqual(m.transition(PUBLISHER, KEY, 8, "PUBLISHED", rid(9)), 9)
        self.assertEqual(
            [s["lifecycle"] for s in m.items[KEY].snapshots],
            ["RETRACTED", "STAGED"])
        self.assertEqual(len(m.items[KEY].events), 9)
        self.assertEqual(len(m.items[KEY].versions), 9)
        self.assertEqual(m.items[KEY].last_reviewer, REVIEWER)

    def test_rejection_and_resubmission(self):
        m = prepare()
        m.transition(EDITOR, KEY, 2, "IN_REVIEW", rid(3))
        self.assertEqual(m.transition(REVIEWER, KEY, 3, "REJECTED", rid(4)), 4)
        self.assertEqual(m.transition(EDITOR, KEY, 4, "DRAFT", rid(5)), 5)
        self.assertEqual(m.edit(EDITOR, KEY, 5, example(), ["SYNTHETIC_EVIDENCE"],
                                True, True, rid(6)), 6)
        self.assertEqual(m.items[KEY].events[-2][0], "RESTORE")
        self.assertEqual(m.items[KEY].snapshots, [])

    def test_cross_user_owner_author_reviewer_publisher_guards(self):
        m = prepare()
        expect_block(self, m, "CMS_OWNER_DENIED",
                     lambda: m.edit(EDITOR_B, KEY, 2, example(), [], True, True, rid(3)))
        expect_block(self, m, "CMS_OWNER_DENIED",
                     lambda: m.transition(EDITOR_B, KEY, 2, "IN_REVIEW", rid(3)))
        m.transition(EDITOR, KEY, 2, "IN_REVIEW", rid(3))
        expect_block(self, m, "CMS_INDEPENDENT_REVIEW_REQUIRED",
                     lambda: m.transition(EDITOR, KEY, 3, "APPROVED", rid(4)))
        # The real owner cannot also be an independent reviewer even with ADMIN.
        m.roles[EDITOR] = "ADMIN"
        expect_block(self, m, "CMS_INDEPENDENT_REVIEW_REQUIRED",
                     lambda: m.transition(EDITOR, KEY, 3, "APPROVED", rid(4)))
        m.transition(REVIEWER, KEY, 3, "APPROVED", rid(4))
        expect_block(self, m, "CMS_PUBLISHER_DENIED",
                     lambda: m.transition(EDITOR, KEY, 4, "PUBLISHED", rid(5)))

    def test_stale_duplicate_and_illegal_edges_are_atomic(self):
        m = prepare()
        expect_block(self, m, "CMS_STALE_REVISION",
                     lambda: m.transition(EDITOR, KEY, 1, "IN_REVIEW", rid(3)))
        expect_block(self, m, "CMS_DUPLICATE_REQUEST",
                     lambda: m.transition(EDITOR, KEY, 2, "IN_REVIEW", rid(2)))
        expect_block(self, m, "CMS_ILLEGAL_TRANSITION",
                     lambda: m.transition(PUBLISHER, KEY, 2, "PUBLISHED", rid(3)))
        # A failed transition leaves all persisted rows untouched.
        m.transition(EDITOR, KEY, 2, "IN_REVIEW", rid(3))
        expect_block(self, m, "CMS_DRAFT_LOCKED",
                     lambda: m.edit(EDITOR, KEY, 3, example(), [], True, True, rid(4)))

    def test_missing_evidence_media_rights_cannot_approve(self):
        m = ready()
        m.create(EDITOR, KEY, "SOLUTION_GUIDE", example(), [], rid(1))
        m.transition(EDITOR, KEY, 1, "IN_REVIEW", rid(2))
        expect_block(self, m, "CMS_EVIDENCE_OR_RIGHTS_MISSING",
                     lambda: m.transition(REVIEWER, KEY, 2, "APPROVED", rid(3)))
        m = prepare()
        m.transition(EDITOR, KEY, 2, "IN_REVIEW", rid(3))
        expect_block(self, m, "CMS_MEDIA_RIGHTS_NOT_READY",
                     lambda: m.transition(REVIEWER, KEY, 3, "APPROVED",
                                          rid(4), media_ready=False))

    def test_source_allowlist_rejects_credential_or_query_urls(self):
        for i,source in enumerate([
            {"kind": "PUBLIC_URL", "url": "http://example.test/page"},
            {"kind": "PUBLIC_URL", "url": "https://user@host.test/path"},
            {"kind": "PUBLIC_URL", "url": "https://host.test/page?token=synthetic"},
            {"kind": "PUBLIC_URL", "url": "https://host.test/path#section"},
            {"kind": "PUBLIC_URL", "url": "https://host.test/page", "private": True},
            {"kind": "UNAPPROVED_PRIVATE_ARTIFACT", "file": "example.json"},
        ]):
            with self.subTest(source=i):
                m = ready()
                p = example()
                p["source_refs"] = [source]
                m.create(EDITOR, KEY, "SOLUTION_GUIDE", p, ["SYNTHETIC_EVIDENCE"], rid(1))
                m.edit(EDITOR, KEY, 1, p, ["SYNTHETIC_EVIDENCE"], True, True, rid(2))
                m.transition(EDITOR, KEY, 2, "IN_REVIEW", rid(3))
                m.transition(REVIEWER, KEY, 3, "APPROVED", rid(4))
                expect_block(self, m, "CMS_SOURCE_UNSAFE",
                             lambda: m.transition(PUBLISHER, KEY, 4, "PUBLISHED", rid(5)))

    def test_rollback_of_old_body_is_not_a_supported_transition(self):
        m = prepare()
        expect_block(self, m, "CMS_VERSION_ROLLBACK_NOT_IMPLEMENTED",
                     lambda: m.restore_old_revision(KEY, 1))
        # Do not label RETRACT+RESUBMIT as historical content rollback.

    def test_current_sql_contract_parity_checks_are_static_not_live_db(self):
        sql=(ROOT/"db/migrations/0055_jianshi_cms_transaction_gate.sql").read_text()
        api=(ROOT/"db/migrations/0056_jianshi_cms_session_guard.sql").read_text()
        for expected in ("CMS_WRITE_DISABLED","CMS_STALE_REVISION",
                         "CMS_INDEPENDENT_REVIEW_REQUIRED","CMS_PUBLISHER_DENIED",
                         "CMS_EVIDENCE_OR_RIGHTS_MISSING","CMS_MEDIA_RIGHTS_NOT_READY",
                         "CMS_SOURCE_UNSAFE","CMS_INVALID_PUBLIC_PROJECTION",
                         "'PUBLISHED'","'UNPUBLISHED'","'RETRACTED'",
                         "publication_snapshots"):
            self.assertIn(expected,sql)
        self.assertIn("for update",sql.lower())
        for op in ("CREATE", "EDIT", "STATE"):
            self.assertIn("p_operation='"+op+"'",api)
        self.assertIn("REVOKE",api.upper())
        self.assertNotIn("grant execute on function public.cms_internal_write_v01"
                         "(uuid,text,jsonb) to authenticated",api.lower())

if __name__ == "__main__":
    unittest.main()
