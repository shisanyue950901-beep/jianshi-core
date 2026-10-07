-- R8.7 staging/upgrade repair: deduplicate entities that match multiple discovery rules.
create or replace view opportunity_evidence_class_counts_v01 as
select
  o.id as opportunity_id,
  count(distinct oe.entity_id) filter (
    where r.evidence_class='TECHNICAL_SUPPLY'
      and r.counts_for_public_validation=true
      and gh.github_repository_id is not null
  ) as technical_evidence_count,
  count(distinct oe.entity_id) filter (
    where r.evidence_class='COMMERCIAL_PROOF'
      and r.counts_for_public_validation=true
      and ml.id is not null
      and ml.active=true
  ) as commercial_evidence_count,
  count(distinct oe.entity_id) filter (
    where r.evidence_class='DEMAND_SIGNAL'
      and r.counts_for_public_validation=true
      and false
  ) as demand_evidence_count,
  count(distinct r.evidence_class) filter (
    where r.counts_for_public_validation=true
      and (
        (r.evidence_class='TECHNICAL_SUPPLY' and gh.github_repository_id is not null)
        or (r.evidence_class='COMMERCIAL_PROOF' and ml.id is not null and ml.active=true)
      )
  ) as validation_class_count
from opportunities o
left join opportunity_evidence oe
  on oe.opportunity_id=o.id
 and oe.active=true
 and oe.rule_version='OPP_V0.1'
left join evidence_class_rules r
  on r.evidence_type=oe.evidence_type
left join github_hot_current gh
  on oe.evidence_type='GITHUB_REPOSITORY'
 and gh.github_repository_id=oe.entity_id
left join marketplace_listings ml
  on oe.evidence_type='MARKETPLACE_LISTING'
 and ml.id=oe.entity_id
group by o.id;
alter view opportunity_evidence_class_counts_v01 set (security_invoker=true);
