-- R3 security hardening after Supabase Advisor.
-- Views explicitly run with caller permissions/RLS instead of creator permissions.
alter view marketplace_listing_history set (security_invoker = true);
alter view github_repository_momentum set (security_invoker = true);
alter view github_repository_quality set (security_invoker = true);
alter view github_hot_current set (security_invoker = true);
alter view github_rising_current set (security_invoker = true);

create index if not exists idx_signals_source_id on signals(source_id);

-- pg_net is intentionally left in its installed schema because this Supabase build
-- reports extrelocatable=false. Moving it is not supported; the linter warning is accepted.
