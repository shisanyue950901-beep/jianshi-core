-- P4.11 | Fail-closed public source disclosure ACL.
-- Already executed against Production and Staging on 2026-10-08.
-- Re-runnable safely; no ingestion data or schema is changed.
-- Service-role Edge Functions continue to read these views.
begin;

revoke select on
  public.github_hot_current,
  public.github_repository_momentum,
  public.github_repository_quality,
  public.github_rising_current,
  public.marketplace_exit_benchmarks_v01,
  public.marketplace_listing_history,
  public.marketplace_observed_exits_v01,
  public.opportunity_github_acceleration_v01,
  public.public_github_evidence_v01,
  public.public_market_evidence_v01,
  public.public_tech_signals_v01,
  public.source_policy_effective_v01,
  public.source_provenance_effective_v01
from anon, authenticated;

commit;

-- Must return 0 after applying, in every deployed environment.
select count(*) as remaining_sensitive_grants
from pg_class c
join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public'
  and c.relname in (
    'github_hot_current','github_repository_momentum','github_repository_quality',
    'github_rising_current','marketplace_exit_benchmarks_v01',
    'marketplace_listing_history','marketplace_observed_exits_v01',
    'opportunity_github_acceleration_v01','public_github_evidence_v01',
    'public_market_evidence_v01','public_tech_signals_v01',
    'source_policy_effective_v01','source_provenance_effective_v01'
  )
  and (has_table_privilege('anon',c.oid,'SELECT')
    or has_table_privilege('authenticated',c.oid,'SELECT'));
