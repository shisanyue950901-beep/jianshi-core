create table if not exists opportunity_daily_snapshots (
  id bigserial primary key,
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  snapshot_date date not null,
  observed_at timestamptz not null default now(),
  heat_score numeric(5,2),
  content_score numeric(5,2),
  build_score numeric(5,2),
  business_score numeric(5,2),
  overall_score numeric(5,2),
  evidence_count integer not null default 0,
  source_count integer not null default 0,
  github_repo_count integer not null default 0,
  market_listing_count integer not null default 0,
  public_ready boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(opportunity_id,snapshot_date)
);

create index if not exists idx_opportunity_daily_date
  on opportunity_daily_snapshots(snapshot_date desc);
create index if not exists idx_opportunity_daily_opp_date
  on opportunity_daily_snapshots(opportunity_id,snapshot_date desc);

alter table opportunity_daily_snapshots enable row level security;
revoke all on opportunity_daily_snapshots from anon,authenticated;
revoke all on sequence opportunity_daily_snapshots_id_seq from anon,authenticated;

create or replace function refresh_opportunity_daily_snapshots_v01()
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  snapshot_day date := (now() at time zone 'Asia/Shanghai')::date;
  affected integer;
begin
  insert into opportunity_daily_snapshots(
    opportunity_id,snapshot_date,observed_at,
    heat_score,content_score,build_score,business_score,overall_score,
    evidence_count,source_count,github_repo_count,market_listing_count,public_ready,
    updated_at
  )
  select
    r.opportunity_id,
    snapshot_day,
    now(),
    r.heat_score,
    r.content_score,
    r.build_score,
    r.business_score,
    round((
      coalesce(r.heat_score,0) * 0.30 +
      coalesce(r.content_score,0) * 0.20 +
      coalesce(r.build_score,0) * 0.25 +
      coalesce(r.business_score,0) * 0.25
    )::numeric,2),
    r.evidence_count,
    r.source_count,
    r.github_repo_count,
    r.market_listing_count,
    r.public_ready,
    now()
  from opportunity_rank_current r
  on conflict (opportunity_id,snapshot_date)
  do update set
    observed_at=excluded.observed_at,
    heat_score=excluded.heat_score,
    content_score=excluded.content_score,
    build_score=excluded.build_score,
    business_score=excluded.business_score,
    overall_score=excluded.overall_score,
    evidence_count=excluded.evidence_count,
    source_count=excluded.source_count,
    github_repo_count=excluded.github_repo_count,
    market_listing_count=excluded.market_listing_count,
    public_ready=excluded.public_ready,
    updated_at=now();

  get diagnostics affected = row_count;

  return jsonb_build_object(
    'snapshot_date',snapshot_day,
    'opportunities',affected
  );
end;
$$;

revoke all on function refresh_opportunity_daily_snapshots_v01() from public,anon,authenticated;

-- Seed today's snapshot immediately so R7 can start accumulating history from deployment day.
select refresh_opportunity_daily_snapshots_v01();

drop view if exists public_opportunity_changes_v01;
create view public_opportunity_changes_v01 as
with latest_day as (
  select max(snapshot_date) as snapshot_date
  from opportunity_daily_snapshots
),
current_rows as (
  select s.*
  from opportunity_daily_snapshots s
  join latest_day d on d.snapshot_date=s.snapshot_date
),
history_counts as (
  select opportunity_id,count(distinct snapshot_date) as history_days
  from opportunity_daily_snapshots
  group by opportunity_id
)
select
  o.slug,
  o.title,
  c.snapshot_date,
  c.observed_at,
  c.heat_score,
  c.content_score,
  c.build_score,
  c.business_score,
  c.overall_score,
  c.evidence_count,
  c.source_count,
  c.github_repo_count,
  c.market_listing_count,
  c.public_ready,
  hc.history_days,
  p1.snapshot_date as previous_date,
  p1.heat_score as heat_score_1d,
  p1.overall_score as overall_score_1d,
  p1.evidence_count as evidence_count_1d,
  p7.snapshot_date as seven_day_date,
  p7.heat_score as heat_score_7d,
  p7.overall_score as overall_score_7d,
  p7.evidence_count as evidence_count_7d,
  case when p1.id is null then null else round((c.heat_score-p1.heat_score)::numeric,2) end as heat_delta_1d,
  case when p1.id is null then null else round((c.overall_score-p1.overall_score)::numeric,2) end as overall_delta_1d,
  case when p1.id is null then null else c.evidence_count-p1.evidence_count end as evidence_delta_1d,
  case when p7.id is null then null else round((c.heat_score-p7.heat_score)::numeric,2) end as heat_delta_7d,
  case when p7.id is null then null else round((c.overall_score-p7.overall_score)::numeric,2) end as overall_delta_7d,
  case when p7.id is null then null else c.evidence_count-p7.evidence_count end as evidence_delta_7d,
  case
    when p1.id is null then 'ACCUMULATING'
    when c.public_ready and not p1.public_ready then 'NEWLY_VALIDATED'
    when (c.evidence_count-p1.evidence_count) >= 5 then 'EVIDENCE_ACCELERATING'
    when (c.heat_score-p1.heat_score) >= 3 then 'RISING'
    when (c.heat_score-p1.heat_score) <= -3 then 'COOLING'
    else 'STABLE'
  end as change_state,
  case
    when p1.id is null then '历史数据正在积累，明天开始显示与昨日变化。'
    when c.public_ready and not p1.public_ready then '今天首次通过多源验证，已从持续观察升级为已验证机会。'
    when (c.evidence_count-p1.evidence_count) >= 5 then '今天新增了较多有效证据，值得重新评估。'
    when (c.heat_score-p1.heat_score) >= 3 then '今天趋势热度明显上升。'
    when (c.heat_score-p1.heat_score) <= -3 then '今天趋势热度有所回落。'
    else '今天整体变化不大，继续观察。'
  end as change_summary_zh
from current_rows c
join opportunities o on o.id=c.opportunity_id
join history_counts hc on hc.opportunity_id=c.opportunity_id
left join opportunity_daily_snapshots p1
  on p1.opportunity_id=c.opportunity_id
 and p1.snapshot_date=c.snapshot_date-1
left join opportunity_daily_snapshots p7
  on p7.opportunity_id=c.opportunity_id
 and p7.snapshot_date=c.snapshot_date-7;

alter view public_opportunity_changes_v01 set (security_invoker=true);

drop view if exists public_daily_brief_v01;
create view public_daily_brief_v01 as
select
  c.*,
  row_number() over (
    order by
      case when c.change_state='NEWLY_VALIDATED' then 0
           when c.change_state='EVIDENCE_ACCELERATING' then 1
           when c.change_state='RISING' then 2
           else 3 end,
      coalesce(c.heat_delta_1d,0) desc,
      c.heat_score desc
  ) as rising_rank,
  row_number() over (order by c.build_score desc,c.business_score desc) as build_rank,
  row_number() over (order by c.content_score desc,c.heat_score desc) as content_rank,
  row_number() over (order by c.overall_score desc) as overall_rank
from public_opportunity_changes_v01 c;

alter view public_daily_brief_v01 set (security_invoker=true);

comment on table opportunity_daily_snapshots is
'R7 daily opportunity state, one row per opportunity per China calendar day; updated by each 6h refresh.';
comment on view public_opportunity_changes_v01 is
'R7 public day-over-day and 7-day change projection. Null deltas mean history is not yet available and must not be fabricated.';
