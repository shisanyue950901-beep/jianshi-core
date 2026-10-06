-- R8.2 Watchlist alert engine.
-- Generates private in-app alerts from already-computed daily opportunity changes.
-- No email is sent by this migration.

create table if not exists user_alert_events (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  watchlist_item_id bigint not null references watchlist_items(id) on delete cascade,
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  event_date date not null,
  event_type text not null
    check (event_type in ('NEWLY_VALIDATED','NEW_EVIDENCE','SCORE_CHANGE')),
  headline_zh text not null,
  body_zh text,
  payload jsonb not null default '{}'::jsonb,
  status text not null default 'UNREAD'
    check (status in ('UNREAD','READ','DISMISSED')),
  created_at timestamptz not null default now(),
  read_at timestamptz,
  updated_at timestamptz not null default now(),
  unique(watchlist_item_id,event_date,event_type)
);

create index if not exists idx_user_alert_events_user_status_time
  on user_alert_events(user_id,status,created_at desc);
create index if not exists idx_user_alert_events_opportunity_time
  on user_alert_events(opportunity_id,created_at desc);

alter table user_alert_events enable row level security;
revoke all on user_alert_events from anon,authenticated;
revoke all on sequence user_alert_events_id_seq from anon,authenticated;

grant select,update on user_alert_events to authenticated;
grant select,insert,update on user_alert_events to service_role;
grant usage,select on sequence user_alert_events_id_seq to service_role;

drop policy if exists user_alert_events_select_own on user_alert_events;
create policy user_alert_events_select_own
on user_alert_events for select to authenticated
using (user_id=auth.uid());

drop policy if exists user_alert_events_update_own on user_alert_events;
create policy user_alert_events_update_own
on user_alert_events for update to authenticated
using (user_id=auth.uid())
with check (user_id=auth.uid());

create or replace function refresh_user_alert_events_v01()
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  inserted_validation integer := 0;
  inserted_evidence integer := 0;
  inserted_score integer := 0;
begin
  insert into user_alert_events(
    user_id,watchlist_item_id,opportunity_id,event_date,event_type,
    headline_zh,body_zh,payload
  )
  select
    w.user_id,
    wi.id,
    wi.opportunity_id,
    c.snapshot_date,
    'NEWLY_VALIDATED',
    o.title || ' 今天升级为已验证机会',
    '这个方向今天首次通过多源验证，建议重新查看证据和商业判断。',
    jsonb_build_object(
      'change_state',c.change_state,
      'source_count',c.source_count,
      'evidence_count',c.evidence_count,
      'overall_score',c.overall_score
    )
  from watchlist_items wi
  join watchlists w on w.id=wi.watchlist_id
  join opportunities o on o.id=wi.opportunity_id
  join public_opportunity_changes_v01 c on c.slug=o.slug
  where wi.alert_on_validation=true
    and c.change_state='NEWLY_VALIDATED'
  on conflict(watchlist_item_id,event_date,event_type) do nothing;

  get diagnostics inserted_validation = row_count;

  insert into user_alert_events(
    user_id,watchlist_item_id,opportunity_id,event_date,event_type,
    headline_zh,body_zh,payload
  )
  select
    w.user_id,
    wi.id,
    wi.opportunity_id,
    c.snapshot_date,
    'NEW_EVIDENCE',
    o.title || ' 今天新增 ' || c.evidence_delta_1d::text || ' 条有效证据',
    '你关注的方向今天出现了新的有效证据，建议查看详情页。',
    jsonb_build_object(
      'evidence_delta_1d',c.evidence_delta_1d,
      'evidence_count',c.evidence_count,
      'source_count',c.source_count,
      'overall_score',c.overall_score
    )
  from watchlist_items wi
  join watchlists w on w.id=wi.watchlist_id
  join opportunities o on o.id=wi.opportunity_id
  join public_opportunity_changes_v01 c on c.slug=o.slug
  where wi.alert_on_new_evidence=true
    and coalesce(c.evidence_delta_1d,0)>0
  on conflict(watchlist_item_id,event_date,event_type) do nothing;

  get diagnostics inserted_evidence = row_count;

  insert into user_alert_events(
    user_id,watchlist_item_id,opportunity_id,event_date,event_type,
    headline_zh,body_zh,payload
  )
  select
    w.user_id,
    wi.id,
    wi.opportunity_id,
    c.snapshot_date,
    'SCORE_CHANGE',
    o.title || ' 综合分较昨日 '
      || case when c.overall_delta_1d>=0 then '+' else '' end
      || round(c.overall_delta_1d::numeric,1)::text,
    '你关注的方向综合判断发生了超过设定阈值的变化。',
    jsonb_build_object(
      'overall_delta_1d',c.overall_delta_1d,
      'overall_score',c.overall_score,
      'heat_delta_1d',c.heat_delta_1d,
      'evidence_delta_1d',c.evidence_delta_1d,
      'threshold',wi.score_change_threshold
    )
  from watchlist_items wi
  join watchlists w on w.id=wi.watchlist_id
  join opportunities o on o.id=wi.opportunity_id
  join public_opportunity_changes_v01 c on c.slug=o.slug
  where wi.alert_on_score_change=true
    and c.overall_delta_1d is not null
    and abs(c.overall_delta_1d)>=wi.score_change_threshold
  on conflict(watchlist_item_id,event_date,event_type) do nothing;

  get diagnostics inserted_score = row_count;

  return jsonb_build_object(
    'inserted_total',inserted_validation+inserted_evidence+inserted_score,
    'newly_validated',inserted_validation,
    'new_evidence',inserted_evidence,
    'score_change',inserted_score
  );
end;
$$;

revoke all on function refresh_user_alert_events_v01()
  from public,anon,authenticated;
grant execute on function refresh_user_alert_events_v01() to service_role;

create or replace view my_alert_events_v01
with (security_invoker=true) as
select
  e.id,
  e.user_id,
  e.event_date,
  e.event_type,
  e.headline_zh,
  e.body_zh,
  e.payload,
  e.status,
  e.created_at,
  e.read_at,
  e.opportunity_id,
  o.slug,
  o.title,
  o.category
from user_alert_events e
join opportunities o on o.id=e.opportunity_id
where e.user_id=auth.uid();

grant select on my_alert_events_v01 to authenticated;
revoke all on my_alert_events_v01 from anon;

comment on table user_alert_events is
'R8.2 private in-app alert events generated from watchlist settings and daily opportunity changes.';
comment on function refresh_user_alert_events_v01() is
'Idempotent watchlist alert generator. Email delivery is intentionally outside R8.2.';
