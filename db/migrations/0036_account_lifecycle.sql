-- R8.5 Account lifecycle actions.
-- Keep public content independent from accounts. These APIs only mutate the caller's private state.

create or replace function unsave_my_opportunity_v01(p_opportunity_id uuid)
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

  delete from saved_opportunities
  where user_id=uid
    and opportunity_id=p_opportunity_id;

  get diagnostics changed = row_count;
  return changed>0;
end;
$$;

create or replace function unwatch_my_opportunity_v01(p_opportunity_id uuid)
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

  delete from watchlist_items wi
  using watchlists w
  where wi.watchlist_id=w.id
    and w.user_id=uid
    and wi.opportunity_id=p_opportunity_id;

  get diagnostics changed = row_count;
  return changed>0;
end;
$$;

create or replace function get_my_alert_preferences_v01()
returns table(
  in_app_enabled boolean,
  email_enabled boolean,
  daily_digest_enabled boolean,
  weekly_digest_enabled boolean,
  quiet_hours_enabled boolean,
  quiet_hours_start time,
  quiet_hours_end time
)
language sql
stable
security definer
set search_path=public
as $$
  select
    p.in_app_enabled,
    p.email_enabled,
    p.daily_digest_enabled,
    p.weekly_digest_enabled,
    p.quiet_hours_enabled,
    p.quiet_hours_start,
    p.quiet_hours_end
  from alert_preferences p
  where auth.uid() is not null
    and p.user_id=auth.uid();
$$;

create or replace function update_my_alert_preferences_v01(
  p_in_app_enabled boolean default true,
  p_email_enabled boolean default false,
  p_daily_digest_enabled boolean default false,
  p_weekly_digest_enabled boolean default false
)
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

  insert into alert_preferences(
    user_id,in_app_enabled,email_enabled,daily_digest_enabled,weekly_digest_enabled
  )
  values(
    uid,
    coalesce(p_in_app_enabled,true),
    coalesce(p_email_enabled,false),
    coalesce(p_daily_digest_enabled,false),
    coalesce(p_weekly_digest_enabled,false)
  )
  on conflict(user_id)
  do update set
    in_app_enabled=excluded.in_app_enabled,
    email_enabled=excluded.email_enabled,
    daily_digest_enabled=excluded.daily_digest_enabled,
    weekly_digest_enabled=excluded.weekly_digest_enabled,
    updated_at=now();

  return true;
end;
$$;

create or replace function clear_my_jianshi_data_v01()
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  uid uuid := auth.uid();
  saved_deleted integer := 0;
  watched_deleted integer := 0;
  alerts_deleted integer := 0;
  extra_lists_deleted integer := 0;
begin
  if uid is null then
    raise exception 'AUTH_REQUIRED';
  end if;

  delete from user_alert_events
  where user_id=uid;
  get diagnostics alerts_deleted = row_count;

  delete from watchlist_items wi
  using watchlists w
  where wi.watchlist_id=w.id
    and w.user_id=uid;
  get diagnostics watched_deleted = row_count;

  delete from saved_opportunities
  where user_id=uid;
  get diagnostics saved_deleted = row_count;

  delete from watchlists
  where user_id=uid
    and is_default=false;
  get diagnostics extra_lists_deleted = row_count;

  insert into watchlists(user_id,name,is_default)
  values(uid,'我的观察清单',true)
  on conflict do nothing;

  insert into alert_preferences(
    user_id,in_app_enabled,email_enabled,daily_digest_enabled,weekly_digest_enabled,
    quiet_hours_enabled,quiet_hours_start,quiet_hours_end
  )
  values(uid,true,false,false,false,false,null,null)
  on conflict(user_id)
  do update set
    in_app_enabled=true,
    email_enabled=false,
    daily_digest_enabled=false,
    weekly_digest_enabled=false,
    quiet_hours_enabled=false,
    quiet_hours_start=null,
    quiet_hours_end=null,
    updated_at=now();

  return jsonb_build_object(
    'saved_deleted',saved_deleted,
    'watched_deleted',watched_deleted,
    'alerts_deleted',alerts_deleted,
    'extra_lists_deleted',extra_lists_deleted,
    'auth_account_deleted',false
  );
end;
$$;

revoke all on function unsave_my_opportunity_v01(uuid) from public,anon;
revoke all on function unwatch_my_opportunity_v01(uuid) from public,anon;
revoke all on function get_my_alert_preferences_v01() from public,anon;
revoke all on function update_my_alert_preferences_v01(boolean,boolean,boolean,boolean) from public,anon;
revoke all on function clear_my_jianshi_data_v01() from public,anon;

grant execute on function unsave_my_opportunity_v01(uuid) to authenticated;
grant execute on function unwatch_my_opportunity_v01(uuid) to authenticated;
grant execute on function get_my_alert_preferences_v01() to authenticated;
grant execute on function update_my_alert_preferences_v01(boolean,boolean,boolean,boolean) to authenticated;
grant execute on function clear_my_jianshi_data_v01() to authenticated;

comment on function clear_my_jianshi_data_v01() is
'R8.5 clears JianShi behavioral/account-product data owned by auth.uid(); does not delete the Supabase Auth identity.';
