-- R7.5.1: represent provider-unavailable signups as a real WAITLIST state.
-- This avoids creating confirmation-token hashes that can never be re-sent.

alter table newsletter_subscribers
  drop constraint if exists newsletter_subscribers_status_check;

alter table newsletter_subscribers
  alter column unsubscribe_token_hash drop not null;

alter table newsletter_subscribers
  add constraint newsletter_subscribers_status_check
  check (status in (
    'WAITLIST',
    'PENDING_CONFIRMATION',
    'ACTIVE',
    'UNSUBSCRIBED',
    'BOUNCED',
    'COMPLAINED'
  ));

create or replace function request_newsletter_waitlist_v01(
  p_email text,
  p_source_path text
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
    return jsonb_build_object('subscriber_id',existing.id,'status','ACTIVE');
  end if;

  if found and existing.status='WAITLIST'
     and existing.consent_at > now()-interval '10 minutes' then
    insert into newsletter_events(subscriber_id,event_type,provider,metadata)
    values(existing.id,'SUBSCRIBE_REQUESTED','website',jsonb_build_object('result','WAITLIST_COOLDOWN'));
    return jsonb_build_object('subscriber_id',existing.id,'status','WAITLIST');
  end if;

  if found and existing.status='PENDING_CONFIRMATION' then
    insert into newsletter_events(subscriber_id,event_type,provider,metadata)
    values(existing.id,'SUBSCRIBE_REQUESTED','website',jsonb_build_object('result','ALREADY_PENDING_CONFIRMATION'));
    return jsonb_build_object('subscriber_id',existing.id,'status','PENDING_CONFIRMATION');
  end if;

  if found then
    update newsletter_subscribers
    set status='WAITLIST',
        confirmation_token_hash=null,
        unsubscribe_token_hash=null,
        source_path=left(coalesce(p_source_path,'/'),200),
        consent_version='NEWSLETTER_V1_20261006',
        consent_at=now(),
        confirmation_requested_at=null,
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
      normalized_email,'WAITLIST',null,null,left(coalesce(p_source_path,'/'),200),null
    )
    returning id into sid;
  end if;

  insert into newsletter_events(subscriber_id,event_type,provider,metadata)
  values(sid,'SUBSCRIBE_REQUESTED','website',jsonb_build_object('result','WAITLIST'));

  return jsonb_build_object('subscriber_id',sid,'status','WAITLIST');
end;
$$;

revoke all on function request_newsletter_waitlist_v01(text,text) from public,anon,authenticated;
grant execute on function request_newsletter_waitlist_v01(text,text) to service_role;

drop view if exists newsletter_internal_metrics_v01;
create view newsletter_internal_metrics_v01 as
select
  count(*) as total,
  count(*) filter (where status='WAITLIST') as waitlist,
  count(*) filter (where status='PENDING_CONFIRMATION') as pending_confirmation,
  count(*) filter (where status='ACTIVE') as active,
  count(*) filter (where status='UNSUBSCRIBED') as unsubscribed,
  count(*) filter (where status='BOUNCED') as bounced,
  max(created_at) as latest_signup_at
from newsletter_subscribers;

alter view newsletter_internal_metrics_v01 set (security_invoker=true);
revoke all on newsletter_internal_metrics_v01 from anon,authenticated;

comment on function request_newsletter_waitlist_v01(text,text) is
'R7.5.1 provider-unavailable signup path. Stores consent/email without generating unrecoverable confirmation tokens.';
