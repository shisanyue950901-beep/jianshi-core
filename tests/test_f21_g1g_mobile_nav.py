"""F2.1 G1-G: validate real homepage mobile menu JS and responsive CSS.

Uses an in-memory DOM stub to run the EXACT inline script rendered by the
static site builder. It never connects to the web, sets cookies or sends data.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/release"))
from p423_build_project_proofs import parse_cases
from p425_public_admission import eligible_cases
from p445_unified_home import build_home


class Scanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts: list[str] = []
        self._script = False
        self.navs: list[str] = []
        self.details: list[dict] = []
        self.summaries: list[dict] = []
        self.links: list[dict] = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            self._script = True
            self.scripts.append("")
        if tag == "nav":
            self.navs.append(a.get("aria-label", ""))
        if tag == "details":
            self.details.append(a)
        if tag == "summary":
            self.summaries.append(a)
        if tag == "a":
            self.links.append(a)
    def handle_data(self, data):
        if self._script:
            self.scripts[-1] += data
    def handle_endtag(self, tag):
        if tag == "script":
            self._script = False


class F21MobileMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = build_home(eligible_cases(parse_cases()))
        cls.dom = Scanner()
        cls.dom.feed(cls.html)

    def test_one_home_and_two_responsive_nav_modes(self):
        s = self.html
        self.assertEqual(s.count('id="j2"'), 1)
        self.assertNotIn('id="ring"', s)
        self.assertEqual(self.dom.navs.count("主要导航"), 1)
        self.assertEqual(self.dom.navs.count("移动导航"), 1)
        self.assertEqual(len([x for x in self.dom.details if x.get("class")=="j2-mobile"]), 1)
        self.assertEqual(len([x for x in self.dom.summaries if x.get("aria-label")=="展开主要导航"]),1)
        self.assertIn("@media(max-width:1080px){#j2 .j2-nav{display:none}#j2 .j2-mobile{display:block}}", s)
        self.assertIn("@media(max-width:400px)", s)
        self.assertIn("max-height:min(65dvh,460px)", s)
        self.assertIn("overscroll-behavior:contain", s)
        self.assertIn("#j2 .j2-mobile summary:focus-visible", s)
        self.assertIn("prefers-reduced-motion:reduce", s)
        self.assertIn('name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"',s)
        self.assertEqual(s.count("<script>"), 1)
        self.assertEqual(s.count("</script>"), 1)

    def test_all_navigation_items_point_to_authored_destinations(self):
        html=self.html
        fragments=("#j2-opportunities","#j2-solutions","#j2-marketplace","#j2-talent","#j2-academy")
        for href in fragments:
            self.assertGreaterEqual(html.count('href="'+href+'"'),2,href)
            self.assertIn('id="'+href[1:]+'"',html)
        self.assertGreaterEqual(html.count('href="/sources/"'),2)
        for bad in ("service_role","SMTP_PASSWORD","SYNTHETIC_G1F"):
            self.assertNotIn(bad,html)

    @unittest.skipUnless(shutil.which("node"),"Node unavailable; CI must run this check on Node-enabled runner")
    def test_rendered_inline_js_closes_menu_and_preserves_legacy_hash(self):
        script=self.dom.scripts[0]
        # Run the real generated JavaScript inside a fully synthetic DOM.
        # Test click, Escape+focus, outside pointer, break point resize and
        # historic redirects without loading a browser or remote webpage.
        node = r"""
const vm=require('node:vm');
const assert=require('node:assert/strict');
const code=JSON.parse(process.argv[1]);
let close={}, clickers=[], pointer=null, resize=null, focused=0, replaced=[];
const summary={focus:()=>focused++};
const menu={
 open:false,
 querySelectorAll:(sel)=>{assert.equal(sel,'.j2-mobile-list a');return [0,1].map(()=>({
   addEventListener:(type,handler)=>{assert.equal(type,'click');clickers.push(handler);}
 }));},
 querySelector:(sel)=>{assert.equal(sel,'summary');return summary;},
 addEventListener:(type,handler)=>{close[type]=handler;},
 contains:(target)=>target==='inside'
};
let desktop=false;
const document={
 querySelector:(sel)=>{assert.equal(sel,'#j2 .j2-mobile');return menu;},
 addEventListener:(type,handler)=>{if(type==='pointerdown')pointer=handler;}
};
const window={
 addEventListener:(type,handler)=>{if(type==='resize')resize=handler;},
 matchMedia:(q)=>{assert.equal(q,'(min-width:1081px)');return {matches:desktop};}
};
const location={hash:'',replace:(to)=>replaced.push(to)};
vm.runInNewContext(code,{window,document,location});
assert.equal(clickers.length,2);
assert.equal(typeof close.keydown,'function');
assert.equal(typeof pointer,'function');
assert.equal(typeof resize,'function');
menu.open=true; clickers[0]();assert.equal(menu.open,false,'fragment navigation must close');
menu.open=true; close.keydown({key:'Escape'});assert.equal(menu.open,false);
assert.equal(focused,1,'Escape returns focus to menu opener');
menu.open=true;pointer({target:'inside'});assert.equal(menu.open,true);
pointer({target:'outside'});assert.equal(menu.open,false,'outside click closes');
menu.open=true;desktop=false;resize();assert.equal(menu.open,true);
desktop=true;resize();assert.equal(menu.open,false,'desktop resize closes');
location.hash='#archive';vm.runInNewContext(code,{window,document,location});
assert.equal(replaced[0],'/#j2-opportunities');
console.log('F2.1 mobile DOM interactions 7/7 PASS');
"""
        result=subprocess.run(["node","-e",node,json.dumps(script)],
            cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout[-3200:])
        self.assertIn("7/7 PASS",result.stdout)


if __name__=="__main__":
    unittest.main()
