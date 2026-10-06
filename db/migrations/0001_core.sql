create extension if not exists pgcrypto;
create extension if not exists pg_trgm;

do $$ begin
  create type source_status as enum ('GREEN','YELLOW','RED','DISABLED');
exception when duplicate_object then null; end $$;

do $$ begin
  create type job_status as enum ('PENDING','RUNNING','SUCCESS','FAILED','DEAD');
exception when duplicate_object then null; end $$;

do $$ begin
  create type entity_kind as enum ('COMPANY','PRODUCT');
exception when duplicate_object then null; end $$;

do $$ begin
  create type score_kind as enum ('HEAT','CONTENT','BUILD','BUSINESS');
exception when duplicate_object then null; end $$;

do $$ begin
  create type opportunity_status as enum ('CANDIDATE','ACTIVE','WATCH','ARCHIVED');
exception when duplicate_object then null; end $$;

create table if not exists data_sources (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  homepage_url text,
  source_status source_status not null default 'YELLOW',
  access_method text not null,
  auto_collect boolean not null default false,
  redisplay_allowed boolean not null default false,
  raw_storage_policy text,
  refresh_interval_minutes integer,
  rate_limit_note text,
  last_success_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists source_policies (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references data_sources(id) on delete cascade,
  policy_url text,
  reviewed_at timestamptz not null,
  commercial_use_allowed boolean,
  automated_collection_allowed boolean not null default false,
  redisplay_allowed boolean not null default false,
  fulltext_storage_allowed boolean not null default false,
  notes text,
  evidence_hash text,
  created_at timestamptz not null default now()
);
create index if not exists idx_source_policies_source_reviewed on source_policies(source_id, reviewed_at desc);

create table if not exists raw_items (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references data_sources(id),
  source_external_id text,
  source_url text,
  fetched_at timestamptz not null,
  title text,
  summary text,
  allowed_payload jsonb,
  object_storage_path text,
  content_hash text not null,
  parser_version text not null,
  http_status integer,
  created_at timestamptz not null default now(),
  unique(source_id, content_hash)
);
create index if not exists idx_raw_items_source_fetched on raw_items(source_id, fetched_at desc);

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  canonical_url text,
  country_code text,
  founded_at date,
  team_size integer,
  founder_count integer,
  status text not null default 'ACTIVE',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists ux_companies_canonical_url on companies(canonical_url) where canonical_url is not null;

create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references companies(id) on delete set null,
  name text not null,
  slug text not null unique,
  canonical_url text,
  description text,
  logo_url text,
  founded_at date,
  country_code text,
  pricing_model text,
  business_model text,
  ai_category text,
  status text not null default 'ACTIVE',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists ux_products_canonical_url on products(canonical_url) where canonical_url is not null;
create index if not exists idx_products_name_trgm on products using gin (name gin_trgm_ops);

create table if not exists metric_snapshots (
  id bigserial primary key,
  entity_kind entity_kind not null,
  entity_id uuid not null,
  metric_type text not null,
  numeric_value numeric,
  text_value text,
  unit text,
  source_id uuid references data_sources(id),
  observed_at timestamptz not null,
  evidence_url text,
  created_at timestamptz not null default now()
);
create index if not exists idx_metric_entity_time on metric_snapshots(entity_kind, entity_id, metric_type, observed_at desc);

create table if not exists opportunities (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  title text not null,
  category text,
  thesis text,
  problem text,
  target_customer text,
  business_model text,
  china_fit numeric(5,2) check (china_fit between 0 and 100),
  solo_founder_fit numeric(5,2) check (solo_founder_fit between 0 and 100),
  status opportunity_status not null default 'CANDIDATE',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists score_snapshots (
  id bigserial primary key,
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  score_kind score_kind not null,
  score numeric(5,2) not null check (score between 0 and 100),
  score_version text not null,
  reason_json jsonb not null default '{}'::jsonb,
  calculated_at timestamptz not null default now()
);
create index if not exists idx_scores_latest on score_snapshots(opportunity_id, score_kind, calculated_at desc);

create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  job_type text not null,
  status job_status not null default 'PENDING',
  payload jsonb not null default '{}'::jsonb,
  attempts integer not null default 0,
  max_attempts integer not null default 3,
  next_retry_at timestamptz,
  locked_by text,
  locked_at timestamptz,
  started_at timestamptz,
  finished_at timestamptz,
  error_text text,
  created_at timestamptz not null default now()
);
create index if not exists idx_jobs_pick on jobs(status, next_retry_at, created_at);

create table if not exists pipeline_runs (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references data_sources(id),
  run_type text not null,
  status text not null,
  started_at timestamptz not null,
  finished_at timestamptz,
  fetched_count integer not null default 0,
  accepted_count integer not null default 0,
  duplicate_count integer not null default 0,
  parser_error_count integer not null default 0,
  forbidden_source_attempt_count integer not null default 0,
  quality_gate_status text,
  quality_gate_reason jsonb,
  created_at timestamptz not null default now()
);

create table if not exists audit_events (
  id bigserial primary key,
  actor_type text not null,
  actor_id text,
  action text not null,
  entity_type text,
  entity_id text,
  before_json jsonb,
  after_json jsonb,
  source text,
  created_at timestamptz not null default now()
);

create or replace function enforce_source_gate()
returns trigger language plpgsql as $$
begin
  if new.auto_collect and new.source_status <> 'GREEN' then
    raise exception 'AUTO_COLLECT_FORBIDDEN_FOR_NON_GREEN_SOURCE: %', new.code;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_source_gate on data_sources;
create trigger trg_source_gate
before insert or update on data_sources
for each row execute function enforce_source_gate();

create or replace view latest_scores as
select distinct on (opportunity_id, score_kind)
  opportunity_id, score_kind, score, score_version, reason_json, calculated_at
from score_snapshots
order by opportunity_id, score_kind, calculated_at desc, id desc;
