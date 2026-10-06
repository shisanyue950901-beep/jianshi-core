-- R7.5 lightweight newsletter subscription.
-- No account/password required. Email remains private and is only accessible
-- through service-role code. Double opt-in is supported; provider send stays
-- fail-closed until Resend production secrets are present in Vault.

create table if not exists newsletter_subscribers (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  status text not null default 'PENDING_CONFIRMATION'
    check (status in ('PENDING_CONFIRMATION','ACTIVE','UNSUBSCRIBED','BOUNCED','COMPLAINED')),
  confirmation_token_hash text,
  unsubscribe_token_hash text not null,
  source_path text,
  interests jsonb not null default '["DAILY_TOP10"]'::jsonb,
  consent_version text not null default 'NEWSLETTER_V1_20261006',
  consent_at timestamptz not null default now(),
  confirmation_requested_at timestamptz,
  confirmed_at timestamptz,
  unsubscribed_at timestamptz,
  last_sent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint newsletter_email_normalized check (email=lower(btrim(email)))
);

create unique index if not exists ux_newsletter_subscribers_email
  on newsletter_subscribers(email);
create index if not exists idx_newsletter_subscribers_status
  on newsletter_subscribers(status,created_at desc);

create table if not exists newsletter_events (
  id bigserial primary key,
  subscriber_id uuid references newsletter_subscribers(id) on delete set null,
  event_type text not null check (event_type in (
    'SUBSCRIBE_REQUESTED','CONFIRMATION_QUEUED','CONFIRMATION_PROVIDER_PENDING',
    'CONFIRMED','UNSUBSCRIBED','SEND_QUEUED','DELIVERED','BOUNCED','COMPLAINED'
  )),
  provider text,
  provider_request_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_newsletter_events_subscriber_time
  on newsletter_events(subscriber_id,created_at desc);

alter table newsletter_subscribers enable row level security;
alter table newsletter_events enable row level security;
revoke all on newsletter_subscribers,newsletter_events from anon,authenticated;
revoke all on sequence newsletter_events_id_seq from anon,authenticated;

create or replace function queue_newsletter_confirmation_v01(
  p_subscriber_id uuid,
  p_email text,
  p_confirm_token text,
  p_unsubscribe_token text
)
returns jsonb
language plpgsql
security definer
set search_path=public,vault,net
as $$
declare
  api_key text;
  from_email text;
  endpoint text;
  request_id bigint;
begin
  select decrypted_secret into api_key
  from vault.decrypted_secrets where name='resend_api_key' limit 1;

  select decrypted_secret into from_email
  from vault.decrypted_secrets where name='newsletter_from_email' limit 1;

  select decrypted_secret into endpoint
  from vault.decrypted_secrets where name='jianshi_project_url' limit 1;

  if api_key is null or from_email is null or endpoint is null then
    insert into newsletter_events(subscriber_id,event_type,provider,metadata)
    values(p_subscriber_id,'CONFIRMATION_PROVIDER_PENDING','resend',
           jsonb_build_object('reason','EMAIL_PROVIDER_NOT_CONFIGURED'));
    return jsonb_build_object('sent',false,'reason','EMAIL_PROVIDER_NOT_CONFIGURED');
  end if;

  select net.http_post(
    url := 'https://api.resend.com/emails',
    headers := jsonb_build_object(
      'Authorization','Bearer ' || api_key,
      'Content-Type','application/json'
    ),
    body := jsonb_build_object(
      'from',from_email,
      'to',jsonb_build_array(p_email),
      'subject','确认订阅「见势」每日机会',
      'html',
        '<div style="font-family:Arial,Microsoft YaHei,sans-serif;max-width:620px;margin:auto;padding:24px">' ||
        '<h2>确认订阅「见势」</h2>' ||
        '<p>你申请接收「每天 Top 10 机会」。确认后，我们才会向这个邮箱发送每日情报。</p>' ||
        '<p><a style="display:inline-block;padding:12px 18px;background:#171714;color:#fff;text-decoration:none" href="' ||
        endpoint || '/functions/v1/newsletter-subscribe?mode=confirm&token=' || p_confirm_token ||
        '">确认订阅</a></p>' ||
        '<p style="color:#777;font-size:12px">如果不是你本人提交，可以忽略这封邮件。</p>' ||
        '<p style="color:#777;font-size:12px"><a href="' ||
        endpoint || '/functions/v1/newsletter-subscribe?mode=unsubscribe&token=' || p_unsubscribe_token ||
        '">不再接收见势邮件</a></p></div>'
    ),
    timeout_milliseconds := 15000
  ) into request_id;

  insert into newsletter_events(subscriber_id,event_type,provider,provider_request_id)
  values(p_subscriber_id,'CONFIRMATION_QUEUED','resend',request_id::text);

  return jsonb_build_object('sent',true,'request_id',request_id);
exception when others then
  insert into newsletter_events(subscriber_id,event_type,provider,metadata)
  values(p_subscriber_id,'CONFIRMATION_PROVIDER_PENDING','resend',
         jsonb_build_object('reason','PROVIDER_CALL_FAILED'));
  return jsonb_build_object('sent',false,'reason','PROVIDER_CALL_FAILED');
end;
$$;

revoke all on function queue_newsletter_confirmation_v01(uuid,text,text,text)
  from public,anon,authenticated;

create or replace view newsletter_internal_metrics_v01 as
select
  count(*) as total,
  count(*) filter (where status='PENDING_CONFIRMATION') as pending_confirmation,
  count(*) filter (where status='ACTIVE') as active,
  count(*) filter (where status='UNSUBSCRIBED') as unsubscribed,
  count(*) filter (where status='BOUNCED') as bounced,
  max(created_at) as latest_signup_at
from newsletter_subscribers;

alter view newsletter_internal_metrics_v01 set (security_invoker=true);
revoke all on newsletter_internal_metrics_v01 from anon,authenticated;

comment on table newsletter_subscribers is
'R7.5 private email subscription state. No public/anon table access. Double opt-in before ACTIVE.';


grant select,insert,update on newsletter_subscribers,newsletter_events to service_role;
grant usage,select on sequence newsletter_events_id_seq to service_role;
grant execute on function queue_newsletter_confirmation_v01(uuid,text,text,text) to service_role;

create or replace function newsletter_provider_ready_v01()
returns boolean
language sql
security definer
set search_path=public,vault
as $$
  select exists(select 1 from vault.decrypted_secrets where name='resend_api_key')
     and exists(select 1 from vault.decrypted_secrets where name='newsletter_from_email')
     and exists(select 1 from vault.decrypted_secrets where name='jianshi_project_url');
$$;

revoke all on function newsletter_provider_ready_v01() from public,anon,authenticated;
grant execute on function newsletter_provider_ready_v01() to service_role;


create or replace function request_newsletter_subscription_v01(
  p_email text,
  p_source_path text,
  p_confirmation_token_hash text,
  p_unsubscribe_token_hash text
)
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  normalized_email text := lower(btrim(p_email));
  existing newsletter_subscribers%rowtype;
  sid uuid;
  should_send boolean := true;
begin
  select * into existing
  from newsletter_subscribers
  where email=normalized_email
  for update;

  if found and existing.status='ACTIVE' then
    insert into newsletter_events(subscriber_id,event_type,provider,metadata)
    values(existing.id,'SUBSCRIBE_REQUESTED','website',jsonb_build_object('result','ALREADY_ACTIVE'));
    return jsonb_build_object('subscriber_id',existing.id,'status','ACTIVE','should_send',false);
  end if;

  if found and existing.status='PENDING_CONFIRMATION'
     and existing.confirmation_requested_at is not null
     and existing.confirmation_requested_at > now()-interval '10 minutes' then
    insert into newsletter_events(subscriber_id,event_type,provider,metadata)
    values(existing.id,'SUBSCRIBE_REQUESTED','website',jsonb_build_object('result','COOLDOWN'));
    return jsonb_build_object('subscriber_id',existing.id,'status','PENDING_CONFIRMATION','should_send',false);
  end if;

  if found then
    update newsletter_subscribers
    set status='PENDING_CONFIRMATION',
        confirmation_token_hash=p_confirmation_token_hash,
        unsubscribe_token_hash=p_unsubscribe_token_hash,
        source_path=left(coalesce(p_source_path,'/'),200),
        consent_version='NEWSLETTER_V1_20261006',
        consent_at=now(),
        confirmation_requested_at=now(),
        confirmed_at=null,
        unsubscribed_at=null,
        updated_at=now()
    where id=existing.id
    returning id into sid;
  else
    insert into newsletter_subscribers(
      email,status,confirmation_token_hash,unsubscribe_token_hash,source_path,
      confirmation_requested_at
    )
    values(
      normalized_email,'PENDING_CONFIRMATION',p_confirmation_token_hash,p_unsubscribe_token_hash,
      left(coalesce(p_source_path,'/'),200),now()
    )
    returning id into sid;
  end if;

  insert into newsletter_events(subscriber_id,event_type,provider,metadata)
  values(sid,'SUBSCRIBE_REQUESTED','website',jsonb_build_object('result','ACCEPTED'));

  return jsonb_build_object('subscriber_id',sid,'status','PENDING_CONFIRMATION','should_send',should_send);
end;
$$;

create or replace function confirm_newsletter_subscription_v01(p_token_hash text)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  sid uuid;
begin
  update newsletter_subscribers
  set status='ACTIVE',
      confirmed_at=coalesce(confirmed_at,now()),
      confirmation_token_hash=null,
      updated_at=now()
  where confirmation_token_hash=p_token_hash
    and status='PENDING_CONFIRMATION'
  returning id into sid;

  if sid is null then return false; end if;

  insert into newsletter_events(subscriber_id,event_type,provider)
  values(sid,'CONFIRMED','website');
  return true;
end;
$$;

create or replace function unsubscribe_newsletter_v01(p_token_hash text)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  sid uuid;
begin
  update newsletter_subscribers
  set status='UNSUBSCRIBED',
      unsubscribed_at=now(),
      confirmation_token_hash=null,
      updated_at=now()
  where unsubscribe_token_hash=p_token_hash
    and status in ('PENDING_CONFIRMATION','ACTIVE')
  returning id into sid;

  if sid is null then return false; end if;

  insert into newsletter_events(subscriber_id,event_type,provider)
  values(sid,'UNSUBSCRIBED','website');
  return true;
end;
$$;

revoke all on function request_newsletter_subscription_v01(text,text,text,text) from public,anon,authenticated;
revoke all on function confirm_newsletter_subscription_v01(text) from public,anon,authenticated;
revoke all on function unsubscribe_newsletter_v01(text) from public,anon,authenticated;
grant execute on function request_newsletter_subscription_v01(text,text,text,text) to service_role;
grant execute on function confirm_newsletter_subscription_v01(text) to service_role;
grant execute on function unsubscribe_newsletter_v01(text) to service_role;
