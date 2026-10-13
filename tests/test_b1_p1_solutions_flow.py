"""B1 P1: human-first four-solution directory and details stay within editorial scope."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from p446_content_hubs import CARD_PREVIEWS, SOLUTIONS, render_pages
from f21_catalog_filter import JS


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.related_links = []
        self.sections = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "data-f21-solution" in attrs:
            self.cards.append(attrs)
        if tag == "a" and "g2c-link" in attrs.get("class", "").split():
            self.related_links.append(attrs["href"])
        if tag == "section" and "g2c-related" in attrs.get("class", "").split():
            self.sections.append(attrs)


class B1P1Solutions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = render_pages()
        cls.directory = cls.pages["solutions/"]

    def test_card_business_preview_is_simple_and_accurate(self):
        page = self.directory
        tags = Tags()
        tags.feed(page)
        self.assertEqual(len(tags.cards), 4)
        self.assertEqual(set(CARD_PREVIEWS), {row["slug"] for row in SOLUTIONS})
        self.assertEqual(page.count('<dl class="solution-facts">'), 4)
        self.assertEqual(page.count("<dt>适合谁</dt>"), 4)
        self.assertEqual(page.count("<dt>参考成果</dt>"), 4)
        self.assertEqual(page.count("<dt>先准备</dt>"), 4)
        for row in SOLUTIONS:
            slug = row["slug"]
            self.assertIn('/solutions/' + slug + '/', [v["href"] for v in tags.cards])
            for key in ("problem", "fit", "result", "prepare", "risk"):
                self.assertIn(CARD_PREVIEWS[slug][key], page)
        self.assertNotIn("01 / SOLUTION CATALOG", page)
        self.assertNotIn("FURTHER READING / NEXT STEP", page)
        self.assertNotIn("发布需求前先明确业务目标", page)
        self.assertNotIn("平台正式开放后才会提供", page)

    def test_default_view_shows_four_cards_and_hides_redundant_actions(self):
        page = self.directory
        self.assertIn('<button type="button" id="f21-reset" hidden>', page)
        self.assertIn('id="catalog"', page)
        self.assertIn('id="f21-empty" hidden', page)
        self.assertIn("找到 4 个应用方向", page)
        self.assertNotIn('href="#catalog"', page)
        self.assertIn('<details class="solution-guide">', page)
        self.assertIn("它不会提交订单或上传企业资料", page)
        self.assertIn('href="/marketplace/brief/"', page)
        self.assertIn('暂时不能在网站上购买服务', page)
        self.assertIn("reset.hidden=!q&&category==='all'", JS)

    def test_detail_first_answers_then_early_action_with_full_disclosure(self):
        for row in SOLUTIONS:
            page = self.pages["solutions/" + row["slug"] + "/"]
            with self.subTest(slug=row["slug"]):
                self.assertLess(page.index("能解决什么问题？"),
                                page.index("先看准备材料和参考成果"))
                self.assertLess(page.index("先看准备材料和参考成果"),
                                page.index("先做一个低风险的小测试"))
                self.assertLess(page.index("先做一个低风险的小测试"),
                                page.index('<details class="solution-technical">'))
                self.assertEqual(page.count('id="delivery"'), 1)
                self.assertIn("参考交付清单", page)
                self.assertIn("建议实施流程", page)
                self.assertIn("验收与质量检查", page)
                self.assertIn(row["boundary"], page)
                self.assertIn("个人信息或商业机密", page)
                self.assertIn("不是已发生的客户合作", page)
                self.assertIn('href="/marketplace/brief/"', page)
                self.assertIn('href="/solutions/"', page)
                self.assertNotIn('class="kicker"', page)
                tags = Tags()
                tags.feed(page)
                self.assertEqual(len(tags.related_links), 3)
                self.assertEqual(len(tags.sections), 1)
                self.assertIn("g2c-related-compact", tags.sections[0].get("class", ""))

    def test_all_editorial_guides_still_have_safe_related_public_routes(self):
        for route in ("solutions/", *(f"solutions/{r['slug']}/" for r in SOLUTIONS)):
            with self.subTest(route=route):
                page = self.pages[route]
                self.assertEqual(page.count("<main>"), 1)
                self.assertIn('<details><summary>相关内容和下一步</summary>', page)
                self.assertIn("不代表在线服务、课程或商单已开放", page)
                self.assertNotIn("保证制作效果", page)
                self.assertNotIn("立即下单", page)

    @unittest.skipUnless(shutil.which("node"), "Node JS runtime required in CI")
    def test_actual_filter_js_search_category_empty_reset(self):
        records = [
            {"category": ("creative" if r["slug"] in ("ecommerce-visual", "brand-video")
                          else "automation" if r["slug"] == "automation" else "global"),
             "keywords": (r["name"] + " " + CARD_PREVIEWS[r["slug"]]["problem"])}
            for r in SOLUTIONS
        ]
        simulator = r"""
const vm=require('node:vm'),assert=require('node:assert/strict');
const code=JSON.parse(process.argv[1]),rows=JSON.parse(process.argv[2]);
function el(){return {value:'',hidden:false,textContent:'',calls:0,
 handlers:{},addEventListener(k,f){this.handlers[k]=f;},
 focus(){this.calls++}};}
const query=el(),kind=el(),reset=el(),feedback=el(),empty=el();
kind.value='all';
const cards=rows.map(row=>({
 hidden:false,getAttribute(k){return k==='data-keywords'?row.keywords:row.category}
}));
const root={querySelector(k){return {'#f21-search':query,'#f21-category':kind,'#f21-reset':reset}[k]}};
const grid={querySelectorAll(k){assert.equal(k,'[data-f21-solution]');return cards}};
const map={'f21-solutions-search':root,'catalog':grid,'f21-results':feedback,'f21-empty':empty};
vm.runInNewContext(code,{document:{getElementById:k=>map[k]}});
assert.equal(cards.filter(x=>!x.hidden).length,4);
assert.equal(reset.hidden,true);
kind.value='creative';kind.handlers.change();
assert.equal(cards.filter(x=>!x.hidden).length,2);
assert.equal(reset.hidden,false);
kind.value='all';kind.handlers.change();
query.value='自动化';query.handlers.input();
assert.equal(cards.filter(x=>!x.hidden).length,1);
assert.equal(empty.hidden,true);
query.value='不存在-987';query.handlers.input();
assert.equal(cards.filter(x=>!x.hidden).length,0);
assert.equal(empty.hidden,false);
reset.handlers.click();
assert.equal(cards.filter(x=>!x.hidden).length,4);
assert.equal(kind.value,'all');
assert.equal(query.value,'');
assert.equal(reset.hidden,true);
assert.equal(query.calls,1);
console.log('B1-P1 filter category/text/empty/reset 4/4 PASS');
"""
        r = subprocess.run(
            ["node", "-e", simulator, json.dumps(JS, ensure_ascii=False),
             json.dumps(records, ensure_ascii=False)],
            capture_output=True, text=True, cwd=ROOT, timeout=20
        )
        self.assertEqual(r.returncode, 0, r.stderr[-2400:])
        self.assertIn("4/4 PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
