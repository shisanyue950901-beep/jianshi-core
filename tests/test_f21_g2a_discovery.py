"""G2-A: actual offline discovery directory + live JS interaction contracts."""
from __future__ import annotations
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/release"))
from f21_g2_discovery import ENTRIES,CATEGORIES,PROJECT_FACTS,RESEARCH_FACTS,PICK_COUNT,JS,render,publish

class Scanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.ids=[]
        self.cards=[]
        self.canonicals=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if "id" in d:self.ids.append(d["id"])
        if tag=="a":
            self.links.append(d.get("href",""))
            if "data-discover-card" in d:self.cards.append(d)
        if tag=="link" and d.get("rel")=="canonical":
            self.canonicals.append(d.get("href"))

class DiscoveryTests(unittest.TestCase):
    def test_every_editorial_route_is_unique_and_explicit(self):
        self.assertEqual(len(ENTRIES),17)
        self.assertEqual(len(set(row[0] for row in ENTRIES)),17)
        self.assertEqual(Counter(row[1] for row in ENTRIES),
                         {"solutions":4,"research":6,"projects":3,"guides":4})
        for route,kind,title,summary,label in ENTRIES:
            with self.subTest(route=route):
                self.assertTrue(route.startswith("/") and route.endswith("/"))
                self.assertNotIn("http",route)
                self.assertTrue(all((title,summary,label)))
                self.assertNotIn("/internal/",route)
                self.assertNotIn("/prototypes/",route)

    def test_page_has_search_filters_and_real_destinations(self):
        html=render()
        dom=Scanner()
        dom.feed(html)
        self.assertEqual(dom.ids.count("discover"),1)
        self.assertEqual(dom.ids.count("discover-query"),1)
        self.assertEqual(dom.ids.count("discover-reset"),1)
        self.assertEqual(dom.ids.count("discover-count"),1)
        self.assertEqual(dom.ids.count("discover-empty"),1)
        self.assertEqual(len(dom.cards),17)
        self.assertEqual(set(x["href"] for x in dom.cards),
                         {"/projects/" if row[1] == "projects" else row[0] for row in ENTRIES})
        self.assertEqual(sum(x["href"] == "/projects/" for x in dom.cards), 3)
        for legacy in ("/projects/carrd/", "/projects/plausible/", "/projects/nerdwallet/"):
            self.assertNotIn('href="' + legacy + '"', html)
        self.assertEqual(dom.canonicals,["https://jianshi-bua.pages.dev/discover/"])
        self.assertEqual(html.count('<script>'),1)
        self.assertEqual(html.count('<style>'),1)
        self.assertIn('role="search"',html)
        self.assertIn('aria-live="polite"',html)
        self.assertIn('href="/sources/"',html)
        self.assertIn('href="/validation/"',html)
        self.assertIn("不代表",html)
        for banned in ("SMTP_PASSWORD","sb_secret_","private_notes",
                       "SYNTHETIC_G1F","listing_number","用户联系邮箱"):
            self.assertNotIn(banned,html)

    def test_founder_first_default_before_enterprise_ai_without_fake_opportunities(self):
        html=render()
        self.assertEqual(PICK_COUNT,9)
        self.assertEqual(len(PROJECT_FACTS),3)
        self.assertEqual(len(RESEARCH_FACTS),6)
        self.assertIn('data-discover-category="founder" aria-pressed="true"',html)
        self.assertIn("找创业项目，先看怎么赚钱",html)
        self.assertIn("谁付钱",html)
        self.assertIn("怎么收费",html)
        self.assertIn("广告及商业合作伙伴",html)
        self.assertIn("不保证照着做能赚钱",html)
        self.assertLess(html.index("<h3>Carrd｜单页网站</h3>"),
                        html.index("<h3>Plausible｜网站数据分析</h3>"))
        self.assertLess(html.index("<h3>Plausible｜网站数据分析</h3>"),
                        html.index("<h3>NerdWallet｜金融产品比较</h3>"))
        self.assertLess(html.index("<h3>NerdWallet｜金融产品比较</h3>"),
                        html.index('href="/research/vertical-industry-saas/"'))
        self.assertLess(html.index('href="/research/vertical-industry-saas/"'),
                        html.index('href="/solutions/ecommerce-visual/"'))
        self.assertNotIn("G2 / PUBLIC DISCOVERY",html)
        self.assertNotIn("01 / CONTENT DIRECTORY",html)
        for slug in ("projects","research","solutions","guides","all"):
            self.assertIn('data-discover-category="'+slug+'"',html)

    def test_missing_or_redirected_public_destination_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for path,*_ in ENTRIES:
                output=root/path.lstrip("/")/"index.html"
                output.parent.mkdir(parents=True,exist_ok=True)
                output.write_text("<!doctype html><html><main>已审核公开正文</main></html>",
                                  encoding="utf-8")
            self.assertEqual(publish(root),17)
            self.assertTrue((root/"discover/index.html").exists())
            missing=root/ENTRIES[0][0].lstrip("/")/"index.html"
            missing.unlink()
            with self.assertRaisesRegex(RuntimeError,"source route missing"):
                publish(root)
            missing.write_text("<!doctype html><html><meta http-equiv='refresh'></html>",
                               encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"not a content page"):
                publish(root)

    def test_client_only_search_forbids_network_and_tracking(self):
        for token in ("fetch(", "XMLHttpRequest","WebSocket","sendBeacon",
                      "localStorage","sessionStorage","innerHTML","eval(",
                      "document.cookie","window.location"):
            self.assertNotIn(token,JS)
        self.assertIn("card.hidden=!match",JS)
        self.assertIn("aria-pressed",JS)
        self.assertIn("empty.hidden=visible!==0",JS)
        self.assertIn("reset.addEventListener('click'",JS)
        self.assertIn("reset.hidden=category==='founder'&&!query",JS)

    @unittest.skipUnless(shutil.which("node"),"Node not installed")
    def test_actual_js_filters_chinese_keywords_categories_empty_and_reset(self):
        records=[{"category":kind,"search":" ".join((name,description,note))}
                 for _,kind,name,description,note in ENTRIES]
        simulator=r"""
const vm=require('node:vm');
const assert=require('node:assert/strict');
const code=JSON.parse(process.argv[1]);
const records=JSON.parse(process.argv[2]);
const events={};
function target(data={}){
 return {dataset:data,hidden:false,value:'',textContent:'',handlers:{},
   addEventListener(type,handler){this.handlers[type]=handler;},
   setAttribute(name,v){this[name]=v;},
   focus(){events.focus=(events.focus||0)+1;}
 };
}
const input=target(),counter=target(),empty=target(),reset=target(),form=target();
const buttons=['founder','projects','research','solutions','guides','all']
 .map(type=>target({discoverCategory:type}));
const cards=records.map(r=>target({category:r.category,search:r.search}));
const root={querySelectorAll:(sel)=>sel==='[data-discover-category]'?buttons:cards};
const m={'discover':root,'discover-query':input,'discover-count':counter,
 'discover-empty':empty,'discover-reset':reset,'discover-form':form};
vm.runInNewContext(code,{document:{getElementById:id=>m[id]}});
assert.equal(cards.filter(x=>!x.hidden).length,9);
assert.equal(buttons[0]['aria-pressed'],'true');
assert.equal(reset.hidden,true);
buttons[1].handlers.click();
assert.equal(reset.hidden,false);
assert.equal(cards.filter(x=>!x.hidden).length,3);
buttons[2].handlers.click();
assert.equal(cards.filter(x=>!x.hidden).length,6);
assert.equal(buttons[2]['aria-pressed'],'true');
input.value='自动化';input.handlers.input();
assert.equal(cards.filter(x=>!x.hidden).length,1);
assert.equal(buttons[5]['aria-pressed'],'true');
input.value='行业';input.handlers.input();
assert.equal(cards.filter(x=>!x.hidden).length>=1,true);
input.value='绝不可能出现的关键词 123abc';input.handlers.input();
assert.equal(cards.filter(x=>!x.hidden).length,0);
assert.equal(empty.hidden,false);
reset.handlers.click();
assert.equal(cards.filter(x=>!x.hidden).length,9);
assert.equal(buttons[0]['aria-pressed'],'true');
assert.equal(input.value,'');
assert.equal(reset.hidden,true);
assert.equal(events.focus,1);
let prevented=false;form.handlers.submit({preventDefault(){prevented=true;}});
assert.equal(prevented,true);
console.log('G2 founder-first search/filter/empty/reset/keyboard PASS');
"""
        result=subprocess.run(["node","-e",simulator,json.dumps(JS,ensure_ascii=False),
                               json.dumps(records,ensure_ascii=False)],
                              text=True,capture_output=True,cwd=ROOT,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr[-2500:])
        self.assertIn("founder-first search/filter/empty/reset/keyboard PASS",result.stdout)

if __name__=="__main__":
    unittest.main()
