"""F2.1 G2-B: four practical solution trials and three offline interactive guides."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from f21_g2b_guided_actions import (
    CHECKLISTS, ACADEMY_PLANS, SOLUTION_TRIALS, CSS, JS,
    readiness, learning_selector, solution_trial,
)
from p446_content_hubs import SOLUTIONS, COURSE_PATHS, render_pages

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.records=[]
    def handle_starttag(self,tag,attrs):
        self.records.append((tag,dict(attrs)))

class G2BPublicGuides(unittest.TestCase):
    def test_content_integrity_and_no_fake_services(self):
        self.assertEqual(set(CHECKLISTS),{"marketplace","talent"})
        self.assertTrue(all(len(rows)==6 for rows in CHECKLISTS.values()))
        self.assertEqual(len(ACADEMY_PLANS),5)
        self.assertEqual(len({p[0] for p in ACADEMY_PLANS}),5)
        self.assertEqual({p[1] for p in ACADEMY_PLANS},{p[0] for p in COURSE_PATHS})
        self.assertEqual(set(SOLUTION_TRIALS),{r["slug"] for r in SOLUTIONS})
        for key in SOLUTION_TRIALS:
            body=solution_trial(key)
            self.assertEqual(body.count("<li>"),3)
            self.assertIn("不是已发生的客户合作",body)
            self.assertIn('href="/marketplace/brief/"',body)
        for kind in CHECKLISTS:
            self.assertEqual(readiness(kind).count('type="checkbox"'),6)
            self.assertIn("不存储、不登录、不发送",readiness(kind))
        self.assertEqual(learning_selector().count("data-g2b-plan="),5)
        self.assertEqual(learning_selector().count('type="checkbox"'),15)
        self.assertIn("不是已录制",learning_selector())

    def test_all_public_pages_render_with_accessible_actions(self):
        pages=render_pages()
        self.assertEqual(len(pages),8)
        guide_pages=("marketplace/","talent/","academy/")
        for route,page in pages.items():
            inspector=Tags()
            inspector.feed(page)
            tags=inspector.records
            expected=1 if route=="solutions/" or route in guide_pages else 0
            self.assertEqual(page.count("<script>"),expected,route)
            self.assertEqual(page.count("</script>"),expected,route)
            self.assertEqual(page.count("<main>"),1,route)
            self.assertEqual(page.count("</main>"),1,route)
            self.assertEqual(page.count('rel="canonical"'),1,route)
            if route in guide_pages:
                self.assertIn("data-g2b-checklist",page)
                self.assertIn("data-g2b-progress",page)
                self.assertIn("data-g2b-reset",page)
                self.assertIn('aria-live="polite"',page)
            if route.startswith("solutions/") and route!="solutions/":
                self.assertIn("g2b-trial",page)
                self.assertIn("低风险",page)
                self.assertEqual(page.count('href="/marketplace/brief/"'),1)
                self.assertIn('aria-label="相关内容与下一步"',page)
            for banned in ("sb_secret_","service_role","SYNTHETIC_G1F","password=","@qq.com","@gmail.com"):
                self.assertNotIn(banned,page,route)
        self.assertIn('id="g2b-academy-choice"',pages["academy/"])

    def test_browser_behavior_makes_no_network_or_persistence_calls(self):
        self.assertIn("document.querySelectorAll('[data-g2b-checklist]')",JS)
        self.assertIn("report.textContent=",JS)
        self.assertIn("c.checked=false",JS)
        self.assertIn("plan.hidden=plan.dataset.g2bPlan!==selector.value",JS)
        for forbidden in ("fetch(","XMLHttpRequest","WebSocket","sendBeacon",
                          "localStorage","sessionStorage","document.cookie",
                          "innerHTML","eval(","location.replace","window.location"):
            self.assertNotIn(forbidden,JS)
        self.assertIn("@media(max-width:700px)",CSS)

    @unittest.skipUnless(shutil.which("node"),"Node unavailable; CI must test JS")
    def test_real_js_checkbox_reset_and_learning_selector(self):
        stub=r"""
const vm=require('node:vm');
const assert=require('node:assert/strict');
const src=JSON.parse(process.argv[1]);
function node(attrs={}){
 return {dataset:attrs,checked:false,hidden:false,textContent:'',value:'',
   handlers:{},focused:0,addEventListener(k,fn){this.handlers[k]=fn;},
   focus(){this.focused++;}
 };
}
function form(total){
 const checks=Array.from({length:total},()=>node());
 const progress=node(), reset=node();
 return {checks,progress,reset,
  querySelectorAll(q){assert.equal(q,'input[type="checkbox"]');return checks;},
  querySelector(q){if(q==='[data-g2b-progress]')return progress;
    if(q==='[data-g2b-reset]')return reset;throw Error(q);}
 };
}
const f1=form(6),f2=form(3),selector=node(),plans=['visual','video','agent','global','research']
 .map(p=>node({g2bPlan:p}));
selector.value='visual';
const document={
 querySelectorAll(sel){
  if(sel==='[data-g2b-checklist]')return [f1,f2];
  if(sel==='[data-g2b-plan]')return plans;
  throw Error(sel);
 },
 getElementById(id){assert.equal(id,'g2b-academy-choice');return selector;}
};
vm.runInNewContext(src,{document});
assert.match(f1.progress.textContent,/0 \/ 6/);
f1.checks[0].checked=true;f1.checks[0].handlers.change();
assert.match(f1.progress.textContent,/1 \/ 6/);
f1.checks.forEach(c=>{c.checked=true;});f1.checks[1].handlers.change();
assert.match(f1.progress.textContent,/已完成自查，不代表平台审核通过/);
f1.reset.handlers.click();
assert.match(f1.progress.textContent,/0 \/ 6/);
assert.equal(f1.checks[0].focused,1);
assert.equal(plans.filter(p=>!p.hidden).length,1);
selector.value='agent';selector.handlers.change();
assert.equal(plans.filter(p=>!p.hidden).length,1);
assert.equal(plans[2].hidden,false);
f2.checks[0].checked=true;f2.checks[0].handlers.change();
assert.match(f2.progress.textContent,/1 \/ 3/);
console.log('G2-B checklist + reset + plan switching: 9/9 PASS');
"""
        result=subprocess.run(
            ["node","-e",stub,json.dumps(JS,ensure_ascii=False)],
            text=True,capture_output=True,cwd=ROOT,timeout=15,
        )
        self.assertEqual(result.returncode,0,result.stderr[-2400:])
        self.assertIn("9/9 PASS",result.stdout)

if __name__=="__main__":
    unittest.main()
