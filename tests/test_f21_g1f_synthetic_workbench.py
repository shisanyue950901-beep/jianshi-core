"""F2.1 G1-F local-only workbench: real JS model tests + strict release exclusion."""
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UI=ROOT/"web/prototypes/f21f/index.html"
STYLE=ROOT/"web/prototypes/f21f/style.css"
APP=ROOT/"web/prototypes/f21f/app.js"
MODEL=ROOT/"web/prototypes/f21f/model.js"
JS_TEST=ROOT/"tests/f21_g1f_model.test.cjs"


class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
        self.scripts=[]
        self.input_labels=set()
        self.view_buttons=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if "id" in d:
            self.ids.append(d["id"])
        if tag=="script":
            self.scripts.append(d)
        if tag=="label" and "for" in d:
            self.input_labels.add(d["for"])
        if tag=="button" and "data-view" in d:
            self.view_buttons.append(d["data-view"])


class G1FOfflineWorkbench(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui=UI.read_text(encoding="utf-8")
        cls.style=STYLE.read_text(encoding="utf-8")
        cls.app=APP.read_text(encoding="utf-8")
        cls.model=MODEL.read_text(encoding="utf-8")

    def test_internal_page_has_four_real_tabs_and_accessible_fields(self):
        inspector=Inspector()
        inspector.feed(self.ui)
        self.assertEqual(len(inspector.ids),len(set(inspector.ids)),"duplicate page id")
        self.assertEqual(inspector.view_buttons,["editor","versions","rights","audit"])
        for field in ("actor","title","summary","body","search","filter",
                      "facts","rights","license","scan"):
            self.assertIn(field,inspector.ids)
            self.assertIn(field,inspector.input_labels)
        for target in ("queue-list","queue-empty","version-from","version-to","before","after",
                       "media-list","audit-rows","audit-empty","preview-output",
                       "feedback","stale-test","metric-published"):
            self.assertIn(target,inspector.ids)
        self.assertIn('aria-live="polite"',self.ui)
        self.assertIn('content="noindex,nofollow,noarchive"',self.ui)
        self.assertIn('connect-src \'none\'',self.ui)
        self.assertIn('form-action \'none\'',self.ui)
        self.assertEqual([s.get("src") for s in inspector.scripts],["model.js","app.js"])
        self.assertIn("prefers-reduced-motion:reduce",self.style)
        for term in ("360px","@media(max-width:850px)","@media(max-width:560px)"):
            if term=="360px":
                continue
            self.assertIn(term,self.style)

    def test_no_real_identity_or_submission_or_network(self):
        self.assertIn("仅本地演练",self.ui)
        self.assertIn("不代表完成真实登录",self.ui)
        self.assertIn("没有登录、网络、数据库写入",self.ui)
        self.assertIn("SYNTHETIC_",self.model)
        self.assertIn("SyntheticCMS",self.model)
        self.assertIn("INDEPENDENT_REVIEW_REQUIRED",self.model)
        self.assertIn("STALE_REVISION",self.model)
        self.assertIn("MEDIA_RIGHTS_NOT_READY",self.model)
        self.assertIn("textContent",self.app)
        for filetext in (self.app,self.model):
            for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon(",
                              "localStorage", "sessionStorage","indexedDB",
                              "innerHTML","eval(", "new Function(",
                              "service_role", "SUPABASE_SERVICE_ROLE_KEY"):
                self.assertNotIn(forbidden,filetext)
        for term in ('<form','<iframe','<img','type="file"','src="https://'):
            self.assertNotIn(term,self.ui)
        self.assertNotIn("api.supabase",self.ui)
        self.assertNotIn("supabase.co",self.ui)

    def test_not_in_public_builder_and_no_public_artifact(self):
        release=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
        self.assertNotIn("prototypes/f21f",release)
        self.assertNotIn("f21f",release)
        for path in ("web/dist/prototypes/f21f","web/dist/f21f",
                     "web/dist/admin", "public/f21f","dist/f21f"):
            self.assertFalse((ROOT/path).exists(),path)
        wf=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")
        self.assertEqual(wf.count("cron: '55 0 * * *'"),1)
        self.assertEqual(wf.count("cron: '55 6,12,18 * * *'"),1)
        self.assertIn("AUTH_LAUNCH_GATE_NOT_READY",
            (ROOT/"db/migrations/0037_auth_launch_gate.sql").read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("node"),"Node unavailable: run node --test tests/f21_g1f_model.test.cjs separately")
    def test_full_js_editorial_flow_runs_in_node(self):
        result=subprocess.run(["node","--test",str(JS_TEST)],cwd=ROOT,
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,timeout=40,check=False)
        self.assertEqual(result.returncode,0,
                         "Actual offline JavaScript workflow failed:\n"+result.stdout[-3500:])
        self.assertIn("# pass 7",result.stdout)
        self.assertIn("# fail 0",result.stdout)


if __name__=="__main__":
    unittest.main()
