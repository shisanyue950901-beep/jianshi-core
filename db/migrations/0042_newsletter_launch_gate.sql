-- P1.1 Newsletter production launch gate.
-- Credentials alone must never enable real outbound email.
-- Public send paths remain fail-closed until every launch criterion is explicitly passed.

create table if not exists newsletter_launch_control (
  singleton boolean primary key default true check (singleton),
  sender_domain_verified boolean not null default false,
  confirmation_e2e_pass boolean not null default false,
  daily_digest_e2e_pass boolean not null default false,
  unsubscribe_e2e_pass boolean not null default false,
  bounce_complaint_handling_pass boolean not null default false,
  security_review_pass boolean not null default false,
  updated_at timestamptz not null default now()
);

insert into newsletter_launch_control(singleton)
values(true)
on conflict(singleton) do nothing;

alter table newsletter_launch_control enable row level security;
revoke all on newsletter_launch_control from public,anon,authenticated;
grant select,update on newsletter_launch_control to service_role;

create or replace function newsletter_launch_ready_v01()
returns boolean
language sql
security definer
set search_path=public
as $$
  select
    public.newsletter_provider_ready_v01()
    and coalesce(sender_domain_verified,false)
    and coalesce(confirmation_e2e_pass,false)
    and coalesce(daily_digest_e2e_pass,false)
    and coalesce(unsubscribe_e2e_pass,false)
    and coalesce(bounce_complaint_handling_pass,false)
    and coalesce(security_review_pass,false)
  from public.newsletter_launch_control
  where singleton=true;
$$;

revoke all on function newsletter_launch_ready_v01() from public,anon,authenticated;
grant execute on function newsletter_launch_ready_v01() to service_role;

create or replace view newsletter_launch_status_v01
with (security_invoker=true)
as
select
  public.newsletter_provider_ready_v01() as provider_ready,
  sender_domain_verified,
  confirmation_e2e_pass,
  daily_digest_e2e_pass,
  unsubscribe_e2e_pass,
  bounce_complaint_handling_pass,
  security_review_pass,
  public.newsletter_launch_ready_v01() as launch_ready,
  updated_at
from public.newsletter_launch_control
where singleton=true;

revoke all on newsletter_launch_status_v01 from public,anon,authenticated;
grant select on newsletter_launch_status_v01 to service_role;

comment on table newsletter_launch_control is
'P1.1 explicit fail-closed production launch gate for JianShi newsletter. Provider credentials alone never open sending.';
comment on function newsletter_launch_ready_v01() is
'True only when provider credentials exist and every newsletter launch criterion has explicitly passed.';
