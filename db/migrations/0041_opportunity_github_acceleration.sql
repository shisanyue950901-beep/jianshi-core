-- R8.8 Opportunity-level technical acceleration.
-- Uses existing GREEN GitHub snapshots and github_rising_current.
-- Does not change OPP_V0.2 scores or public validation semantics.

create or replace view opportunity_github_acceleration_v01 as
with mapped as (
  select distinct
    oe.opportunity_id,
    oe.entity_id as github_repository_id
  from opportunity_evidence oe
  where oe.active=true
    and oe.rule_version='OPP_V0.1'
    and oe.evidence_type='GITHUB_REPOSITORY'
),
rising as (
  select
    m.opportunity_id,
    r.github_repository_id,
    r.full_name,
    r.delta_hours,
    r.delta_stars,
    r.recent_stars_per_day,
    r.recent_velocity_score,
    r.heat_score,
    r.rank_score
  from mapped m
  join github_rising_current r
    on r.github_repository_id=m.github_repository_id
)
select
  opportunity_id,
  count(distinct github_repository_id) as rising_repo_count,
  round(coalesce(sum(recent_stars_per_day),0)::numeric,2) as recent_stars_per_day_sum,
  round(coalesce(avg(recent_stars_per_day),0)::numeric,2) as recent_stars_per_day_avg,
  round(coalesce(avg(recent_velocity_score),0)::numeric,2) as avg_recent_velocity_score,
  round(coalesce(max(recent_velocity_score),0)::numeric,2) as max_recent_velocity_score,
  round(coalesce(avg(delta_hours),0)::numeric,2) as avg_observation_window_hours
from rising
group by opportunity_id;

alter view opportunity_github_acceleration_v01 set (security_invoker=true);

create or replace view public_daily_brief_v01 as
select
  c.slug,
  c.title,
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
  c.history_days,
  c.previous_date,
  c.heat_score_1d,
  c.overall_score_1d,
  c.evidence_count_1d,
  c.seven_day_date,
  c.heat_score_7d,
  c.overall_score_7d,
  c.evidence_count_7d,
  c.heat_delta_1d,
  c.overall_delta_1d,
  c.evidence_delta_1d,
  c.heat_delta_7d,
  c.overall_delta_7d,
  c.evidence_delta_7d,
  c.change_state,
  c.change_summary_zh,
  row_number() over (
    order by
      case
        when c.change_state='NEWLY_VALIDATED' then 0
        when c.change_state='EVIDENCE_ACCELERATING' then 1
        when c.change_state='RISING' then 2
        else 3
      end,
      coalesce(c.heat_delta_1d,0) desc,
      coalesce(a.rising_repo_count,0) desc,
      coalesce(a.max_recent_velocity_score,0) desc,
      c.heat_score desc
  ) as rising_rank,
  row_number() over (
    order by c.public_ready desc,c.build_score desc,c.business_score desc
  ) as build_rank,
  row_number() over (
    order by c.content_score desc,c.heat_score desc
  ) as content_rank,
  row_number() over (
    order by c.public_ready desc,c.overall_score desc
  ) as overall_rank,
  coalesce(a.rising_repo_count,0) as rising_repo_count,
  coalesce(a.recent_stars_per_day_sum,0) as recent_stars_per_day_sum,
  coalesce(a.recent_stars_per_day_avg,0) as recent_stars_per_day_avg,
  coalesce(a.avg_recent_velocity_score,0) as avg_recent_velocity_score,
  coalesce(a.max_recent_velocity_score,0) as max_recent_velocity_score
from public_opportunity_changes_v01 c
left join opportunities o on o.slug=c.slug
left join opportunity_github_acceleration_v01 a
  on a.opportunity_id=o.id;

alter view public_daily_brief_v01 set (security_invoker=true);

comment on view opportunity_github_acceleration_v01 is
'R8.8 explainability layer: current 1-48h positive GitHub star momentum aggregated to opportunity level. Does not alter OPP_V0.2.';
comment on view public_daily_brief_v01 is
'R8.8 rising rank keeps real daily change primary, then uses current GitHub acceleration as a tie-breaker.';
