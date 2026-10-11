"""F2.1 G1: real shared page primitives, accessible local catalogue and CMS review kernel."""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/release"))
sys.path.insert(0, str(ROOT / "scripts/content"))

from f21_catalog_filter import JS, CATEGORIES, BY_SLUG
from f21_components import site_header, site_footer, PUBLIC_NAV
from f21_review_workbench import InMemoryReviewWorkbench
from f21_content_contract import ContentContractError
from p446_content_hubs import render_pages, SOLUTIONS
from p448_v2_local_drafts import render_one


class HTMLInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nav = []
        self.ids = {}
        self.refs = []
        self.current = []
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids[attrs["id"]] = self.ids.get(attrs["id"], 0) + 1
        if tag == "nav":
            self.nav.append(attrs.get("aria-label", ""))
        if tag == "a":
            self.refs.append(attrs.get("href", ""))
            if "aria-current" in attrs:
                self.current.append(attrs.get("href"))
        if tag in ("input", "select"):
            self.inputs.append((tag, attrs))


class G1ComponentsAndCMS(unittest.TestCase):
    @staticmethod
    def demo():
        return {
            "content_id": "SYNTHETIC_G1_CMS_001",
            "content_type": "SOLUTION_GUIDE",
            "title": "仅合成：AI 方案结构测试",
            "summary": "此方案不对应任何真实客户、企业订单或成功案例。",
            "category": "合成测试", "tags": ["TEST", "CMS"],
            "language": "zh-CN", "status": "DRAFT",
            "author_id": "TEST_EDITOR_A", "revision": 1,
            "source_refs": [{"kind": "AUTHOR_ORIGINAL", "description": "Synthetic sample for tests"}],
            "source_verified_at": "2026-10-11", "license_status": "OWNED",
            "rights_confirmed": True, "facts_verified": True,
            "private_notes": "NEVER_LEAK_SYNTHETIC_SECRET",
            "contact_phone": "TEST_NO_REAL_PHONE",
        }

    def test_shared_navigation_and_footer_on_ten_public_content_pages(self):
        pages = render_pages()
        pages["marketplace/brief/"] = render_one("marketplace/brief/")
        pages["talent/portfolio/"] = render_one("talent/portfolio/")
        self.assertEqual(len(pages), 10)
        self.assertEqual(len(PUBLIC_NAV), 6)
        self.assertIn('aria-label="辅助信息"', site_footer())
        for route, document in pages.items():
            with self.subTest(route=route):
                dom = HTMLInspector()
                dom.feed(document)
                self.assertIn("主要导航", dom.nav)
                self.assertIn("移动导航", dom.nav)
                self.assertIn("辅助信息", dom.nav)
                self.assertEqual(document.count('aria-label="见势首页"'), 1)
                self.assertEqual(document.count('<details class="mobile">'), 1)
                self.assertIn('href="/privacy/"', document)
                self.assertEqual(len(dom.current), 2)
                expected = "/" + route.split("/")[0] + "/"
                self.assertEqual(dom.current, [expected, expected])
                self.assertEqual(document.count("<main>"), 1)
                self.assertEqual(document.count("</main>"), 1)

    def test_catalogue_has_four_verified_cards_and_local_search_controls(self):
        s = render_pages()["solutions/"]
        d = HTMLInspector()
        d.feed(s)
        self.assertEqual(d.ids.get("catalog"), 1)
        self.assertEqual(d.ids.get("f21-search"), 1)
        self.assertEqual(d.ids.get("f21-category"), 1)
        self.assertEqual(d.ids.get("f21-reset"), 1)
        self.assertEqual(d.ids.get("f21-results"), 1)
        self.assertEqual(d.ids.get("f21-empty"), 1)
        self.assertEqual(s.count('data-f21-solution data-category="'), 4)
        self.assertEqual(s.count('<script>'), 1)
        self.assertEqual(len(CATEGORIES), 4)
        self.assertEqual(set(BY_SLUG), {row["slug"] for row in SOLUTIONS})
        self.assertEqual(s.count('data-category="creative"'), 2)
        self.assertEqual(s.count('data-category="automation"'), 1)
        self.assertEqual(s.count('data-category="global"'), 1)
        self.assertIn("已找到 ", JS)
        self.assertIn("card.hidden=!show;", JS)
        self.assertIn("empty.hidden=visible!==0;", JS)
        self.assertIn("reset.addEventListener('click'", JS)
        self.assertIn("aria-live=\"polite\"", s)
        for banned in ("fetch(", "sendBeacon", "XMLHttpRequest", "WebSocket",
                       "localStorage", "sessionStorage", "innerHTML", "eval("):
            self.assertNotIn(banned, JS)

    def test_other_guides_remain_static_and_all_study_links_work(self):
        pages = render_pages()
        for route, markup in pages.items():
            if route != "solutions/":
                self.assertEqual(markup.count("<script>"), 0, route)
        for row in SOLUTIONS:
            self.assertIn('href="/solutions/' + row["slug"] + '/"', pages["solutions/"])
            self.assertIn('id="delivery"', pages["solutions/" + row["slug"] + "/"])

    def test_cms_two_person_review_and_safe_public_feed(self):
        workspace = InMemoryReviewWorkbench()
        initial = self.demo()
        added = workspace.add_draft(initial)
        self.assertEqual(added["revision"], 1)
        self.assertEqual(initial["status"], "DRAFT")
        with self.assertRaises(ContentContractError):
            workspace.add_draft(initial)
        with self.assertRaises(ContentContractError):
            workspace.private_view(initial["content_id"], actor_id="TEST_RANDOM", role="AUTHOR")
        self.assertEqual(workspace.public_feed(), [])
        first = workspace.change_state(initial["content_id"], "IN_REVIEW",
                                       actor_id="TEST_EDITOR_A", role="AUTHOR", expected_revision=1)
        with self.assertRaises(ContentContractError):
            workspace.change_state(initial["content_id"], "APPROVED",
                                   actor_id="TEST_EDITOR_A", role="REVIEWER", expected_revision=2)
        with self.assertRaises(ContentContractError):
            workspace.change_state(initial["content_id"], "APPROVED",
                                   actor_id="TEST_REVIEWER_B", role="REVIEWER", expected_revision=1)
        second = workspace.change_state(initial["content_id"], "APPROVED",
                                        actor_id="TEST_REVIEWER_B", role="REVIEWER", expected_revision=2)
        third = workspace.change_state(initial["content_id"], "PUBLISHED",
                                       actor_id="TEST_PUBLISHER_C", role="PUBLISHER",
                                       expected_revision=3, published_at="2026-10-11")
        self.assertEqual([first["revision"], second["revision"], third["revision"]], [2, 3, 4])
        feed = workspace.public_feed()
        self.assertEqual(len(feed), 1)
        self.assertNotIn("private_notes", feed[0])
        self.assertNotIn("contact_phone", feed[0])
        self.assertNotIn("TEST_NO_REAL_PHONE", str(feed))
        self.assertNotIn("NEVER_LEAK_SYNTHETIC_SECRET", str(feed))
        self.assertEqual(len(workspace.audit_log()), 3)
        workspace.change_state(initial["content_id"], "UNPUBLISHED",
                               actor_id="TEST_PUBLISHER_C", role="PUBLISHER", expected_revision=4)
        self.assertEqual(workspace.public_feed(), [])

    def test_cms_rejected_or_stale_input_does_not_mutate_audit(self):
        w = InMemoryReviewWorkbench()
        d = self.demo()
        w.add_draft(d)
        for state, actor, role, revision in [
            ("PUBLISHED", "TEST_EDITOR_A", "AUTHOR", 1),
            ("IN_REVIEW", "TEST_RANDOM", "AUTHOR", 1),
            ("IN_REVIEW", "TEST_EDITOR_A", "AUTHOR", 2),
        ]:
            with self.subTest(state=state,actor=actor):
                with self.assertRaises(ContentContractError):
                    w.change_state(d["content_id"], state, actor_id=actor,
                                   role=role, expected_revision=revision)
        self.assertEqual(len(w.audit_log()), 0)
        self.assertEqual(w.private_view(d["content_id"],actor_id="TEST_EDITOR_A",role="AUTHOR")["status"], "DRAFT")


if __name__ == "__main__":
    unittest.main()
