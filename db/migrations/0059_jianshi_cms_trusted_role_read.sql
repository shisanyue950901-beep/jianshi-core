-- F2.1 G2-H.2: STAGING ONLY, service-only role resolution after GoTrue JWT + session check.
-- NO browser role grants, no feature-flag changes and no production DDL.
create or replace function public.cms_internal_actor_role_v01(p_actor uuid)
returns text
language sql security invoker stable
set search_path = ''
as $$
  select jianshi_cms.ensure_write_gate(p_actor, ARRAY['EDITOR','REVIEWER','PUBLISHER']::text[]);
$$;
revoke all on function public.cms_internal_actor_role_v01(uuid) from PUBLIC, anon, authenticated;
grant execute on function public.cms_internal_actor_role_v01(uuid) to service_role;
comment on function public.cms_internal_actor_role_v01(uuid)
is 'Staging trusted server only. Resolve a current editor role only after verified GoTrue JWT and active session; the existing gate must pass.';
