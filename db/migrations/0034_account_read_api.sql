-- R8.3 Account read API.
-- Replace cross-table security_invoker views with narrow security-definer RPCs.
-- Authenticated users never receive direct SELECT on the internal opportunities table.

drop view if exists my_saved_opportunities_v01;
drop view if exists my_watchlist_items_v01;
drop view if exists my_alert_events_v01;

create or replace function get_my_saved_opportunities_v01()
returns table(
  opportunity_id uuid,
  slug text,
  title text,
  category text,
  private_note text,
  saved_at timestamptz
)
language sql
stable
security definer
set search_path=public
as $$
  select
    s.opportunity_id,
    o.slug,
    o.title,
    o.category,
    s.private_note,
    s.created_at
  from saved_opportunities s
  join opportunities o on o.id=s.opportunity_id
  where auth.uid() is not null
    and s.user_id=auth.uid()
  order by s.created_at desc;
$$;

create or replace function get_my_watchlist_items_v01()
returns table(
  watchlist_id uuid,
  watchlist_name text,
  opportunity_id uuid,
  slug text,
  title text,
  category text,
  alert_on_validation boolean,
  alert_on_new_evidence boolean,
  alert_on_score_change boolean,
  score_change_threshold numeric,
  watched_at timestamptz
)
language sql
stable
security definer
set search_path=public
as $$
  select
    w.id,
    w.name,
    wi.opportunity_id,
    o.slug,
    o.title,
    o.category,
    wi.alert_on_validation,
    wi.alert_on_new_evidence,
    wi.alert_on_score_change,
    wi.score_change_threshold,
    wi.created_at
  from watchlists w
  join watchlist_items wi on wi.watchlist_id=w.id
  join opportunities o on o.id=wi.opportunity_id
  where auth.uid() is not null
    and w.user_id=auth.uid()
  order by wi.created_at desc;
$$;

create or replace function get_my_alert_events_v01(p_limit integer default 50)
returns table(
  alert_id bigint,
  event_date date,
  event_type text,
  headline_zh text,
  body_zh text,
  payload jsonb,
  status text,
  created_at timestamptz,
  read_at timestamptz,
  opportunity_id uuid,
  slug text,
  title text,
  category text
)
language sql
stable
security definer
set search_path=public
as $$
  select
    e.id,
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
  where auth.uid() is not null
    and e.user_id=auth.uid()
  order by e.created_at desc
  limit least(greatest(coalesce(p_limit,50),1),100);
$$;

revoke all on function get_my_saved_opportunities_v01() from public,anon;
revoke all on function get_my_watchlist_items_v01() from public,anon;
revoke all on function get_my_alert_events_v01(integer) from public,anon;

grant execute on function get_my_saved_opportunities_v01() to authenticated;
grant execute on function get_my_watchlist_items_v01() to authenticated;
grant execute on function get_my_alert_events_v01(integer) to authenticated;

comment on function get_my_saved_opportunities_v01() is
'R8.3 narrow authenticated read API; filters by auth.uid() and avoids exposing internal opportunities table.';
comment on function get_my_watchlist_items_v01() is
'R8.3 narrow authenticated watchlist read API.';
comment on function get_my_alert_events_v01(integer) is
'R8.3 narrow authenticated alert read API, max 100 rows.';
