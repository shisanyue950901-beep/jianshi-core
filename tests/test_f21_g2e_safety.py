"""G2-E public isolation: rollback migration must be additive and the operator
prototype must not enter the static release artifact. Local only, no CMS writes.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
MIG=(ROOT/"db/migrations/0057_jianshi_cms_historical_draft_restore.sql").read_text()
HTML=(ROOT/"web/prototypes/f21g2e/index.html").read_text(encoding="utf-8")
JS=(ROOT/"web/prototypes/f21g2e/app.js").read_text(encoding="utf-8")
MODEL=(ROOT/"web/prototypes/f21g2e/model.js").read_text(encoding="utf-8")
BUILDER=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/publish-static.yml").read_text(encoding="utf-8")

class TestG2ESafety(unittest.TestCase):
    def test_no_public_exposure_from_build(self):
        self.assertNotIn("f21g2e",BUILDER)
        self.assertNotIn("f21g2e",WF)
        self.assertFalse((ROOT/"web/dist/prototypes/f21g2e/index.html").exists())
        self.assertFalse((ROOT/"web/dist/cms-admin/index.html").exists())
        self.assertIn('content="noindex,nofollow"',HTML)
        self.assertIn("隔离合成演示",HTML)

    def test_prototype_data_only_and_no_network(self):
        for term in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon",
                     "localStorage", "sessionStorage", "document.cookie",
                     "SUPABASE_SERVICE_ROLE_KEY", "sb_secret_", "https://api."):
            self.assertNotIn(term,HTML+JS+MODEL)
        self.assertIn("replaceChildren()",JS)
        self.assertIn("textContent=",JS)
        self.assertIn("CMS_RESTORE_REQUIRES_DRAFT",MODEL)
        self.assertIn("rights:false,facts:false",MODEL)

    def test_restore_migration_private_and_additive(self):
        self.assertIn("language plpgsql security invoker",MIG)
        self.assertIn("perform jianshi_cms.ensure_write_gate",MIG)
        self.assertIn("from PUBLIC, anon, authenticated",MIG)
        self.assertIn("to service_role",MIG)
        self.assertNotIn("create policy",MIG.lower())
        self.assertNotIn("grant execute to authenticated",MIG.lower())
        self.assertNotIn("update public.product_feature_flags",MIG.lower())
        self.assertNotIn("drop table",MIG.lower())
        self.assertNotIn("alter table ",MIG.lower())

    def test_schedule_frequency_kept(self):
        self.assertEqual(WF.count("cron: '55 0 * * *'"),1)
        self.assertEqual(WF.count("cron: '55 6,12,18 * * *'"),1)

if __name__=="__main__":
    unittest.main()
