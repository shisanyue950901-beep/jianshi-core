-- R8.1 User data foundation.
-- Public content remains readable without login. Private user data is owned by auth.uid().

create table if not exists user_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  locale text not null default 'zh-CN',
  timezone text not null default 'Asia/Shanghai',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_profiles_display_name_len
    check (display_name is null or char_length(display_name) between 1 and 80)
);

create table if not exists saved_opportunities (
  user_id uuid not null references auth.users(id) on delete cascade,
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  private_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(user_id,opportunity_id),
  constraint saved_opportunities_note_len
    check (private_note is null or char_length(private_note) <= 2000)
);
create index if not exists idx_saved_opportunities_user_created
  on saved_opportunities(user_id,created_at desc);

create table if not exists watchlists (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null default '我的观察清单',
  is_default boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint watchlists_name_len check (char_length(name) between 1 and 60)
);
create index if not exists idx_watchlists_user
  on watchlists(user_id,created_at desc);
create unique index if not exists ux_watchlists_one_default_per_user
  on watchlists(user_id) where is_default;

create table if not exists watchlist_items (
  id bigserial primary key,
  watchlist_id uuid not null references watchlists(id) on delete cascade,
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  alert_on_validation boolean not null default true,
  alert_on_new_evidence boolean not null default true,
  alert_on_score_change boolean not null default true,
  score_change_threshold numeric(5,2) not null default 3.00
    check (score_change_threshold between 0.10 and 100.00),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(watchlist_id,opportunity_id)
);
create index if not exists idx_watchlist_items_watchlist
  on watchlist_items(watchlist_id,created_at desc);
create index if not exists idx_watchlist_items_opportunity
  on watchlist_items(opportunity_id);

create table if not exists alert_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  in_app_enabled boolean not null default true,
  email_enabled boolean not null default false,
  daily_digest_enabled boolean not null default false,
  weekly_digest_enabled boolean not null default false,
  quiet_hours_enabled boolean not null default false,
  quiet_hours_start time,
  quiet_hours_end time,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint alert_preferences_quiet_hours
    check (
      (quiet_hours_enabled=false)
      or (quiet_hours_start is not null and quiet_hours_end is not null)
    )
);

alter table user_profiles enable row level security;
alter table saved_opportunities enable row level security;
alter table watchlists enable row level security;
alter table watchlist_items enable row level security;
alter table alert_preferences enable row level security;

revoke all on user_profiles,saved_opportunities,watchlists,watchlist_items,alert_preferences
  from anon,authenticated;
revoke all on sequence watchlist_items_id_seq from anon,authenticated;

grant select,insert,update on user_profiles to authenticated;
grant select,insert,update,delete on saved_opportunities to authenticated;
grant select,insert,update,delete on watchlists to authenticated;
grant select,insert,update,delete on watchlist_items to authenticated;
grant select,insert,update on alert_preferences to authenticated;
grant usage,select on sequence watchlist_items_id_seq to authenticated;

drop policy if exists user_profiles_select_own on user_profiles;
create policy user_profiles_select_own
on user_profiles for select to authenticated
using (id=auth.uid());

drop policy if exists user_profiles_insert_own on user_profiles;
create policy user_profiles_insert_own
on user_profiles for insert to authenticated
with check (id=auth.uid());

drop policy if exists user_profiles_update_own on user_profiles;
create policy user_profiles_update_own
on user_profiles for update to authenticated
using (id=auth.uid()) with check (id=auth.uid());

drop policy if exists saved_opportunities_select_own on saved_opportunities;
create policy saved_opportunities_select_own
on saved_opportunities for select to authenticated
using (user_id=auth.uid());

drop policy if exists saved_opportunities_insert_own on saved_opportunities;
create policy saved_opportunities_insert_own
on saved_opportunities for insert to authenticated
with check (user_id=auth.uid());

drop policy if exists saved_opportunities_update_own on saved_opportunities;
create policy saved_opportunities_update_own
on saved_opportunities for update to authenticated
using (user_id=auth.uid()) with check (user_id=auth.uid());

drop policy if exists saved_opportunities_delete_own on saved_opportunities;
create policy saved_opportunities_delete_own
on saved_opportunities for delete to authenticated
using (user_id=auth.uid());

drop policy if exists watchlists_select_own on watchlists;
create policy watchlists_select_own
on watchlists for select to authenticated
using (user_id=auth.uid());

drop policy if exists watchlists_insert_own on watchlists;
create policy watchlists_insert_own
on watchlists for insert to authenticated
with check (user_id=auth.uid());

drop policy if exists watchlists_update_own on watchlists;
create policy watchlists_update_own
on watchlists for update to authenticated
using (user_id=auth.uid()) with check (user_id=auth.uid());

drop policy if exists watchlists_delete_own on watchlists;
create policy watchlists_delete_own
on watchlists for delete to authenticated
using (user_id=auth.uid());

drop policy if exists watchlist_items_select_own on watchlist_items;
create policy watchlist_items_select_own
on watchlist_items for select to authenticated
using (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=auth.uid()
  )
);

drop policy if exists watchlist_items_insert_own on watchlist_items;
create policy watchlist_items_insert_own
on watchlist_items for insert to authenticated
with check (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=auth.uid()
  )
);

drop policy if exists watchlist_items_update_own on watchlist_items;
create policy watchlist_items_update_own
on watchlist_items for update to authenticated
using (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=auth.uid()
  )
)
with check (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=auth.uid()
  )
);

drop policy if exists watchlist_items_delete_own on watchlist_items;
create policy watchlist_items_delete_own
on watchlist_items for delete to authenticated
using (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=auth.uid()
  )
);

drop policy if exists alert_preferences_select_own on alert_preferences;
create policy alert_preferences_select_own
on alert_preferences for select to authenticated
using (user_id=auth.uid());

drop policy if exists alert_preferences_insert_own on alert_preferences;
create policy alert_preferences_insert_own
on alert_preferences for insert to authenticated
with check (user_id=auth.uid());

drop policy if exists alert_preferences_update_own on alert_preferences;
create policy alert_preferences_update_own
on alert_preferences for update to authenticated
using (user_id=auth.uid()) with check (user_id=auth.uid());

create or replace function handle_new_auth_user_v01()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
begin
  insert into user_profiles(id,display_name)
  values(
    new.id,
    nullif(left(coalesce(new.raw_user_meta_data->>'display_name',''),80),'')
  )
  on conflict(id) do nothing;

  insert into watchlists(user_id,name,is_default)
  values(new.id,'我的观察清单',true)
  on conflict do nothing;

  insert into alert_preferences(user_id)
  values(new.id)
  on conflict(user_id) do nothing;

  return new;
end;
$$;

revoke all on function handle_new_auth_user_v01() from public,anon,authenticated;

drop trigger if exists on_auth_user_created_jianshi on auth.users;
create trigger on_auth_user_created_jianshi
after insert on auth.users
for each row execute function handle_new_auth_user_v01();

create or replace view my_saved_opportunities_v01
with (security_invoker=true) as
select
  s.user_id,
  s.opportunity_id,
  o.slug,
  o.title,
  o.category,
  s.private_note,
  s.created_at,
  s.updated_at
from saved_opportunities s
join opportunities o on o.id=s.opportunity_id
where s.user_id=auth.uid();

create or replace view my_watchlist_items_v01
with (security_invoker=true) as
select
  w.user_id,
  w.id as watchlist_id,
  w.name as watchlist_name,
  wi.opportunity_id,
  o.slug,
  o.title,
  o.category,
  wi.alert_on_validation,
  wi.alert_on_new_evidence,
  wi.alert_on_score_change,
  wi.score_change_threshold,
  wi.created_at,
  wi.updated_at
from watchlists w
join watchlist_items wi on wi.watchlist_id=w.id
join opportunities o on o.id=wi.opportunity_id
where w.user_id=auth.uid();

grant select on my_saved_opportunities_v01,my_watchlist_items_v01 to authenticated;
revoke all on my_saved_opportunities_v01,my_watchlist_items_v01 from anon;

comment on table saved_opportunities is
'R8.1 private one-click saves. RLS: auth.uid() owns every row.';
comment on table watchlist_items is
'R8.1 private tracked opportunities and future alert preferences. Alert delivery is not enabled by this migration.';
comment on function handle_new_auth_user_v01() is
'Creates private JianShi profile, default watchlist and alert preferences for a new Supabase Auth user.';
