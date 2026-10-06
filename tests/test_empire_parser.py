import json, sys, unittest
from pathlib import Path
sys.path.insert(0, "src")
from jianshi.collectors.empire_flippers import normalize, parse_page, snapshot_hash

class TestEmpireParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(Path("fixtures/empire_flippers_live_sample.json").read_text(encoding="utf-8"))
    def test_parse(self):
        rows = parse_page(self.payload)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].listing_number, 97090)
        self.assertEqual(rows[0].monetizations, ["Amazon FBA","eCommerce"])
        self.assertEqual(rows[1].annual_listing_multiple, 3.6)
    def test_hash_stable(self):
        row = parse_page(self.payload)[0]
        self.assertEqual(snapshot_hash(row), snapshot_hash(row))
        self.assertEqual(len(snapshot_hash(row)), 64)

    def test_sold_listing_is_not_active(self):
        row = normalize({
            "id":"sold-fixture",
            "listing_number":99999,
            "listing_status":"Sold",
            "monetizations":[{"monetization":"SaaS"}],
            "niches":[{"niche":"Business"}],
        })
        self.assertEqual(row.listing_status,"Sold")
        self.assertFalse(row.active)

if __name__ == "__main__": unittest.main()
