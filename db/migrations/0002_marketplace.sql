-- Marketplace listing is intentionally separate from product/company identity.
-- A broker listing may be anonymous and should not be forced into products.
create table if not exists marketplace_listings (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references data_sources(id),
  source_external_id text not null,
  listing_number bigint,
  public_title text,
  listing_status text,
  listing_price numeric,
  unpriced boolean not null default false,
  average_monthly_net_profit numeric,
  average_monthly_expenses numeric,
  average_monthly_gross_revenue numeric,
  average_annual_net_profit numeric,
  average_annual_expenses numeric,
  average_annual_gross_revenue numeric,
  listing_multiple numeric,
  annual_listing_multiple numeric,
  listing_multiple_type text,
  profit_margin numeric,
  mrr numeric,
  churn_percent numeric,
  growth_percent numeric,
  hours_worked_per_week numeric,
  days_on_marketplace integer,
  country_code text,
  countries jsonb not null default '[]'::jsonb,
  monetizations jsonb not null default '[]'::jsonb,
  niches jsonb not null default '[]'::jsonb,
  first_made_money_at date,
  first_listed_at timestamptz,
  reason_for_sale text,
  source_updated_at timestamptz,
  source_url text,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(source_id, source_external_id)
);
create index if not exists idx_marketplace_status on marketplace_listings(listing_status, active);
create index if not exists idx_marketplace_source_number on marketplace_listings(source_id, listing_number);

-- APPEND-ONLY history. Never UPDATE/DELETE in normal collector operation.
create table if not exists marketplace_listing_snapshots (
  id bigserial primary key,
  marketplace_listing_id uuid not null references marketplace_listings(id) on delete cascade,
  source_id uuid not null references data_sources(id),
  observed_at timestamptz not null,
  snapshot_hash text not null,
  snapshot jsonb not null,
  created_at timestamptz not null default now(),
  unique(marketplace_listing_id, snapshot_hash)
);
create index if not exists idx_marketplace_snapshot_time on marketplace_listing_snapshots(marketplace_listing_id, observed_at desc);

create or replace view marketplace_current_for_sale as
select * from marketplace_listings
where active = true and listing_status = 'For Sale';
