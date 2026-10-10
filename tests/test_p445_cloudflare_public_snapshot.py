"""P4.45: preserve GitHub-audited public research on Cloudflare Pages builds."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"web"/"build.py"

def load_builder():
    spec=importlib.util.spec_from_file_location("p445_snapshot_builder",SOURCE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CloudflareSnapshotParityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.module=load_builder()
        self.module.REPO_ROOT=self.root
        self.module.DIST=self.root/"web"/"dist"
        self.module.API=""
        self.cfenv=patch.dict(os.environ,{
            "CF_PAGES":"1",
            "CF_PAGES_BRANCH":"main",
        },clear=False)
        self.cfenv.start()
        self.addCleanup(self.cfenv.stop)

    def write(self, rel, content):
        dest=self.root/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(content,encoding="utf-8")
        return dest

    def populate(self):
        self.write("web/dist/index.html",'<main id="ring"><a href="/research/">研究分类</a></main>')
        self.write("web/dist/_headers","/*\n  Cache-Control: no-store, max-age=0\n")
        self.write("web/dist/_redirects","/config/* / 302\n")
        self.write("web/dist/research/index.html",'<meta name="robots" content="noindex,follow"><div id="category-comparison"></div>')
        self.write("dist/opportunities/index.html",'<div id="category-comparison"></div>')
        for slug in self.module.PUBLISHED_RESEARCH_SLUGS:
            text=(f'<meta name="robots" content="noindex,nofollow">'
                  f'<div id="sample-metrics"></div>'
                  f'<p>当前分类包含 72 个去重项目案例；其中 71 个包含挂牌报价信息。</p>')
            self.write(f"web/dist/research/{slug}/index.html",text)
            self.write(f"dist/opportunity/{slug}/index.html",text)

    def test_preserves_public_snapshot_without_http_requests(self):
        self.populate()
        snap=self.root/"web/dist/research/amazon-fba-niche-brand/index.html"
        before=snap.read_bytes()
        self.assertTrue(self.module._preserve_cloudflare_public_snapshot())
        self.assertEqual(before,snap.read_bytes())
        self.assertEqual(len(self.module.PUBLISHED_RESEARCH_SLUGS),6)

    def test_never_use_snapshot_mode_outside_production_cloudflare(self):
        self.populate()
        with patch.dict(os.environ,{"CF_PAGES":"0"}):
            self.assertFalse(self.module._preserve_cloudflare_public_snapshot())
        with patch.dict(os.environ,{"CF_PAGES_BRANCH":"feature-preview"}):
            self.assertFalse(self.module._preserve_cloudflare_public_snapshot())
        self.module.API="https://example.invalid/public-feed"
        self.assertFalse(self.module._preserve_cloudflare_public_snapshot())

    def test_fail_closed_when_snapshot_file_missing(self):
        self.populate()
        (self.root/"web/dist/research/agency-business/index.html").unlink()
        with self.assertRaisesRegex(RuntimeError,"Missing audited committed Pages snapshot"):
            self.module._preserve_cloudflare_public_snapshot()

    def test_fail_closed_when_mirror_counts_disagree(self):
        self.populate()
        slug="amazon-fba-niche-brand"
        self.write(f"dist/opportunity/{slug}/index.html",
                   '<meta name="robots" content="noindex,nofollow">'
                   '<p>当前分类包含 70 个去重项目案例。</p>')
        with self.assertRaisesRegex(RuntimeError,"Published research snapshot mismatch"):
            self.module._preserve_cloudflare_public_snapshot()

    def test_fail_closed_if_public_home_or_index_contract_was_lost(self):
        self.populate()
        self.write("web/dist/index.html",'<main id="ring"></main>')
        with self.assertRaisesRegex(RuntimeError,"Committed public homepage contract missing"):
            self.module._preserve_cloudflare_public_snapshot()
        self.populate()
        self.write("web/dist/research/index.html",'<div id="category-comparison"></div>')
        with self.assertRaisesRegex(RuntimeError,"Committed public comparison contract missing"):
            self.module._preserve_cloudflare_public_snapshot()

    def test_fail_closed_if_security_controls_are_dropped(self):
        self.populate()
        self.write("web/dist/_headers","/*\n  Cache-Control: max-age=3600\n")
        with self.assertRaisesRegex(RuntimeError,"Committed public cache policy missing"):
            self.module._preserve_cloudflare_public_snapshot()

if __name__=="__main__":
    unittest.main()
