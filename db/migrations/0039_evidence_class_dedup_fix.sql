-- R8.7 staging/upgrade repair: deduplicate entities that match multiple discovery rules.
create or replace view opportunity_evidence_class_counts_v01 as
select
  o.id as opportunity_id,
  count(distinct oe.entity_id) filter (
    where r.evidence_class='TECHNICAL_SUPPLY'
      and r.counts_for_public_validation=true
  ) as technical_evidence_count,
  count(distinct oe.entity_id) filter (
    where r.evidence_class='COMMERCIAL_PROOF'
      and r.counts_for_public_validation=true
  ) as commercial_evidence_count,
  count(distinct oe.entity_id) filter (
    where r.evidence_class='DEMAND_SIGNAL'
      and r.counts_for_public_validation=true
  ) as demand_evidence_count,
  count(distinct r.evidence_class) filter (
    where r.counts_for_public_validation=true
      and oe.entity_id is not null
  ) as validation_class_count
from opportunities o
left join opportunity_evidence oe
  on oe.opportunity_id=o.id
 and oe.active=true
 and oe.rule_version='OPP_V0.1'
left join evidence_class_rules r
  on r.evidence_type=oe.evidence_type
group by o.id;

alter view opportunity_evidence_class_counts_v01 set (security_invoker=true);
