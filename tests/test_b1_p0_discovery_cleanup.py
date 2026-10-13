"""B1 P0 discovery information density: source/static test, not real-device proof."""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))

from f21_g2_discovery import ENTRIES, PICK_COUNT, JS, render
from f21_g2c_related_quality import RELATED, render_related


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.routes = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "discover-card" in a.get("class", "").split():
            self.routes.append(a.get("href"))


class B1P0DiscoveryCleanup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = render()

    def test_no_duplicate_hero_and_meta_introductions(self):
        page = self.html
        self.assertIn("这里有 3 家真实公司案例、6 种生意模式", page)
        self.assertIn("选个方向看看", page)
        self.assertNotIn("先看创业案例与商业模式；企业 AI 方案在独立分类里", page)
        self.assertNotIn("3 个真实公司案例和 6 种商业模式，都是研究参考，不是现成商机", page)
        self.assertNotIn("FURTHER READING / NEXT STEP", page)
        self.assertEqual(page.count('id="discover-count"'), 1)

    def test_core_search_categories_and_user_actions_stay_present(self):
        page = self.html
        parser = Links()
        parser.feed(page)
        self.assertEqual(len(parser.routes), 17)
        self.assertEqual(set(parser.routes), {row[0] for row in ENTRIES})
        self.assertEqual(PICK_COUNT, 9)
        for token in ('id="discover-query"', 'id="discover-reset" hidden',
                      'data-discover-category="founder" aria-pressed="true"',
                      'data-discover-category="solutions"',
                      'id="discover-empty"', 'href="/projects/carrd/"',
                      'href="/projects/nerdwallet/"', 'href="/discover/"'):
            # Self links do not occur in the discovery cards; discover route
            # is available through the site navigation.
            self.assertIn(token, page)
        self.assertIn("reset.hidden=category==='founder'&&!query", JS)
        self.assertIn("input.addEventListener('input'", JS)

    def test_long_risk_and_secondary_links_can_be_opened_on_demand(self):
        page = self.html
        self.assertIn('<details class="discover-notice" aria-label="资料与风险说明">', page)
        self.assertIn("公开标价不代表实际成交", page)
        self.assertIn("不保证照着做能赚钱", page)
        self.assertIn('href="/sources/"', page)
        self.assertIn('href="/validation/"', page)
        self.assertIn('<section class="g2c-related g2c-related-compact"', page)
        self.assertIn('<details><summary>还想继续比较？</summary>', page)
        self.assertNotIn('href="/solutions/"', render_related("/discover/"))
        self.assertEqual([x[0] for x in RELATED["/discover/"]],
                         ["/projects/", "/research/", "/sources/"])
        self.assertIn('aria-label="相关内容与下一步"', page)
        self.assertIn('不代表在线服务、课程或商单已开放', page)


if __name__ == "__main__":
    unittest.main()
