"""F2.1 G1-C private CMS schema, offline prototype and regression contracts.

This test does not connect to Supabase and must not create any production data.
"""
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/content"))
from f21_content_contract import ContentContractError, transition
from f21_review_workbench import InMemoryReviewWorkbench

MIGRATION = ROOT / "db/migrations/0054_jianshi_cms_private_foundation.sql"
PREVIEW = ROOT / "web/prototypes/f21c/index.html"
TABLES = (
    "content_items", "content_revisions", "media_rights",
    "review_events", "publication_snapshots",
)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.buttons = []
        self.forms = []
        self.scripts = []
        self.attrs = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "button":
            self.buttons.append(d)
        if tag == "form":
            self.forms.append(d)
        if tag == "script":
            self.scripts.append(d)
        self.attrs.append((tag,d))


class F21G1CFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8")
        cls.ui = PREVIEW.read_text(encoding="utf-8")

    def test_private_schema_all_five_tables_force_rls_and_deny_anon(self):
        sql = self.sql
        self.assertIn("create schema if not exists jianshi_cms;", sql)
        self.assertEqual(len(TABLES), 5)
        self.assertEqual(sql.count("create table if not exists jianshi_cms."), 5)
        for name in TABLES:
            with self.subTest(table=name):
                self.assertIn("create table if not exists jianshi_cms."+name, sql)
                self.assertIn("alter table jianshi_cms."+name+" enable row level security;", sql)
                self.assertIn("alter table jianshi_cms."+name+" force row level security;", sql)
        self.assertEqual(sql.count("force row level security;"), 5)
        self.assertIn("revoke all on schema jianshi_cms from PUBLIC, anon, authenticated;", sql)
        self.assertIn("revoke all on all tables in schema jianshi_cms from PUBLIC, anon, authenticated;", sql)
        self.assertIn("revoke all on all sequences in schema jianshi_cms from PUBLIC, anon, authenticated;", sql)
        self.assertNotRegex(sql, r"(?i)grant\s+(usage|select|insert|update|delete)\s+on\s+.*?\s+to\s+(anon|authenticated)")
        self.assertNotIn("create policy", sql.lower())
        self.assertNotIn("security definer", sql.lower())

    def test_release_needs_review_rights_and_cannot_bypass_accounts(self):
        sql=self.sql
        for marker in ("content_publication_gate", "content_published_date_gate",
                       "last_reviewer_id <> owner_user_id", "rights_declared",
                       "facts_checked", "source_evidence_private", "usage_consent",
                       "security_scan_state", "private_asset_key", "public_allowlist_json",
                       "review_event_id", "unique(item_id, request_id)"):
            self.assertIn(marker, sql)
        self.assertIn("grant select, insert on jianshi_cms.content_revisions to service_role;", sql)
        self.assertIn("grant select, insert on jianshi_cms.review_events to service_role;", sql)
        self.assertNotIn("grant select, insert, update on jianshi_cms.review_events", sql)
        self.assertNotIn("grant select, insert, update on jianshi_cms.content_revisions", sql)
        self.assertIn("'cms_editor',false", sql)
        self.assertIn("on conflict(feature_key) do update set enabled=false", sql)

    def test_internal_preview_is_noindex_synthetic_and_local_only(self):
        page = self.ui
        dom=PageParser()
        dom.feed(page)
        self.assertIn('content="noindex,nofollow,noarchive"', page)
        self.assertIn('content="no-referrer"', page)
        self.assertIn("仅离线原型", page)
        self.assertIn("合成", page)
        self.assertIn("没有真实课程视频", page)
        self.assertEqual(len(dom.scripts), 1)
        self.assertEqual(len(dom.forms), 0)
        for key in ("view-queue","view-media","view-audit","records","editor",
                    "output","preview","reset","status"):
            self.assertIn(key, dom.ids)
        for button in dom.buttons:
            self.assertNotEqual(button.get("type"), "submit")
        self.assertIn("addEventListener('click'", page)
        self.assertIn("output.textContent", page)
        self.assertNotIn("output.innerHTML", page)
        for marker in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon(",
                       "localStorage", "sessionStorage", "document.cookie",
                       "<iframe", "<form", "type=\"module\"",
                       "src=\"https://", "script src=", "service_role",
                       "api_key", "PRIVATE_KEY"):
            self.assertNotIn(marker, page)
        self.assertLess(len(page.encode("utf-8")), 50000)

    def test_private_proto_never_exported_to_public_static(self):
        release=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertNotIn("f21c", release)
        self.assertNotIn("jianshi_cms", release)
        assert (ROOT/"web/dist").exists()
        self.assertFalse((ROOT/"web/dist/prototypes/f21c/index.html").exists())
        self.assertFalse((ROOT/"web/dist/f21c/index.html").exists())
        self.assertFalse((ROOT/"web/dist/db/migrations/0054_jianshi_cms_private_foundation.sql").exists())

    def test_synthetic_review_flow_still_requires_distinct_actors_and_version(self):
        record={
            "content_id": "SYNTHETIC_G1C_001",
            "content_type": "RESOURCE",
            "title": "合成资源版权目录",
            "summary": "仅供 staging 安全测试，不对应真实企业或公开资源。",
            "category": "测试资源",
            "tags": ["SYNTHETIC"],"language": "zh-CN","status": "DRAFT",
            "author_id": "TEST_AUTHOR","revision": 1,
            "source_refs": [{"kind": "AUTHOR_ORIGINAL","description": "synthetic test content"}],
            "source_verified_at": "2026-10-11",
            "license_status": "OWNED","rights_confirmed": True,
            "facts_verified": True,
            "private_notes": "SYNTHETIC_PRIVATE_DETAIL",
        }
        desk=InMemoryReviewWorkbench()
        desk.add_draft(record)
        desk.change_state(record["content_id"],"IN_REVIEW",actor_id="TEST_AUTHOR",
                          role="AUTHOR",expected_revision=1)
        with self.assertRaises(ContentContractError):
            desk.change_state(record["content_id"],"APPROVED",actor_id="TEST_AUTHOR",
                              role="REVIEWER",expected_revision=2)
        with self.assertRaises(ContentContractError):
            desk.change_state(record["content_id"],"APPROVED",actor_id="TEST_REVIEWER",
                              role="REVIEWER",expected_revision=1)
        desk.change_state(record["content_id"],"APPROVED",actor_id="TEST_REVIEWER",
                          role="REVIEWER",expected_revision=2)
        desk.change_state(record["content_id"],"PUBLISHED",actor_id="TEST_PUBLISHER",
                          role="PUBLISHER",expected_revision=3,published_at="2026-10-11")
        public=desk.public_feed()
        self.assertEqual(len(public),1)
        self.assertNotIn("private_notes",public[0])
        self.assertNotIn("SYNTHETIC_PRIVATE_DETAIL",str(public))
        desk.change_state(record["content_id"],"UNPUBLISHED",actor_id="TEST_PUBLISHER",
                          role="PUBLISHER",expected_revision=4)
        self.assertEqual(desk.public_feed(),[])

    def test_production_cron_and_auth_gates_remain_frozen(self):
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"),1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"),1)
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY",
                      (ROOT/"db/migrations/0037_auth_launch_gate.sql").read_text())
        self.assertIn("'v2_matchmaking',false",
                      (ROOT/"db/migrations/0053_jianshi2_private_matching_foundation.sql").read_text())


if __name__=="__main__":
    unittest.main()
