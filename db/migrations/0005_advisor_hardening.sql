create schema if not exists extensions;
alter extension pg_trgm set schema extensions;

create index if not exists idx_marketplace_snapshots_source_id
  on marketplace_listing_snapshots(source_id);
create index if not exists idx_metric_snapshots_source_id
  on metric_snapshots(source_id);
create index if not exists idx_pipeline_runs_source_id
  on pipeline_runs(source_id);
create index if not exists idx_products_company_id
  on products(company_id);

comment on table data_sources is
'Private-by-default P0 table. RLS intentionally has no user policies and grants to anon/authenticated are revoked.';
