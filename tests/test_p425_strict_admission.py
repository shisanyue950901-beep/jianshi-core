"""Strict publication gate: product homepage != attributable operating evidence."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/"scripts/release/p423_build_project_proofs.py"
DIST=ROOT/"web/dist"
LEDGER=ROOT/"config/p424_project_research_evidence.json"

class StrictPublicAdmissionTest(unittest.TestCase):
    def test_qualifying_projects_require_business_operating_evidence(self):
        data=json.loads(LEDGER.read_text(encoding="utf-8"))
        allowed={x["id"] for x in data["additional_evidence"] if x["tier"] in ("regulatory_filing","founder_historical")}
        self.assertEqual(allowed,{"nerdwallet","carrd","plausible"})
        self.assertNotIn("easlo",allowed)
        self.assertNotIn("louise",allowed)

    def test_only_admitted_businesses_have_public_dossiers(self):
        r=subprocess.run([sys.executable,str(GEN)],cwd=ROOT,capture_output=True,text=True,timeout=35)
        self.assertEqual(r.returncode,0,r.stderr)
        report=json.loads(r.stdout)
        self.assertEqual(report["cases"],3)
        self.assertEqual(report["public_pages"],4)
        self.assertEqual(report["held_for_research"],17)
        paths={p.parent.name for p in (DIST/"projects").glob("*/index.html")}
        self.assertEqual(paths,{"nerdwallet","carrd","plausible"})
        home=(DIST/"projects/index.html").read_text(encoding="utf-8")
        self.assertIn('3 家公司的生意',home)
        self.assertNotIn('Easlo｜',home)
        self.assertNotIn('Louise Lennox',home)
        self.assertNotIn('Tally｜',home)

    def test_publish_runtime_filters_legacy_editorial_case_payload(self):
        src=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
        sys.path.insert(0,str(ROOT/"scripts/release"))
        from p423_build_project_proofs import parse_cases
        from p425_public_admission import eligible_cases,public_home
        all_cases=parse_cases()
        self.assertEqual(len(all_cases),20)
        eligible=eligible_cases(all_cases)
        self.assertEqual({x["id"] for x in eligible},{"carrd","nerdwallet","plausible"})
        compiled=public_home(src,eligible)
        self.assertEqual(compiled.count("data:image/webp;base64,"),8)
        self.assertIn("3 个有经营证据的项目",compiled)
        self.assertIn('data-rank-period="all" aria-pressed="true"',compiled)
        self.assertIn("let kind='all',rankPeriod='all'",compiled)
        self.assertIn("const PUBLIC_EVIDENCE_LABELS=",compiled)
        self.assertIn("查看经营依据 ↗",compiled)
        self.assertNotIn("Easlo｜",compiled)
        self.assertNotIn("Louise Lennox",compiled)
        self.assertNotIn("Tally｜",compiled)
        self.assertNotIn("Bellroy｜",compiled)
        self.assertIn("视觉示意 · 非收录项目",compiled)
        self.assertIn("Carrd｜",compiled)
        self.assertIn("NerdWallet｜",compiled)
        self.assertIn("Plausible｜",compiled)

if __name__=="__main__":
    unittest.main()
