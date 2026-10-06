insert into data_sources
(code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,raw_storage_policy,refresh_interval_minutes,rate_limit_note)
values
('github','GitHub','https://github.com','GREEN','OFFICIAL_REST_API_PUBLIC_METADATA',true,true,'PUBLIC_METADATA_ONLY',360,'Respect API rate limits')
on conflict (code) do update set
  name=excluded.name,
  homepage_url=excluded.homepage_url,
  source_status=excluded.source_status,
  access_method=excluded.access_method,
  auto_collect=excluded.auto_collect,
  redisplay_allowed=excluded.redisplay_allowed,
  raw_storage_policy=excluded.raw_storage_policy,
  refresh_interval_minutes=excluded.refresh_interval_minutes,
  rate_limit_note=excluded.rate_limit_note,
  updated_at=now();

insert into source_policies
(source_id,policy_url,reviewed_at,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,notes)
select id,'https://docs.github.com/en/rest','2026-10-06',true,true,true,false,
       '仅采集 GitHub 官方 REST API 返回的公开仓库元数据；不采集私有仓库或用户私密数据。'
from data_sources where code='github'
and not exists (
  select 1 from source_policies p
  where p.source_id=data_sources.id and p.reviewed_at='2026-10-06'
);

create table if not exists github_discovery_queries (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  query_template text not null,
  sort_by text not null default 'stars',
  order_by text not null default 'desc',
  per_page integer not null default 50 check (per_page between 1 and 100),
  enabled boolean not null default true,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into github_discovery_queries(code,query_template,sort_by,order_by,per_page,notes)
values
('recent_breakout','created:>=__DATE_90D__ stars:>100 archived:false','stars','desc',50,'最近 90 天新仓库的突破候选'),
('ai_agents','topic:ai-agent stars:>100 archived:false','stars','desc',50,'AI Agent 主题'),
('llm','topic:llm stars:>300 archived:false','stars','desc',50,'LLM 主题'),
('saas','topic:saas stars:>50 archived:false','stars','desc',50,'SaaS 主题')
on conflict (code) do update set
  query_template=excluded.query_template,
  sort_by=excluded.sort_by,
  order_by=excluded.order_by,
  per_page=excluded.per_page,
  notes=excluded.notes,
  updated_at=now();

create table if not exists github_repositories (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references data_sources(id),
  github_repo_id bigint not null,
  full_name text not null,
  owner_login text not null,
  name text not null,
  description text,
  html_url text not null,
  homepage_url text,
  language text,
  topics jsonb not null default '[]'::jsonb,
  license_spdx text,
  archived boolean not null default false,
  is_fork boolean not null default false,
  default_branch text,
  stargazers_count bigint not null default 0,
  forks_count bigint not null default 0,
  open_issues_count bigint not null default 0,
  github_created_at timestamptz,
  github_updated_at timestamptz,
  pushed_at timestamptz,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(source_id,github_repo_id)
);
create unique index if not exists ux_github_repositories_full_name on github_repositories(full_name);
create index if not exists idx_github_repositories_stars on github_repositories(stargazers_count desc);
create index if not exists idx_github_repositories_pushed on github_repositories(pushed_at desc);

create table if not exists github_repository_snapshots (
  id bigserial primary key,
  github_repository_id uuid not null references github_repositories(id) on delete cascade,
  source_id uuid not null references data_sources(id),
  observed_at timestamptz not null,
  snapshot_hash text not null,
  stargazers_count bigint not null,
  forks_count bigint not null,
  open_issues_count bigint not null,
  pushed_at timestamptz,
  github_updated_at timestamptz,
  snapshot jsonb not null,
  created_at timestamptz not null default now(),
  unique(github_repository_id,snapshot_hash)
);
create index if not exists idx_github_snapshots_repo_time
  on github_repository_snapshots(github_repository_id,observed_at desc);
create index if not exists idx_github_snapshots_source
  on github_repository_snapshots(source_id);

create table if not exists signals (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references data_sources(id),
  entity_type text not null,
  entity_id uuid not null,
  signal_type text not null,
  signal_strength numeric(5,2) check (signal_strength between 0 and 100),
  title text not null,
  description text,
  evidence_url text,
  observed_at timestamptz not null,
  dedupe_key text not null unique,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_signals_time on signals(observed_at desc);
create index if not exists idx_signals_entity on signals(entity_type,entity_id,observed_at desc);

alter table github_discovery_queries enable row level security;
alter table github_repositories enable row level security;
alter table github_repository_snapshots enable row level security;
alter table signals enable row level security;

revoke all on github_discovery_queries,github_repositories,github_repository_snapshots,signals from anon,authenticated;
revoke all on sequence github_repository_snapshots_id_seq from anon,authenticated;
