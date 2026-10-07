-- P4.3 First-party anonymous behavior analytics.
-- Purpose: validate real product usage without third-party ad trackers.
-- Privacy: no email/name/IP/user-agent/full search text is persisted.
-- Auth, OPP_V0.2, public_ready and source policy remain unchanged.

create table if not exists behavior_events (
  event_id uuid primary key,
  visitor_id uuid not null,
  session_id uuid not null,
  event_type text not null check (event_type in (
    'PAGE_VIEW',
    'OPPORTUNITY_CARD_CLICK',
    'OPPORTUNITY_DETAIL_VIEW',
    'SECOND_OPPORTUNITY_VIEW',
    'CATALOG_SEARCH',
    'CATALOG_FILTER',
    'SOURCE_OUTBOUND_CLICK',
    'ENGAGED_30S',
    'SCROLL_50',
    'SCROLL_90'
  )),
  page_path text not null
    check (char_length(page_path) between 1 and 200 and page_path like '/%'),
  opportunity_slug text
    check (opportunity_slug is null or opportunity_slug ~ '^[a-z0-9-]{2,80}$'),
  referrer_domain text
    check (referrer_domain is null or char_length(referrer_domain) <= 253),
  utm_source text check (utm_source is null or char_length(utm_source) <= 80),
  utm_medium text check (utm_medium is null or char_length(utm_medium) <= 80),
  utm_campaign text check (utm_campaign is null or char_length(utm_campaign) <= 80),
  device_class text not null default 'UNKNOWN'
    check (device_class in ('MOBILE','TABLET','DESKTOP','UNKNOWN')),
  metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(metadata)='object' and octet_length(metadata::text) <= 2048),
  received_at timestamptz not null default now()
);

create index if not exists idx_behavior_events_received
  on behavior_events(received_at desc);
create index if not exists idx_behavior_events_type_time
  on behavior_events(event_type,received_at desc);
create index if not exists idx_behavior_events_visitor_time
  on behavior_events(visitor_id,received_at desc);
create index if not exists idx_behavior_events_session_time
  on behavior_events(session_id,received_at desc);
create index if not exists idx_behavior_events_opportunity_time
  on behavior_events(opportunity_slug,received_at desc)
  where opportunity_slug is not null;

alter table behavior_events enable row level security;
revoke all on behavior_events from public,anon,authenticated;
grant select,insert,delete on behavior_events to service_role;

create or replace function record_behavior_event_v01(
  p_event_id uuid,
  p_visitor_id uuid,
  p_session_id uuid,
  p_event_type text,
  p_page_path text,
  p_opportunity_slug text default null,
  p_referrer_domain text default null,
  p_utm_source text default null,
  p_utm_medium text default null,
  p_utm_campaign text default null,
  p_device_class text default 'UNKNOWN',
  p_metadata jsonb default '{}'::jsonb
)
returns text
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  recent_count integer;
  inserted_count integer;
begin
  if p_event_type not in (
    'PAGE_VIEW','OPPORTUNITY_CARD_CLICK','OPPORTUNITY_DETAIL_VIEW',
    'SECOND_OPPORTUNITY_VIEW','CATALOG_SEARCH','CATALOG_FILTER',
    'SOURCE_OUTBOUND_CLICK','ENGAGED_30S','SCROLL_50','SCROLL_90'
  ) then
    raise exception 'INVALID_EVENT_TYPE';
  end if;

  if p_page_path is null
     or char_length(p_page_path) < 1
     or char_length(p_page_path) > 200
     or p_page_path not like '/%' then
    raise exception 'INVALID_PAGE_PATH';
  end if;

  if p_opportunity_slug is not null
     and p_opportunity_slug !~ '^[a-z0-9-]{2,80}$' then
    raise exception 'INVALID_OPPORTUNITY_SLUG';
  end if;

  if p_metadata is null
     or jsonb_typeof(p_metadata) <> 'object'
     or octet_length(p_metadata::text) > 2048 then
    raise exception 'INVALID_METADATA';
  end if;

  -- Protect against accidental client loops. This is not a substitute for
  -- perimeter abuse protection, but prevents one browser session from flooding.
  select count(*) into recent_count
  from behavior_events
  where session_id=p_session_id
    and received_at >= now() - interval '1 minute';

  if recent_count >= 60 then
    return 'RATE_LIMITED';
  end if;

  insert into behavior_events(
    event_id,visitor_id,session_id,event_type,page_path,opportunity_slug,
    referrer_domain,utm_source,utm_medium,utm_campaign,device_class,metadata
  )
  values(
    p_event_id,p_visitor_id,p_session_id,p_event_type,p_page_path,p_opportunity_slug,
    nullif(left(coalesce(p_referrer_domain,''),253),''),
    nullif(left(coalesce(p_utm_source,''),80),''),
    nullif(left(coalesce(p_utm_medium,''),80),''),
    nullif(left(coalesce(p_utm_campaign,''),80),''),
    case when p_device_class in ('MOBILE','TABLET','DESKTOP','UNKNOWN')
      then p_device_class else 'UNKNOWN' end,
    p_metadata
  )
  on conflict(event_id) do nothing;

  get diagnostics inserted_count = row_count;
  if inserted_count=0 then
    return 'DUPLICATE';
  end if;
  return 'RECORDED';
end;
$$;

revoke all on function record_behavior_event_v01(
  uuid,uuid,uuid,text,text,text,text,text,text,text,text,jsonb
) from public,anon,authenticated;
grant execute on function record_behavior_event_v01(
  uuid,uuid,uuid,text,text,text,text,text,text,text,text,jsonb
) to service_role;

create or replace view analytics_daily_funnel_v01
with (security_invoker=true)
as
select
  (received_at at time zone 'Asia/Shanghai')::date as event_date_cn,
  count(distinct visitor_id) as unique_visitors,
  count(distinct session_id) as sessions,
  count(*) filter (where event_type='PAGE_VIEW') as page_views,
  count(distinct visitor_id) filter (where event_type='OPPORTUNITY_DETAIL_VIEW') as detail_visitors,
  count(distinct visitor_id) filter (where event_type='SECOND_OPPORTUNITY_VIEW') as second_opportunity_visitors,
  count(distinct visitor_id) filter (where event_type='CATALOG_SEARCH') as catalog_search_visitors,
  count(distinct visitor_id) filter (where event_type='SOURCE_OUTBOUND_CLICK') as source_outbound_visitors,
  count(distinct visitor_id) filter (where event_type='ENGAGED_30S') as engaged_30s_visitors,
  count(distinct visitor_id) filter (where event_type='SCROLL_90') as scroll_90_visitors
from behavior_events
group by 1;

revoke all on analytics_daily_funnel_v01 from public,anon,authenticated;
grant select on analytics_daily_funnel_v01 to service_role;

create or replace view analytics_opportunity_daily_v01
with (security_invoker=true)
as
select
  (received_at at time zone 'Asia/Shanghai')::date as event_date_cn,
  opportunity_slug,
  count(distinct visitor_id) filter (where event_type='OPPORTUNITY_CARD_CLICK') as card_click_visitors,
  count(distinct visitor_id) filter (where event_type='OPPORTUNITY_DETAIL_VIEW') as detail_visitors,
  count(distinct visitor_id) filter (where event_type='SOURCE_OUTBOUND_CLICK') as outbound_visitors,
  count(distinct visitor_id) filter (where event_type='ENGAGED_30S') as engaged_30s_visitors,
  count(distinct visitor_id) filter (where event_type='SCROLL_90') as scroll_90_visitors
from behavior_events
where opportunity_slug is not null
group by 1,2;

revoke all on analytics_opportunity_daily_v01 from public,anon,authenticated;
grant select on analytics_opportunity_daily_v01 to service_role;

create or replace view analytics_visitor_lifecycle_v01
with (security_invoker=true)
as
select
  visitor_id,
  min(received_at) as first_seen_at,
  max(received_at) as last_seen_at,
  count(distinct session_id) as session_count,
  count(distinct (received_at at time zone 'Asia/Shanghai')::date) as active_days,
  count(*) filter (where event_type='OPPORTUNITY_DETAIL_VIEW') as detail_views,
  count(distinct opportunity_slug) filter (
    where event_type='OPPORTUNITY_DETAIL_VIEW' and opportunity_slug is not null
  ) as distinct_opportunities_viewed,
  count(*) filter (where event_type='SOURCE_OUTBOUND_CLICK') as source_outbound_clicks,
  bool_or(received_at >= first_event.first_seen + interval '1 day') as returned_after_1d,
  bool_or(received_at >= first_event.first_seen + interval '7 days') as returned_after_7d
from behavior_events
cross join lateral (
  select min(b2.received_at) as first_seen
  from behavior_events b2
  where b2.visitor_id=behavior_events.visitor_id
) first_event
group by visitor_id;

revoke all on analytics_visitor_lifecycle_v01 from public,anon,authenticated;
grant select on analytics_visitor_lifecycle_v01 to service_role;

create or replace function purge_behavior_events_v01(p_retention_days integer default 90)
returns integer
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  deleted_count integer;
begin
  if p_retention_days < 30 or p_retention_days > 365 then
    raise exception 'INVALID_RETENTION_DAYS';
  end if;

  delete from behavior_events
  where received_at < now() - make_interval(days => p_retention_days);

  get diagnostics deleted_count = row_count;
  return deleted_count;
end;
$$;

revoke all on function purge_behavior_events_v01(integer)
  from public,anon,authenticated;
grant execute on function purge_behavior_events_v01(integer)
  to service_role;

do $$
declare
  existing_job bigint;
begin
  select jobid into existing_job
  from cron.job
  where jobname='jianshi-behavior-retention-daily'
  limit 1;
  if existing_job is not null then
    perform cron.unschedule(existing_job);
  end if;
end;
$$;

select cron.schedule(
  'jianshi-behavior-retention-daily',
  '25 3 * * *',
  'select public.purge_behavior_events_v01(90);'
);

comment on table behavior_events is
'P4.3 first-party pseudonymous product analytics. No email/name/IP/user-agent/full search text is persisted. Raw retention defaults to 90 days.';
comment on view analytics_daily_funnel_v01 is
'P4.3 internal daily validation funnel in China Standard Time.';
comment on view analytics_visitor_lifecycle_v01 is
'P4.3 internal anonymous return/engagement lifecycle used for product validation.';
