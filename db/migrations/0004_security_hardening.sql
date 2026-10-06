-- P0 is private-by-default. Public APIs will be added later through curated surfaces.
alter table data_sources enable row level security;
alter table source_policies enable row level security;
alter table raw_items enable row level security;
alter table companies enable row level security;
alter table products enable row level security;
alter table metric_snapshots enable row level security;
alter table opportunities enable row level security;
alter table score_snapshots enable row level security;
alter table jobs enable row level security;
alter table pipeline_runs enable row level security;
alter table audit_events enable row level security;
alter table marketplace_listings enable row level security;
alter table marketplace_listing_snapshots enable row level security;

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;

alter function enforce_source_gate() set search_path = public;
