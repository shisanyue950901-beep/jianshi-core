"""Regression: header mobile menu must never inherit white article details styling."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"release"))
from p446_content_hubs import CSS as SHARED_CSS, render_pages
from f21_g2_discovery import render as render_discovery
from p448_v2_local_drafts import render_one
from f21_components import site_header


class MobileNavigationStyleRegression(unittest.TestCase):
    def test_white_disclosure_css_must_be_content_scoped(self):
        self.assertIn("main details{background:#fff;",SHARED_CSS)
        self.assertIn("main summary{cursor:pointer;",SHARED_CSS)
        self.assertIn("main details p,main details li{",SHARED_CSS)
        self.assertNotIn("\ndetails{background:#fff;",SHARED_CSS)
        self.assertNotIn("\nsummary{cursor:pointer;",SHARED_CSS)
        self.assertIn(".top .mobile{margin:0;padding:0;border:0;background:transparent;",SHARED_CSS)
        self.assertIn(".top .mobile:not([open]) > nav{display:none}",SHARED_CSS)
        self.assertIn(".top .mobile[open] summary{background:#263a5b;",SHARED_CSS)
        self.assertIn(".top .mobile > nav{z-index:40;",SHARED_CSS)

    def test_existing_navigation_semantics_and_real_contents_untouched(self):
        header=site_header("/solutions/")
        self.assertIn('<details class="mobile">',header)
        self.assertIn('aria-label="展开导航"',header)
        self.assertIn('aria-label="移动导航"',header)
        self.assertIn('href="/solutions/" aria-current="page"',header)
        pages={
            "/solutions/":render_pages()["solutions/"],
            "/discover/":render_discovery(),
            "/marketplace/brief/":render_one("marketplace/brief/"),
            "/talent/portfolio/":render_one("talent/portfolio/"),
        }
        for route,page in pages.items():
            with self.subTest(route=route):
                self.assertIn(".top .mobile:not([open]) > nav{display:none}",page)
                self.assertEqual(page.count('<details class="mobile">'),1)
                self.assertIn('class="mobile"',page)
                self.assertIn('class="top"',page)
                self.assertIn('class="footer"',page)
                self.assertIn("<main",page)
                self.assertIn("</main>",page)
                self.assertIn('class="hero',page)
                self.assertNotIn('href="/account/preview/"',page)


if __name__=="__main__":
    unittest.main()
