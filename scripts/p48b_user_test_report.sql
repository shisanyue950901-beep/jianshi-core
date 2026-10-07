-- P4.8B controlled real-user test report.
-- READ ONLY. No DDL / DML. Run against Production after P4.8A deployment.
-- Epoch starts after the P4.8A static snapshot was live and internally accepted.
--
-- Frozen interpretation:
-- - Project sample size = distinct sessions with OPPORTUNITY_DETAIL_VIEW on one of the six target slugs.
-- - Do not redesign from this report before >= 30 target detail sessions.
-- - Entry click rate denominator = sessions that viewed / or /opportunities/.
-- - Second-project rate = target detail sessions that viewed >= 2 distinct target project slugs.
-- - All rates are session-based to avoid one heavy reader dominating the result.

with
params as (
  select
    timestamptz '2026-10-07T15:49:06Z' as epoch_start,
    30::integer as minimum_detail_sessions_before_decision
),
target_slugs(slug) as (
  values
    ('vertical-industry-saas'),
    ('amazon-fba-niche-brand'),
    ('digital-product-business'),
    ('affiliate-content-site'),
    ('amazon-kdp-publishing'),
    ('agency-business')
),
epoch_events as (
  select e.*
  from behavior_events e
  cross join params p
  where e.received_at >= p.epoch_start
),
target_events as (
  select e.*
  from epoch_events e
  join target_slugs t on t.slug=e.opportunity_slug
),
eligible_entry_sessions as (
  select distinct session_id
  from epoch_events
  where event_type='PAGE_VIEW'
    and page_path in ('/','/opportunities/')
),
entry_click_sessions as (
  select distinct session_id
  from target_events
  where event_type='OPPORTUNITY_CARD_CLICK'
    and page_path in ('/','/opportunities/')
),
target_detail_sessions as (
  select distinct session_id
  from target_events
  where event_type='OPPORTUNITY_DETAIL_VIEW'
),
target_session_rollup as (
  select
    d.session_id,
    count(distinct e.opportunity_slug) filter (
      where e.event_type='OPPORTUNITY_DETAIL_VIEW'
    ) as distinct_target_projects_viewed,
    bool_or(e.event_type='ENGAGED_30S') as engaged_30s,
    bool_or(e.event_type='SCROLL_90') as scroll_90
  from target_detail_sessions d
  join target_events e using(session_id)
  group by d.session_id
),
target_first_detail as (
  select distinct on (session_id)
    session_id,
    visitor_id,
    opportunity_slug,
    device_class,
    referrer_domain,
    utm_source,
    utm_medium,
    utm_campaign,
    received_at
  from target_events
  where event_type='OPPORTUNITY_DETAIL_VIEW'
  order by session_id,received_at
),
per_project as (
  select
    t.slug,
    count(distinct e.session_id) filter (
      where e.event_type='OPPORTUNITY_DETAIL_VIEW'
    ) as detail_sessions,
    count(distinct e.visitor_id) filter (
      where e.event_type='OPPORTUNITY_DETAIL_VIEW'
    ) as detail_visitors,
    count(distinct e.session_id) filter (
      where e.event_type='ENGAGED_30S'
    ) as engaged_30s_sessions,
    count(distinct e.session_id) filter (
      where e.event_type='SCROLL_90'
    ) as scroll_90_sessions
  from target_slugs t
  left join target_events e on e.opportunity_slug=t.slug
  group by t.slug
),
entry_source as (
  select
    page_path,
    count(distinct session_id) as click_sessions
  from target_events
  where event_type='OPPORTUNITY_CARD_CLICK'
  group by page_path
),
device_mix as (
  select device_class,count(*) as detail_sessions
  from target_first_detail
  group by device_class
),
acquisition_mix as (
  select
    coalesce(nullif(utm_source,''),'(none)') as utm_source,
    coalesce(nullif(utm_medium,''),'(none)') as utm_medium,
    coalesce(nullif(utm_campaign,''),'(none)') as utm_campaign,
    coalesce(nullif(referrer_domain,''),'(direct/unknown)') as referrer_domain,
    count(*) as detail_sessions
  from target_first_detail
  group by 1,2,3,4
),
summary_values as (
  select
    (select count(distinct visitor_id) from epoch_events) as epoch_unique_visitors,
    (select count(distinct session_id) from epoch_events) as epoch_sessions,
    (select count(*) from eligible_entry_sessions) as eligible_entry_sessions,
    (select count(*) from entry_click_sessions) as entry_click_sessions,
    (select count(*) from target_detail_sessions) as target_detail_sessions,
    (select count(*) from target_session_rollup where engaged_30s) as engaged_30s_sessions,
    (select count(*) from target_session_rollup where scroll_90) as scroll_90_sessions,
    (select count(*) from target_session_rollup where distinct_target_projects_viewed>=2) as second_target_project_sessions,
    (
      select count(*)
      from target_detail_sessions d
      where not exists (
        select 1
        from target_events c
        where c.session_id=d.session_id
          and c.event_type='OPPORTUNITY_CARD_CLICK'
      )
    ) as direct_or_untracked_detail_sessions
)
select jsonb_build_object(
  'meta',jsonb_build_object(
    'report_version','P4.8B-V1',
    'epoch_start',(select epoch_start from params),
    'minimum_detail_sessions_before_decision',(select minimum_detail_sessions_before_decision from params),
    'target_project_count',(select count(*) from target_slugs),
    'decision_state',case
      when (select target_detail_sessions from summary_values) >=
           (select minimum_detail_sessions_before_decision from params)
      then 'ENOUGH_FOR_FIRST_REVIEW'
      else 'ACCUMULATING'
    end
  ),
  'summary',(
    select jsonb_build_object(
      'epoch_unique_visitors',epoch_unique_visitors,
      'epoch_sessions',epoch_sessions,
      'eligible_entry_sessions',eligible_entry_sessions,
      'entry_click_sessions',entry_click_sessions,
      'entry_click_rate_pct',case when eligible_entry_sessions=0 then null
        else round((100.0*entry_click_sessions/eligible_entry_sessions)::numeric,2) end,
      'target_detail_sessions',target_detail_sessions,
      'engaged_30s_sessions',engaged_30s_sessions,
      'engaged_30s_rate_pct',case when target_detail_sessions=0 then null
        else round((100.0*engaged_30s_sessions/target_detail_sessions)::numeric,2) end,
      'scroll_90_sessions',scroll_90_sessions,
      'scroll_90_rate_pct',case when target_detail_sessions=0 then null
        else round((100.0*scroll_90_sessions/target_detail_sessions)::numeric,2) end,
      'second_target_project_sessions',second_target_project_sessions,
      'second_target_project_rate_pct',case when target_detail_sessions=0 then null
        else round((100.0*second_target_project_sessions/target_detail_sessions)::numeric,2) end,
      'direct_or_untracked_detail_sessions',direct_or_untracked_detail_sessions
    )
    from summary_values
  ),
  'per_project',coalesce((
    select jsonb_agg(
      jsonb_build_object(
        'slug',slug,
        'detail_sessions',detail_sessions,
        'detail_visitors',detail_visitors,
        'engaged_30s_sessions',engaged_30s_sessions,
        'engaged_30s_rate_pct',case when detail_sessions=0 then null
          else round((100.0*engaged_30s_sessions/detail_sessions)::numeric,2) end,
        'scroll_90_sessions',scroll_90_sessions,
        'scroll_90_rate_pct',case when detail_sessions=0 then null
          else round((100.0*scroll_90_sessions/detail_sessions)::numeric,2) end
      )
      order by detail_sessions desc,slug
    )
    from per_project
  ),'[]'::jsonb),
  'entry_sources',coalesce((
    select jsonb_agg(
      jsonb_build_object('page_path',page_path,'click_sessions',click_sessions)
      order by click_sessions desc,page_path
    )
    from entry_source
  ),'[]'::jsonb),
  'device_mix',coalesce((
    select jsonb_agg(
      jsonb_build_object('device_class',device_class,'detail_sessions',detail_sessions)
      order by detail_sessions desc,device_class
    )
    from device_mix
  ),'[]'::jsonb),
  'acquisition_mix',coalesce((
    select jsonb_agg(
      jsonb_build_object(
        'utm_source',utm_source,
        'utm_medium',utm_medium,
        'utm_campaign',utm_campaign,
        'referrer_domain',referrer_domain,
        'detail_sessions',detail_sessions
      )
      order by detail_sessions desc,utm_source,referrer_domain
    )
    from acquisition_mix
  ),'[]'::jsonb)
) as p48b_user_test_report;
