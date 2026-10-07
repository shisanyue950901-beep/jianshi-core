-- R8.6 Auth launch gate.
-- Account login requires BOTH build intent and a production database gate.
-- The database gate cannot be enabled until every frozen E2E criterion passes.

create table if not exists product_feature_flags (
  feature_key text primary key,
  enabled boolean not null default false,
  reason text,
  updated_at timestamptz not null default now()
);

create table if not exists auth_launch_gates (
  singleton boolean primary key default true check (singleton=true),
  custom_smtp_configured boolean not null default false,
  magic_link_e2e_pass boolean not null default false,
  jwt_ab_isolation_pass boolean not null default false,
  save_e2e_pass boolean not null default false,
  watch_e2e_pass boolean not null default false,
  alerts_isolation_pass boolean not null default false,
  session_logout_refresh_pass boolean not null default false,
  security_review_pass boolean not null default false,
  tested_at timestamptz,
  tested_by text,
  evidence_note text,
  updated_at timestamptz not null default now()
);

alter table product_feature_flags enable row level security;
alter table auth_launch_gates enable row level security;
revoke all on product_feature_flags,auth_launch_gates from anon,authenticated;

insert into product_feature_flags(feature_key,enabled,reason)
values(
  'account_auth',
  false,
  'R8.6 fail-closed until custom SMTP and all Auth E2E gates pass'
)
on conflict(feature_key) do nothing;

insert into auth_launch_gates(singleton)
values(true)
on conflict(singleton) do nothing;

create or replace function auth_launch_ready_v01()
returns boolean
language sql
stable
security definer
set search_path=public
as $$
  select coalesce(
    (
      select
        custom_smtp_configured
        and magic_link_e2e_pass
        and jwt_ab_isolation_pass
        and save_e2e_pass
        and watch_e2e_pass
        and alerts_isolation_pass
        and session_logout_refresh_pass
        and security_review_pass
      from auth_launch_gates
      where singleton=true
    ),
    false
  );
$$;

create or replace function get_public_feature_flags_v01()
returns jsonb
language sql
stable
security definer
set search_path=public
as $$
  select jsonb_build_object(
    'account_auth',
    coalesce(
      (select enabled from product_feature_flags where feature_key='account_auth'),
      false
    ) and auth_launch_ready_v01()
  );
$$;

create or replace function set_account_auth_feature_v01(p_enabled boolean,p_reason text default null)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  ready boolean;
begin
  ready := auth_launch_ready_v01();

  if p_enabled and not ready then
    raise exception 'AUTH_LAUNCH_GATE_NOT_READY';
  end if;

  insert into product_feature_flags(feature_key,enabled,reason,updated_at)
  values('account_auth',p_enabled,coalesce(p_reason,'service-role update'),now())
  on conflict(feature_key)
  do update set
    enabled=excluded.enabled,
    reason=excluded.reason,
    updated_at=now();

  return jsonb_build_object(
    'account_auth',p_enabled,
    'launch_ready',ready
  );
end;
$$;

revoke all on function auth_launch_ready_v01() from public,anon,authenticated;
revoke all on function get_public_feature_flags_v01() from public,anon,authenticated;
revoke all on function set_account_auth_feature_v01(boolean,text) from public,anon,authenticated;

grant execute on function auth_launch_ready_v01() to service_role;
grant execute on function get_public_feature_flags_v01() to service_role;
grant execute on function set_account_auth_feature_v01(boolean,text) to service_role;
grant select,insert,update on product_feature_flags,auth_launch_gates to service_role;

comment on table auth_launch_gates is
'R8.6 production launch evidence. All eight gates must pass before account_auth can be enabled.';
comment on function set_account_auth_feature_v01(boolean,text) is
'Fail-closed service-role feature switch. Enabling account auth is rejected unless all frozen R8.6 launch gates are true.';
