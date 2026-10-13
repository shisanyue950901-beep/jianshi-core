"""P4.48: useful local-only V2 tools cannot collect or publish user data."""
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/release"))
from p448_v2_local_drafts import PAGES, SCRIPT, SPEC, publish, render_one


class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.fields = []
        self.links = []
        self.scripts = 0
        self.forms = 0

    def handle_starttag(self, tag, attrs):
        vals = dict(attrs)
        if vals.get("id"):
            self.ids.add(vals["id"])
        if tag == "textarea":
            self.fields.append(vals)
        if tag == "a":
            self.links.append(vals.get("href"))
        if tag == "script":
            self.scripts += 1
        if tag == "form":
            self.forms += 1


class LocalDraftTests(unittest.TestCase):
    def test_two_separate_draft_routes_and_finite_fields(self):
        self.assertEqual(set(PAGES), {"marketplace/brief/", "talent/portfolio/"})
        for route in PAGES:
            page = render_one(route)
            dom = Inspect()
            dom.feed(page)
            self.assertEqual(len(dom.fields), 7)
            self.assertEqual(dom.scripts, 1)
            self.assertEqual(dom.forms, 0)
            self.assertIn("draft-preview", dom.ids)
            self.assertIn("draft-generate", dom.ids)
            self.assertIn("draft-copy", dom.ids)
            self.assertIn("draft-clear", dom.ids)
            self.assertIn("draft-status", dom.ids)
            self.assertIn("draft-progress", dom.ids)
            self.assertIn(SPEC[route]["back"], dom.links)
            self.assertIn('rel="canonical"', page)
            self.assertIn("不会上传或保存你写的内容", page)
            self.assertIn("关闭或刷新页面后内容会消失", page)
            self.assertIn("未提交", page)
            for field in dom.fields:
                self.assertTrue(int(field["maxlength"]) <= 700)
                self.assertTrue(field["data-label"])
                self.assertIn("draft-", field["id"])

    def test_no_data_exfiltration_or_persistence(self):
        for route in PAGES:
            page = render_one(route)
            for blocked in (
                "fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket",
                "localStorage", "sessionStorage", "indexedDB", "serviceWorker",
                "document.cookie", "<iframe", "<form", "action=", "http://",
                "<video", "外部支付", "立即竞标",
            ):
                self.assertNotIn(blocked, page)
            self.assertEqual(page.count("<script>"), 1)
            self.assertIn("output.textContent", page)
            self.assertNotIn("output.innerHTML", page)
            self.assertIn("navigator.clipboard.writeText", page)
            self.assertIn("addEventListener('click'", page)
            self.assertIn("button type=\"button\"", page)
        self.assertNotIn("eval(", SCRIPT)
        self.assertNotIn("new Function(", SCRIPT)

    def test_output_is_complete_but_only_local(self):
        self.assertEqual(SCRIPT.count("copy.addEventListener"), 1)
        self.assertEqual(SCRIPT.count("generate.addEventListener"), 1)
        self.assertEqual(SCRIPT.count("clear.addEventListener"), 1)
        self.assertIn("（待补充）", SCRIPT)
        self.assertIn("草稿只在当前页面生成", render_one(PAGES[0]))
        self.assertIn("没有上传或发布按钮", render_one(PAGES[1]))
        for route in PAGES:
            self.assertNotIn('type="submit"', render_one(route))

    def test_publish_only_allowed_static_routes(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            self.assertEqual(publish(base), 2)
            for route in PAGES:
                page = base / route / "index.html"
                self.assertTrue(page.exists())
                self.assertEqual(page.read_text(), render_one(route))
            for rel in ("config", "db", "supabase", "docs", "scripts"):
                self.assertFalse((base / rel).exists())

    def test_release_sitemap_and_feature_flags_remain_protected(self):
        source = (ROOT / "scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertIn("publish_v2_drafts(OUTPUT)", source)
        self.assertIn("for route in DRAFT_PAGES", source)
        workflow = (ROOT / ".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(workflow.count("cron: '55 0 * * *'"), 1)
        self.assertEqual(workflow.count("cron: '55 6,12,18 * * *'"), 1)
        auth = (ROOT / "db/migrations/0037_auth_launch_gate.sql").read_text()
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY", auth)
        self.assertIn("'account_auth'", auth)


if __name__ == "__main__":
    unittest.main()
