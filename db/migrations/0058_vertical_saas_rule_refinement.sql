-- P4.5D refine vertical SaaS review queue from human audit.
-- P45B broad SaaS rule is disabled and replaced by two non-overlapping rules.
-- Expected Staging outcome from the audited six rows:
-- 4 HIGH auto-approved + 1 MEDIUM review + 1 excluded from SaaS child mapping.

update child_marketplace_mapping_rules
set
  active=false,
  notes=concat_ws(' | ',nullif(notes,''),'P4.5D superseded after six-row human audit'),
  updated_at=now()
where rule_code='P45B_SAAS_VERTICAL';

insert into child_marketplace_mapping_rules(
  rule_code,child_slug,source_id,any_monetizations,all_monetizations,
  excluded_monetizations,title_contains_all,require_nonempty_niches,
  confidence,auto_approve,rule_version,active,notes
)
select
  x.rule_code,
  'vertical-micro-saas',
  ds.id,
  array['SaaS']::text[],
  array[]::text[],
  array[]::text[],
  x.title_contains_all,
  true,
  x.confidence,
  x.auto_approve,
  'P45D_V1',
  true,
  x.notes
from data_sources ds
cross join (
  values
    (
      'P45D_SAAS_PRIMARY_TITLE',
      array['SaaS Business']::text[],
      'HIGH',
      true,
      'Primary marketplace title explicitly classifies the asset as SaaS Business and niche is non-empty.'
    ),
    (
      'P45D_SAAS_SUBSCRIPTION_MIXED',
      array['Subscription Business']::text[],
      'MEDIUM',
      false,
      'Mixed Subscription + SaaS classification remains human-reviewable because SaaS is not the primary marketplace title.'
    )
) as x(rule_code,title_contains_all,confidence,auto_approve,notes)
where ds.code='empire_flippers'
on conflict(rule_code) do update set
  source_id=excluded.source_id,
  any_monetizations=excluded.any_monetizations,
  title_contains_all=excluded.title_contains_all,
  require_nonempty_niches=excluded.require_nonempty_niches,
  confidence=excluded.confidence,
  auto_approve=excluded.auto_approve,
  rule_version=excluded.rule_version,
  active=true,
  notes=excluded.notes,
  updated_at=now();

comment on table child_marketplace_mapping_rules is
'P4.5D: vertical SaaS mapping now distinguishes primary SaaS-title assets from mixed Subscription+SaaS assets. Digital Product-primary assets are not mapped to the SaaS child unless a future explicit rule is approved.';
