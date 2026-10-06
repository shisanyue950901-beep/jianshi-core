-- R7.10.1: pgcrypto hmac() expects bytea on current Supabase/Postgres runtime.

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

  signature := encode(
    hmac(
      convert_to(p_subscriber_id::text,'UTF8'),
      convert_to(signing_secret,'UTF8'),
      'sha256'
    ),
    'hex'
  );
  return p_subscriber_id::text || '.' || signature;
end;
$$;

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

  expected_signature := encode(
    hmac(
      convert_to(sid::text,'UTF8'),
      convert_to(signing_secret,'UTF8'),
      'sha256'
    ),
    'hex'
  );

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

revoke all on function newsletter_unsubscribe_token_v01(uuid) from public,anon,authenticated;
revoke all on function unsubscribe_newsletter_signed_v01(text) from public,anon,authenticated;
grant execute on function newsletter_unsubscribe_token_v01(uuid) to service_role;
grant execute on function unsubscribe_newsletter_signed_v01(text) to service_role;
