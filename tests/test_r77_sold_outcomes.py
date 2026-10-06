import unittest
from pathlib import Path

class TestR77SoldOutcomes(unittest.TestCase):
    def test_sold_outcome_schema(self):
        sql=Path("db/migrations/0026_marketplace_sold_outcomes.sql").read_text(encoding="utf-8")
        for token in [
            "marketplace_listing_status_events",
            "first_observed_sold_at",
            "last_asking_price_before_sold",
            "last_asking_annual_multiple_before_sold",
            "marketplace_observed_exits_v01",
            "marketplace_exit_benchmarks_v01",
            "For Sale",
            "Sold",
        ]:
            self.assertIn(token,sql)
        self.assertIn("NOT a transaction price",sql)

    def test_collector_fetches_recent_sold_without_claiming_sale_price(self):
        fn=Path("supabase/functions/collect-empire-flippers/index.ts").read_text(encoding="utf-8")
        self.assertIn('collectStatus("For Sale"',fn)
        self.assertIn('collectStatus("Sold"',fn)
        self.assertIn("sold_at_from",fn)
        self.assertIn("sold_lookback_days",fn)
        self.assertIn("sold_values_are_observed_status_not_transaction_price",fn)
        self.assertNotIn("sale_price:",fn)

if __name__=="__main__":
    unittest.main()
