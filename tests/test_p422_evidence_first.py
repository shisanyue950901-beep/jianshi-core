"""P4.22 evidence-first: live public aggregates with dated fallback and no upstream leak."""
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOME=(ROOT/"web/prototypes/p412e/index.html").read_text(encoding="utf-8")
PROOF=(ROOT/"web/prototypes/p422/evidence.html").read_text(encoding="utf-8")
RELEASE=(ROOT/"scripts/release/p412_build_public.py").read_text(encoding="utf-8")

class TestP422EvidenceFirst(unittest.TestCase):
    def test_home_prioritizes_proof_and_keeps_motion(self):
        self.assertIn('href="/validation/"',HOME)
        self.assertIn('id="proof" aria-labelledby="proof-h"',HOME)
        self.assertLess(HOME.index('id="proof"'),HOME.index('id="archive"'))
        self.assertIn('先看真实商业证据与验证缺口',HOME)
        self.assertIn('一个方向很热',HOME)
        self.assertIn('这不是具名公司的盈利证明',HOME)
        self.assertIn('data-theme="light"',HOME)
        self.assertIn("localStorage.setItem('jianshi-theme',next)",HOME)
        self.assertEqual(HOME.count('data:image/webp;base64,'),8)
        self.assertEqual(HOME.count('<style>'),1)
        self.assertEqual(HOME.count('<script>'),1)
        self.assertLess(len(HOME.encode('utf-8'))+124,260000)

    def test_public_validations_are_explicitly_aggregated_and_dated(self):
        self.assertEqual(PROOF.count('<style>'),1)
        self.assertEqual(PROOF.count('<script>'),1)
        self.assertIn('view=catalog',PROOF)
        self.assertIn("const snapshot='2026-10-09T00:45:00Z'",PROOF)
        self.assertIn('历史审核快照（非实时）',PROOF)
        self.assertIn('在线更新暂不可用',PROOF)
        self.assertIn("if(!input||!Array.isArray(input.items)||input.items.length!==6)return null",PROOF)
        self.assertIn('if(x.public_ready&&(tech===0||commercial===0))return null',PROOF)
        self.assertIn("if(![tech,commercial,demand].every(validNumber)",PROOF)
        self.assertIn("timeZone:'Asia/Shanghai'",PROOF)
        self.assertIn('credentials:\'omit\'',PROOF)
        self.assertIn('cache:\'no-store\'',PROOF)
        self.assertIn("const allowed=new Map(base.map",PROOF)
        self.assertIn('textContent=String(value)',PROOF)
        self.assertIn('这不是',HOME)
        self.assertIn('不能据此证明某家企业盈利',PROOF)
        self.assertIn('需求证据',PROOF)
        self.assertEqual(PROOF.count('data:image/webp;base64,'),0)
        for forbidden in ('Empire Flippers','listing_number','source_url','public_title','source_ref_ids','OPP_V0.2'):
            self.assertNotIn(forbidden.lower(),PROOF.lower())
        self.assertNotIn('innerHTML',PROOF)

    def test_release_publishes_only_an_allowlisted_page(self):
        self.assertIn('EVIDENCE = ROOT / "web" / "prototypes" / "p422" / "evidence.html"',RELEASE)
        self.assertIn('OUTPUT / "validation" / "index.html"',RELEASE)
        self.assertIn('for banned in ("Empire Flippers"',RELEASE)
        self.assertIn('f"<url><loc>{SITE}/validation/</loc></url>"',RELEASE)
        self.assertIn('OUTPUT = ROOT / "web" / "dist"',RELEASE)
        node=shutil.which("node")
        if node:
            scripts=[re.search(r'<script>([\s\S]*?)</script>',x) for x in (HOME,PROOF)]
            for match in scripts:
                self.assertIsNotNone(match)
                run=subprocess.run([node,'--check','-'],input=match.group(1),
                                   capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stderr)

if __name__=="__main__":
    unittest.main()
