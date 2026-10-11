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
