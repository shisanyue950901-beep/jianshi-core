-- R8.4 Account write API hardening.
-- Browsers no longer write saved/watchlist/alert tables directly.
-- All user actions go through narrow auth.uid()-scoped RPCs.

create or replace function save_my_opportunity_v01(p_opportunity_id uuid)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  uid uuid := auth.uid();
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED';
  end if;

  if not exists (
    select 1 from opportunities
    where id=p_opportunity_id and status='ACTIVE'
  ) then
    raise exception 'OPPORTUNITY_NOT_FOUND';
  end if;

  insert into saved_opportunities(user_id,opportunity_id)
  values(uid,p_opportunity_id)
  on conflict(user_id,opportunity_id)
  do update set updated_at=now();

  return true;
end;
$$;

create or replace function watch_my_opportunity_v01(p_opportunity_id uuid)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  uid uuid := auth.uid();
  default_watchlist_id uuid;
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED';
  end if;

  if not exists (
    select 1 from opportunities
    where id=p_opportunity_id and status='ACTIVE'
  ) then
    raise exception 'OPPORTUNITY_NOT_FOUND';
  end if;

  select id into default_watchlist_id
  from watchlists
  where user_id=uid and is_default=true
  order by created_at
  limit 1;

  if default_watchlist_id is null then
    insert into watchlists(user_id,name,is_default)
    values(uid,'我的观察清单',true)
    returning id into default_watchlist_id;
  end if;

  insert into watchlist_items(watchlist_id,opportunity_id)
  values(default_watchlist_id,p_opportunity_id)
  on conflict(watchlist_id,opportunity_id)
  do update set updated_at=now();

  return true;
end;
$$;

create or replace function mark_my_alert_read_v01(p_alert_id bigint)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  uid uuid := auth.uid();
  changed integer;
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED';
  end if;

  update user_alert_events
  set status='READ',
      read_at=coalesce(read_at,now()),
      updated_at=now()
  where id=p_alert_id
    and user_id=uid
    and status='UNREAD';

  get diagnostics changed = row_count;
  return changed>0;
end;
$$;

revoke all on function save_my_opportunity_v01(uuid) from public,anon;
revoke all on function watch_my_opportunity_v01(uuid) from public,anon;
revoke all on function mark_my_alert_read_v01(bigint) from public,anon;

grant execute on function save_my_opportunity_v01(uuid) to authenticated;
grant execute on function watch_my_opportunity_v01(uuid) to authenticated;
grant execute on function mark_my_alert_read_v01(bigint) to authenticated;

-- Account UI uses narrow RPCs; remove direct browser access to backing tables.
revoke all on saved_opportunities from authenticated;
revoke all on watchlists from authenticated;
revoke all on watchlist_items from authenticated;
revoke all on user_alert_events from authenticated;
revoke usage,select on sequence watchlist_items_id_seq from authenticated;

comment on function save_my_opportunity_v01(uuid) is
'R8.4 narrow authenticated write API. Uses auth.uid(); no direct table write grant required.';
comment on function watch_my_opportunity_v01(uuid) is
'R8.4 narrow authenticated default-watchlist API. Uses auth.uid().';
comment on function mark_my_alert_read_v01(bigint) is
'R8.4 narrow authenticated alert acknowledgement API. Can only update the caller own alert.';
