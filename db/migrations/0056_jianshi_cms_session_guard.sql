-- F2.1 G1-E | STAGING ONLY. Session check for a trusted CMS gateway.
-- A signed token is verified with GoTrue BEFORE this SQL helper is called.
-- SECURITY DEFINER is deliberately limited to a single boolean existence check:
-- service_role has no SELECT on auth.sessions, no user data is returned.
-- Private schema + function EXECUTE restricted to service_role.
create or replace function jianshi_cms.session_is_active(
  p_user_id uuid,
  p_session_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce(
    p_user_id is not null and p_session_id is not null
    and exists (
      select 1
      from auth.sessions s
      join auth.users u on u.id = s.user_id
      where s.id = p_session_id
        and s.user_id = p_user_id
        and u.deleted_at is null
        and (s.not_after is null or s.not_after > now())
    ),false
  );
$$;

revoke all on function jianshi_cms.session_is_active(uuid,uuid)
  from PUBLIC, anon, authenticated;
grant execute on function jianshi_cms.session_is_active(uuid,uuid)
  to service_role;
comment on function jianshi_cms.session_is_active(uuid,uuid) is
  'Private service-only boolean check of verified JWT session ID against auth.sessions; NEVER expose to browsers or PostgREST public schema.';

-- No secret keys, no user accounts, no test sessions, no feature flag changes.

-- PostgREST has only public exposed by design. These narrow, INVOKER
-- wrappers are service_role-only and delegate to the private schema.
-- Never grant to browser roles and never return raw CMS bodies or audit data.
create or replace function public.cms_internal_session_v01(
  p_user_id uuid, p_session_id uuid
) returns boolean
language sql stable security invoker
set search_path = ''
as $$
 select jianshi_cms.session_is_active(p_user_id,p_session_id);
$$;
revoke all on function public.cms_internal_session_v01(uuid,uuid)
  from PUBLIC,anon,authenticated;
grant execute on function public.cms_internal_session_v01(uuid,uuid)
  to service_role;

create or replace function public.cms_internal_write_v01(
  p_actor uuid,
  p_operation text,
  p_payload jsonb
) returns jsonb
language plpgsql security invoker
set search_path = ''
as $$
declare
  v_id uuid;
  v_revision integer;
begin
  -- Always deny before dispatch when user account or CMS not ready.
  perform jianshi_cms.ensure_write_gate(p_actor,array['EDITOR','REVIEWER','PUBLISHER']);
  if p_payload is null or jsonb_typeof(p_payload)<>'object' then
    raise exception 'CMS_INVALID_PAYLOAD' using errcode='22023';
  end if;
  if p_operation='CREATE' then
    v_id:=jianshi_cms.create_draft(
      p_actor,p_payload->>'content_key',p_payload->>'content_type',
      p_payload->'content',p_payload->'sources',
      (p_payload->>'request_id')::uuid);
    return jsonb_build_object('content_id',v_id);
  elsif p_operation='EDIT' then
    v_revision:=jianshi_cms.edit_draft(
      p_actor,(p_payload->>'content_id')::uuid,
      (p_payload->>'expected_revision')::integer,
      p_payload->'content',p_payload->'sources',
      (p_payload->>'rights_declared')::boolean,
      (p_payload->>'facts_checked')::boolean,
      (p_payload->>'request_id')::uuid);
    return jsonb_build_object('revision',v_revision);
  elsif p_operation='STATE' then
    v_revision:=jianshi_cms.change_review_state(
      p_actor,(p_payload->>'content_id')::uuid,
      (p_payload->>'expected_revision')::integer,
      p_payload->>'next_state',
      (p_payload->>'request_id')::uuid,
      p_payload->>'reason');
    return jsonb_build_object('revision',v_revision);
  end if;
  raise exception 'CMS_OPERATION_NOT_ALLOWED' using errcode='22023';
end;
$$;
revoke all on function public.cms_internal_write_v01(uuid,text,jsonb)
  from PUBLIC,anon,authenticated;
grant execute on function public.cms_internal_write_v01(uuid,text,jsonb)
  to service_role;

comment on function public.cms_internal_write_v01(uuid,text,jsonb) is
 'F2.1 G1-E: narrowly scoped service_role-only RPC facade. The trusted Edge gateway must independently verify GoTrue user+session; CMS and Auth gates stay OFF.';
