-- P4.5B FK index hardening for Staging shadow tables.
-- No behavior, publication, scoring, or mapping-rule changes.

create index if not exists idx_child_registry_parent_opportunity
  on child_opportunity_shadow_registry(parent_opportunity_id);

create index if not exists idx_child_evidence_matches_rule_id
  on child_marketplace_evidence_matches(rule_id);

create index if not exists idx_child_evidence_matches_source_id
  on child_marketplace_evidence_matches(source_id);
