-- R7.10 Newsletter runtime.
-- Completes WAITLIST -> double opt-in -> ACTIVE -> daily digest -> durable unsubscribe.
-- Provider credentials remain fail-closed in Vault.

do $$
begin
  if not exists(select 1 from vault.decrypted_secrets where name='newsletter_signing_secret') then
    perform vault.create_secret(
      encode(gen_random_bytes(32),'hex'),
      'newsletter_signing_secret',
      'HMAC signing secret for durable JianShi newsletter unsubscribe links'
    );
  end if;
end $$;

create table if not exists newsletter_daily_sends (
  id bigserial primary key,
  subscriber_id uuid not null references newsletter_subscribers(id) on delete cascade,
  send_date date not null,
  status text not null default 'PREPARING'
    check(status in ('PREPARING','QUEUED','FAILED','DELIVERED','BOUNCED','COMPLAINED')),
  provider text not null default 'resend',
  provider_request_id text,
  subject text,
  error_code text,
  created_at timestamptz not null default now(),
  queued_at timestamptz,
  updated_at timestamptz not null default now(),
  unique(subscriber_id,send_date)
);
create index if not exists idx_newsletter_daily_sends_date_status
  on newsletter_daily_sends(send_date,status);

alter table newsletter_daily_sends enable row level security;
revoke all on newsletter_daily_sends from anon,authenticated;
revoke all on sequence newsletter_daily_sends_id_seq from anon,authenticated;
grant select,insert,update on newsletter_daily_sends to service_role;
grant usage,select on sequence newsletter_daily_sends_id_seq to service_role;

create or replace function newsletter_provider_ready_v01()
returns boolean
language sql
security definer
set search_path=public,vault
as $$
  select exists(select 1 from vault.decrypted_secrets where name='resend_api_key')
     and exists(select 1 from vault.decrypted_secrets where name='newsletter_from_email')
     and exists(select 1 from vault.decrypted_secrets where name='jianshi_project_url')
     and exists(select 1 from vault.decrypted_secrets where name='newsletter_signing_secret');
$$;

revoke all on function newsletter_provider_ready_v01() from public,anon,authenticated;
grant execute on function newsletter_provider_ready_v01() to service_role;

create or replace function newsletter_unsubscribe_token_v01(p_subscriber_id uuid)
returns text
language plpgsql
security definer
set search_path=public,vault
as $$
declare
  signing_secret text;
  signature text;
begin
  select decrypted_secret into signing_secret
  from vault.decrypted_secrets
  where name='newsletter_signing_secret'
  limit 1;

  if signing_secret is null then
    raise exception 'NEWSLETTER_SIGNING_SECRET_MISSING';
  end if;

  signature := encode(hmac(p_subscriber_id::text,signing_secret,'sha256'),'hex');
  return p_subscriber_id::text || '.' || signature;
end;
$$;

revoke all on function newsletter_unsubscribe_token_v01(uuid) from public,anon,authenticated;
grant execute on function newsletter_unsubscribe_token_v01(uuid) to service_role;

create or replace function unsubscribe_newsletter_signed_v01(p_token text)
returns boolean
language plpgsql
security definer
set search_path=public,vault
as $$
declare
  sid uuid;
  supplied_signature text;
  expected_signature text;
  signing_secret text;
  changed uuid;
begin
  if p_token is null or length(p_token)>256 or position('.' in p_token)=0 then
    return false;
  end if;

  begin
    sid := split_part(p_token,'.',1)::uuid;
  exception when others then
    return false;
  end;

  supplied_signature := split_part(p_token,'.',2);
  if length(supplied_signature)<>64 then
    return false;
  end if;

  select decrypted_secret into signing_secret
  from vault.decrypted_secrets
  where name='newsletter_signing_secret'
  limit 1;

  if signing_secret is null then
    return false;
  end if;

  expected_signature := encode(hmac(sid::text,signing_secret,'sha256'),'hex');
  if supplied_signature<>expected_signature then
    return false;
  end if;

  update newsletter_subscribers
  set status='UNSUBSCRIBED',
      unsubscribed_at=now(),
      confirmation_token_hash=null,
      updated_at=now()
  where id=sid
    and status in ('PENDING_CONFIRMATION','ACTIVE')
  returning id into changed;

  if changed is null then return false; end if;

  insert into newsletter_events(subscriber_id,event_type,provider,metadata)
  values(changed,'UNSUBSCRIBED','website',
         jsonb_build_object('token_type','SIGNED_HMAC_V1'));

  return true;
end;
$$;

revoke all on function unsubscribe_newsletter_signed_v01(text) from public,anon,authenticated;
grant execute on function unsubscribe_newsletter_signed_v01(text) to service_role;

create or replace function request_newsletter_subscription_v02(
  p_email text,
  p_source_path text,
  p_confirmation_token_hash text
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
        unsubscribe_token_hash=null,
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
      email,status,confirmation_token_hash,unsubscribe_token_hash,
      source_path,confirmation_requested_at
    )
    values(
      normalized_email,'PENDING_CONFIRMATION',p_confirmation_token_hash,null,
      left(coalesce(p_source_path,'/'),200),now()
    )
    returning id into sid;
  end if;

  insert into newsletter_events(subscriber_id,event_type,provider,metadata)
  values(sid,'SUBSCRIBE_REQUESTED','website',
         jsonb_build_object('result','ACCEPTED','subscription_version','V02'));

  return jsonb_build_object(
    'subscriber_id',sid,
    'status','PENDING_CONFIRMATION',
    'should_send',true
  );
end;
$$;

revoke all on function request_newsletter_subscription_v02(text,text,text) from public,anon,authenticated;
grant execute on function request_newsletter_subscription_v02(text,text,text) to service_role;

create or replace function prepare_waitlist_confirmation_v01(
  p_subscriber_id uuid,
  p_confirmation_token_hash text
)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  changed uuid;
begin
  update newsletter_subscribers
  set status='PENDING_CONFIRMATION',
      confirmation_token_hash=p_confirmation_token_hash,
      unsubscribe_token_hash=null,
      confirmation_requested_at=now(),
      updated_at=now()
  where id=p_subscriber_id
    and status='WAITLIST'
  returning id into changed;

  return changed is not null;
end;
$$;

create or replace function revert_pending_confirmation_to_waitlist_v01(
  p_subscriber_id uuid,
  p_confirmation_token_hash text
)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  changed uuid;
begin
  update newsletter_subscribers
  set status='WAITLIST',
      confirmation_token_hash=null,
      confirmation_requested_at=null,
      updated_at=now()
  where id=p_subscriber_id
    and status='PENDING_CONFIRMATION'
    and confirmation_token_hash=p_confirmation_token_hash
  returning id into changed;

  return changed is not null;
end;
$$;

revoke all on function prepare_waitlist_confirmation_v01(uuid,text) from public,anon,authenticated;
revoke all on function revert_pending_confirmation_to_waitlist_v01(uuid,text) from public,anon,authenticated;
grant execute on function prepare_waitlist_confirmation_v01(uuid,text) to service_role;
grant execute on function revert_pending_confirmation_to_waitlist_v01(uuid,text) to service_role;

create or replace function queue_newsletter_confirmation_v02(
  p_subscriber_id uuid,
  p_email text,
  p_confirm_token text
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
  unsubscribe_token text;
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
           jsonb_build_object('reason','EMAIL_PROVIDER_NOT_CONFIGURED','version','V02'));
    return jsonb_build_object('sent',false,'reason','EMAIL_PROVIDER_NOT_CONFIGURED');
  end if;

  unsubscribe_token := newsletter_unsubscribe_token_v01(p_subscriber_id);

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
        '<p>你申请接收「每天 Top 10 机会」。只有确认后，我们才会开始发送每日情报。</p>' ||
        '<p><a style="display:inline-block;padding:12px 18px;background:#171714;color:#fff;text-decoration:none" href="' ||
        endpoint || '/functions/v1/newsletter-subscribe?mode=confirm&token=' || p_confirm_token ||
        '">确认订阅</a></p>' ||
        '<p style="color:#777;font-size:12px">如果不是你本人提交，可以忽略这封邮件。</p>' ||
        '<p style="color:#777;font-size:12px"><a href="' ||
        endpoint || '/functions/v1/newsletter-subscribe?mode=unsubscribe&token=' || unsubscribe_token ||
        '">不再接收见势邮件</a></p></div>'
    ),
    timeout_milliseconds := 15000
  ) into request_id;

  insert into newsletter_events(subscriber_id,event_type,provider,provider_request_id,metadata)
  values(p_subscriber_id,'CONFIRMATION_QUEUED','resend',request_id::text,
         jsonb_build_object('version','V02'));

  return jsonb_build_object('sent',true,'request_id',request_id);
exception when others then
  insert into newsletter_events(subscriber_id,event_type,provider,metadata)
  values(p_subscriber_id,'CONFIRMATION_PROVIDER_PENDING','resend',
         jsonb_build_object('reason','PROVIDER_CALL_FAILED','version','V02'));
  return jsonb_build_object('sent',false,'reason','PROVIDER_CALL_FAILED');
end;
$$;

revoke all on function queue_newsletter_confirmation_v02(uuid,text,text) from public,anon,authenticated;
grant execute on function queue_newsletter_confirmation_v02(uuid,text,text) to service_role;

create or replace function queue_newsletter_daily_v01(
  p_subscriber_id uuid,
  p_email text,
  p_send_date date,
  p_subject text,
  p_html text
)
returns jsonb
language plpgsql
security definer
set search_path=public,vault,net
as $$
declare
  api_key text;
  from_email text;
  request_id bigint;
  send_id bigint;
begin
  if not exists(
    select 1 from newsletter_subscribers
    where id=p_subscriber_id and email=p_email and status='ACTIVE'
  ) then
    return jsonb_build_object('sent',false,'reason','SUBSCRIBER_NOT_ACTIVE');
  end if;

  select id into send_id
  from newsletter_daily_sends
  where subscriber_id=p_subscriber_id and send_date=p_send_date;

  if send_id is not null then
    return jsonb_build_object('sent',false,'reason','ALREADY_PROCESSED','send_id',send_id);
  end if;

  select decrypted_secret into api_key
  from vault.decrypted_secrets where name='resend_api_key' limit 1;
  select decrypted_secret into from_email
  from vault.decrypted_secrets where name='newsletter_from_email' limit 1;

  if api_key is null or from_email is null then
    return jsonb_build_object('sent',false,'reason','EMAIL_PROVIDER_NOT_CONFIGURED');
  end if;

  insert into newsletter_daily_sends(subscriber_id,send_date,status,subject)
  values(p_subscriber_id,p_send_date,'PREPARING',left(p_subject,300))
  returning id into send_id;

  select net.http_post(
    url := 'https://api.resend.com/emails',
    headers := jsonb_build_object(
      'Authorization','Bearer ' || api_key,
      'Content-Type','application/json'
    ),
    body := jsonb_build_object(
      'from',from_email,
      'to',jsonb_build_array(p_email),
      'subject',p_subject,
      'html',p_html
    ),
    timeout_milliseconds := 15000
  ) into request_id;

  update newsletter_daily_sends
  set status='QUEUED',
      provider_request_id=request_id::text,
      queued_at=now(),
      updated_at=now()
  where id=send_id;

  update newsletter_subscribers
  set last_sent_at=now(),updated_at=now()
  where id=p_subscriber_id;

  insert into newsletter_events(subscriber_id,event_type,provider,provider_request_id,metadata)
  values(
    p_subscriber_id,'SEND_QUEUED','resend',request_id::text,
    jsonb_build_object('send_date',p_send_date,'daily_send_id',send_id)
  );

  return jsonb_build_object('sent',true,'request_id',request_id,'send_id',send_id);
exception when others then
  if send_id is not null then
    update newsletter_daily_sends
    set status='FAILED',error_code='PROVIDER_CALL_FAILED',updated_at=now()
    where id=send_id;
  end if;
  return jsonb_build_object('sent',false,'reason','PROVIDER_CALL_FAILED');
end;
$$;

revoke all on function queue_newsletter_daily_v01(uuid,text,date,text,text)
  from public,anon,authenticated;
grant execute on function queue_newsletter_daily_v01(uuid,text,date,text,text)
  to service_role;

create or replace view newsletter_runtime_metrics_v01 as
select
  (select count(*) from newsletter_subscribers where status='WAITLIST') as waitlist,
  (select count(*) from newsletter_subscribers where status='PENDING_CONFIRMATION') as pending_confirmation,
  (select count(*) from newsletter_subscribers where status='ACTIVE') as active,
  (select count(*) from newsletter_subscribers where status='UNSUBSCRIBED') as unsubscribed,
  (select count(*) from newsletter_daily_sends where send_date=(now() at time zone 'Asia/Shanghai')::date) as daily_rows_today,
  (select count(*) from newsletter_daily_sends where send_date=(now() at time zone 'Asia/Shanghai')::date and status='QUEUED') as daily_queued_today;

alter view newsletter_runtime_metrics_v01 set (security_invoker=true);
revoke all on newsletter_runtime_metrics_v01 from anon,authenticated;

comment on function newsletter_unsubscribe_token_v01(uuid) is
'R7.10 deterministic HMAC unsubscribe token. Raw token is not stored; old email unsubscribe links remain valid until signing-secret rotation.';
comment on function queue_newsletter_daily_v01(uuid,text,date,text,text) is
'R7.10 idempotent daily digest queue. A subscriber can be queued at most once per send_date.';
