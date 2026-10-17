-- P4.1.5 current PyPI candidate shadow view.
-- Keeps earlier experimental rows out of the current candidate set.

create or replace view pypi_candidate_shadow_v01
with (security_invoker=true) as
select
  e.id as entity_id,
  e.source_external_id as package_name,
  e.source_url,
  e.metadata->>'candidate_rule_version' as candidate_rule_version,
  e.metadata->>'candidate_priority' as candidate_priority,
  (e.metadata->>'candidate_quality_score')::integer as candidate_quality_score,
  e.metadata->'candidate_categories' as candidate_categories,
  e.metadata->>'github_full_name' as github_full_name,
  coalesce((e.metadata->>'github_overlap_current_corpus')::boolean,false) as github_overlap_current_corpus,
  coalesce((e.metadata->>'has_non_github_project_url')::boolean,false) as has_non_github_project_url,
  e.metadata->>'cross_source_role' as cross_source_role,
  e.last_seen_at
from external_signal_entities e
join data_sources ds on ds.id=e.source_id
where ds.code='pypi'
  and e.entity_type='PYPI_PACKAGE'
  and e.metadata->>'candidate_rule_version'='P415_V1'
  and coalesce((e.metadata->>'candidate_match')::boolean,false)=true;

revoke all on pypi_candidate_shadow_v01 from public,anon,authenticated;
grant select on pypi_candidate_shadow_v01 to service_role;

comment on view pypi_candidate_shadow_v01 is
'P4.1.5 service-role-only current PyPI candidate set. Filters out prior experimental candidate-rule versions.';
