create or replace view github_repository_momentum as
with ranked as (
  select
    s.*,
    row_number() over (
      partition by s.github_repository_id
      order by s.observed_at desc, s.id desc
    ) as rn
  from github_repository_snapshots s
),
latest as (
  select * from ranked where rn=1
),
previous as (
  select * from ranked where rn=2
),
base as (
  select
    r.id as github_repository_id,
    r.full_name,
    r.description,
    r.html_url,
    r.language,
    r.topics,
    r.license_spdx,
    r.archived,
    r.is_fork,
    r.github_created_at,
    r.pushed_at,
    l.observed_at as latest_observed_at,
    l.snapshot_hash as latest_snapshot_hash,
    l.stargazers_count as stars,
    l.forks_count as forks,
    l.open_issues_count as open_issues,
    p.observed_at as previous_observed_at,
    p.stargazers_count as previous_stars,
    greatest(
      1.0,
      extract(epoch from (now() - coalesce(r.github_created_at, now()))) / 86400.0
    ) as age_days,
    greatest(
      0.0,
      extract(epoch from (now() - coalesce(r.pushed_at, now()))) / 86400.0
    ) as push_age_days,
    case
      when p.observed_at is not null and l.observed_at > p.observed_at
      then extract(epoch from (l.observed_at - p.observed_at)) / 3600.0
      else null
    end as delta_hours,
    case
      when p.stargazers_count is not null
      then l.stargazers_count - p.stargazers_count
      else null
    end as delta_stars
  from github_repositories r
  join latest l on l.github_repository_id=r.id
  left join previous p on p.github_repository_id=r.id
),
components as (
  select
    b.*,
    least(100.0, greatest(0.0,
      100.0 * ln(stars + 1.0) / ln(100000.0 + 1.0)
    )) as popularity_score,
    least(100.0, greatest(0.0,
      100.0 * ln((stars / greatest(age_days,7.0)) + 1.0) / ln(1000.0 + 1.0)
    )) as lifetime_velocity_score,
    greatest(0.0, 100.0 - least(100.0, push_age_days * 5.0)) as freshness_score,
    greatest(0.0, 100.0 - least(100.0, age_days / 1.8)) as recency_score,
    least(100.0, greatest(0.0,
      case when stars > 0 then (forks::numeric / stars::numeric) * 500.0 else 0.0 end
    )) as fork_score,
    case
      when delta_hours is not null and delta_hours > 0
      then greatest(0.0, coalesce(delta_stars,0)::numeric * 24.0 / delta_hours)
      else null
    end as recent_stars_per_day
  from base b
),
scored as (
  select
    c.*,
    (
      popularity_score * 0.25 +
      lifetime_velocity_score * 0.35 +
      freshness_score * 0.20 +
      recency_score * 0.10 +
      fork_score * 0.10
    ) as static_heat_score,
    case
      when recent_stars_per_day is not null
      then least(100.0, greatest(0.0,
        100.0 * ln(recent_stars_per_day + 1.0) / ln(1000.0 + 1.0)
      ))
      else null
    end as recent_velocity_score
  from components c
)
select
  github_repository_id,
  full_name,
  description,
  html_url,
  language,
  topics,
  license_spdx,
  github_created_at,
  pushed_at,
  latest_observed_at,
  latest_snapshot_hash,
  stars,
  forks,
  open_issues,
  previous_observed_at,
  previous_stars,
  delta_hours,
  delta_stars,
  recent_stars_per_day,
  round(popularity_score::numeric,2) as popularity_score,
  round(lifetime_velocity_score::numeric,2) as lifetime_velocity_score,
  round(freshness_score::numeric,2) as freshness_score,
  round(recency_score::numeric,2) as recency_score,
  round(fork_score::numeric,2) as fork_score,
  round(static_heat_score::numeric,2) as static_heat_score,
  round(coalesce(recent_velocity_score,0)::numeric,2) as recent_velocity_score,
  round((
    case
      when recent_velocity_score is not null
      then static_heat_score * 0.55 + recent_velocity_score * 0.45
      else static_heat_score
    end
  )::numeric,2) as heat_score
from scored
where archived=false and is_fork=false;

create or replace view github_rising_current as
select *
from github_repository_momentum
where stars >= 50;

create or replace function refresh_github_momentum_signals()
returns integer
language plpgsql
security definer
set search_path=public
as $$
declare
  inserted_count integer;
begin
  insert into signals(
    source_id,entity_type,entity_id,signal_type,signal_strength,
    title,description,evidence_url,observed_at,dedupe_key,metadata
  )
  select
    ds.id,
    'GITHUB_REPOSITORY',
    m.github_repository_id,
    'GITHUB_FAST_GROWTH',
    least(100.0, 50.0 + coalesce(m.recent_velocity_score,0) * 0.5),
    'GitHub 快速增长：' || m.full_name,
    '最新观测窗口 Star 增长 ' || coalesce(m.delta_stars,0)::text ||
      '，折算约 ' || round(coalesce(m.recent_stars_per_day,0)::numeric,1)::text || ' Star/天。',
    m.html_url,
    m.latest_observed_at,
    'github_fast_growth:' || m.github_repository_id::text || ':' || m.latest_snapshot_hash,
    jsonb_build_object(
      'delta_stars',m.delta_stars,
      'delta_hours',m.delta_hours,
      'recent_stars_per_day',m.recent_stars_per_day,
      'heat_score',m.heat_score
    )
  from github_repository_momentum m
  join data_sources ds on ds.code='github'
  where m.previous_observed_at is not null
    and m.delta_hours between 0.05 and 48
    and coalesce(m.delta_stars,0) >= greatest(10, ceil(coalesce(m.previous_stars,0) * 0.005))
  on conflict (dedupe_key) do nothing;

  get diagnostics inserted_count = row_count;
  return inserted_count;
end;
$$;

revoke all on function refresh_github_momentum_signals() from public,anon,authenticated;
