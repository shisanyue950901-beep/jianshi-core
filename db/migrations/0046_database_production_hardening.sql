-- P3.6 Database production hardening.
-- Free-first: no paid plan changes, no business scoring changes, no Auth launch.
-- Goals:
-- 1) cover currently unindexed foreign keys;
-- 2) make auth RLS policies InitPlan-friendly at scale;
-- 3) expose service-role-only capacity health for operational checks.

-- ---------------------------------------------------------------------------
-- Foreign-key covering indexes
-- ---------------------------------------------------------------------------

create index if not exists idx_opportunity_github_query_map_query_id
  on opportunity_github_query_map(query_id);

create index if not exists idx_saved_opportunities_opportunity_id
  on saved_opportunities(opportunity_id);

create index if not exists idx_source_provenance_audits_aggregator_source_id
  on source_provenance_audits(aggregator_source_id);

create index if not exists idx_source_provenance_rules_upstream_source_id
  on source_provenance_rules(upstream_source_id);

-- ---------------------------------------------------------------------------
-- RLS performance hardening
-- Supabase/Postgres can evaluate (select auth.uid()) once as an InitPlan
-- instead of re-evaluating auth.uid() for every candidate row.
-- Semantics remain identical: every private row is still caller-owned.
-- ---------------------------------------------------------------------------

drop policy if exists user_profiles_select_own on user_profiles;
create policy user_profiles_select_own
on user_profiles for select to authenticated
using (id=(select auth.uid()));

drop policy if exists user_profiles_insert_own on user_profiles;
create policy user_profiles_insert_own
on user_profiles for insert to authenticated
with check (id=(select auth.uid()));

drop policy if exists user_profiles_update_own on user_profiles;
create policy user_profiles_update_own
on user_profiles for update to authenticated
using (id=(select auth.uid()))
with check (id=(select auth.uid()));

drop policy if exists saved_opportunities_select_own on saved_opportunities;
create policy saved_opportunities_select_own
on saved_opportunities for select to authenticated
using (user_id=(select auth.uid()));

drop policy if exists saved_opportunities_insert_own on saved_opportunities;
create policy saved_opportunities_insert_own
on saved_opportunities for insert to authenticated
with check (user_id=(select auth.uid()));

drop policy if exists saved_opportunities_update_own on saved_opportunities;
create policy saved_opportunities_update_own
on saved_opportunities for update to authenticated
using (user_id=(select auth.uid()))
with check (user_id=(select auth.uid()));

drop policy if exists saved_opportunities_delete_own on saved_opportunities;
create policy saved_opportunities_delete_own
on saved_opportunities for delete to authenticated
using (user_id=(select auth.uid()));

drop policy if exists watchlists_select_own on watchlists;
create policy watchlists_select_own
on watchlists for select to authenticated
using (user_id=(select auth.uid()));

drop policy if exists watchlists_insert_own on watchlists;
create policy watchlists_insert_own
on watchlists for insert to authenticated
with check (user_id=(select auth.uid()));

drop policy if exists watchlists_update_own on watchlists;
create policy watchlists_update_own
on watchlists for update to authenticated
using (user_id=(select auth.uid()))
with check (user_id=(select auth.uid()));

drop policy if exists watchlists_delete_own on watchlists;
create policy watchlists_delete_own
on watchlists for delete to authenticated
using (user_id=(select auth.uid()));

drop policy if exists watchlist_items_select_own on watchlist_items;
create policy watchlist_items_select_own
on watchlist_items for select to authenticated
using (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=(select auth.uid())
  )
);

drop policy if exists watchlist_items_insert_own on watchlist_items;
create policy watchlist_items_insert_own
on watchlist_items for insert to authenticated
with check (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=(select auth.uid())
  )
);

drop policy if exists watchlist_items_update_own on watchlist_items;
create policy watchlist_items_update_own
on watchlist_items for update to authenticated
using (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=(select auth.uid())
  )
)
with check (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=(select auth.uid())
  )
);

drop policy if exists watchlist_items_delete_own on watchlist_items;
create policy watchlist_items_delete_own
on watchlist_items for delete to authenticated
using (
  exists (
    select 1 from watchlists w
    where w.id=watchlist_items.watchlist_id
      and w.user_id=(select auth.uid())
  )
);

drop policy if exists alert_preferences_select_own on alert_preferences;
create policy alert_preferences_select_own
on alert_preferences for select to authenticated
using (user_id=(select auth.uid()));

drop policy if exists alert_preferences_insert_own on alert_preferences;
create policy alert_preferences_insert_own
on alert_preferences for insert to authenticated
with check (user_id=(select auth.uid()));

drop policy if exists alert_preferences_update_own on alert_preferences;
create policy alert_preferences_update_own
on alert_preferences for update to authenticated
using (user_id=(select auth.uid()))
with check (user_id=(select auth.uid()));

drop policy if exists user_alert_events_select_own on user_alert_events;
create policy user_alert_events_select_own
on user_alert_events for select to authenticated
using (user_id=(select auth.uid()));

drop policy if exists user_alert_events_update_own on user_alert_events;
create policy user_alert_events_update_own
on user_alert_events for update to authenticated
using (user_id=(select auth.uid()))
with check (user_id=(select auth.uid()));

-- ---------------------------------------------------------------------------
-- Internal capacity health
-- Default database limit is the current Supabase Free-plan 500 MiB assumption.
-- Pass a different limit after a plan/storage upgrade.
-- ---------------------------------------------------------------------------

create or replace function database_capacity_health_v01(
  p_database_limit_bytes bigint default 524288000
)
returns jsonb
language sql
stable
security definer
set search_path=pg_catalog,public
as $$
with s as (
  select
    pg_database_size(current_database())::bigint as database_bytes,
    greatest(coalesce(p_database_limit_bytes,524288000),1)::bigint as database_limit_bytes,
    current_setting('max_connections')::integer as max_connections,
    (
      select count(*)::integer
      from pg_stat_activity
      where datname=current_database()
    ) as current_connections,
    (
      select count(*)::integer
      from pg_stat_activity
      where datname=current_database()
        and state='active'
    ) as active_connections
),
m as (
  select
    *,
    round((database_bytes::numeric/database_limit_bytes::numeric)*100,2) as database_used_pct,
    round((current_connections::numeric/greatest(max_connections,1)::numeric)*100,2) as connection_used_pct
  from s
)
select jsonb_build_object(
  'database_bytes',database_bytes,
  'database_limit_bytes',database_limit_bytes,
  'database_used_pct',database_used_pct,
  'database_state',
    case
      when database_used_pct >= 90 then 'CRITICAL'
      when database_used_pct >= 70 then 'WARNING'
      else 'HEALTHY'
    end,
  'max_connections',max_connections,
  'current_connections',current_connections,
  'active_connections',active_connections,
  'connection_used_pct',connection_used_pct,
  'connection_state',
    case
      when connection_used_pct >= 90 then 'CRITICAL'
      when connection_used_pct >= 70 then 'WARNING'
      else 'HEALTHY'
    end,
  'warning_threshold_pct',70,
  'critical_threshold_pct',90,
  'checked_at',clock_timestamp()
)
from m;
$$;

revoke all on function database_capacity_health_v01(bigint)
  from public,anon,authenticated;
grant execute on function database_capacity_health_v01(bigint)
  to service_role;

comment on function database_capacity_health_v01(bigint) is
'P3.6 service-role-only DB/connection capacity health. Default limit assumes current Free-plan 500 MiB; pass the real storage limit after upgrades.';
