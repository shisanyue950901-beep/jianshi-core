# R2 Empire Flippers Connector

Official endpoint:
`GET https://api.empireflippers.com/api/v1/listings/list`

Rules frozen from official documentation:
- Authentication: currently not required.
- Rate limit: no more than 1 request/second.
- Current listings may disappear for internal reasons; disappearance does not automatically mean SOLD.
- Collector therefore marks `last_seen_at`; lifecycle reconciliation is a separate step.

## Normalized fields
Price, monthly/annual profit/revenue/expenses, multiple, profit margin, MRR/churn/growth where available, country, niches, monetizations, first money date, weekly owner hours, marketplace age and seller reason.

## Data model
`marketplace_listings` = current normalized state.
`marketplace_listing_snapshots` = append-only historical states.
`raw_items` = allowed audit payload/hash, not public frontend content.
