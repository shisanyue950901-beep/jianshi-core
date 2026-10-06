alter table github_repositories
  add column if not exists owner_type text,
  add column if not exists repo_size_kb bigint,
  add column if not exists has_issues boolean,
  add column if not exists has_projects boolean;

create table if not exists github_repository_discoveries (
  github_repository_id uuid not null references github_repositories(id) on delete cascade,
  query_id uuid not null references github_discovery_queries(id) on delete cascade,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  primary key(github_repository_id,query_id)
);
create index if not exists idx_github_discoveries_query
  on github_repository_discoveries(query_id,last_seen_at desc);

alter table github_repository_discoveries enable row level security;
revoke all on github_repository_discoveries from anon,authenticated;

create or replace view github_repository_quality as
select
  r.id as github_repository_id,
  round((
    (case when nullif(btrim(coalesce(r.description,'')),'') is not null then 15 else 0 end) +
    (case when r.license_spdx is not null then 15 else 0 end) +
    (case when coalesce(r.repo_size_kb,0) >= 100 then 10 else 0 end) +
    (case when r.pushed_at >= now() - interval '30 days' then 20 else 0 end) +
    (case when r.github_created_at <= now() - interval '7 days' then 10 else 0 end) +
    (case when r.stargazers_count >= 500 then 15 else 0 end) +
    (case when r.forks_count >= 10 then 10 else 0 end) +
    (case when r.owner_type='Organization' then 5 else 0 end)
  )::numeric,2) as quality_score
from github_repositories r;

create or replace view github_hot_current as
select
  m.*,
  q.quality_score,
  round((m.heat_score * 0.80 + q.quality_score * 0.20)::numeric,2) as rank_score
from github_repository_momentum m
join github_repository_quality q using (github_repository_id)
where m.stars >= 50;

create or replace view github_rising_current as
select *
from github_hot_current
where previous_observed_at is not null
  and delta_hours between 1 and 48
  and coalesce(delta_stars,0) > 0;
