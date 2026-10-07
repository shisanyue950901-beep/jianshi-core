-- R8.7 Evidence-class validation gate.
-- Future sources cannot make an opportunity public merely by increasing source_count.
-- Validation requires at least one TECHNICAL_SUPPLY class AND one COMMERCIAL_PROOF class.

create table if not exists evidence_class_rules (
  evidence_type text primary key,
  evidence_class text not null
    check (evidence_class in (
      'TECHNICAL_SUPPLY',
      'COMMERCIAL_PROOF',
      'DEMAND_SIGNAL',
      'DISTRIBUTION_SIGNAL',
      'OTHER'
    )),
  counts_for_public_validation boolean not null default false,
  notes text,
  updated_at timestamptz not null default now()
);

alter table evidence_class_rules enable row level security;
revoke all on evidence_class_rules from anon,authenticated;

insert into evidence_class_rules(
  evidence_type,evidence_class,counts_for_public_validation,notes
)
values
(
  'GITHUB_REPOSITORY',
  'TECHNICAL_SUPPLY',
  true,
  'Open-source technical supply signal. Never substitutes for commercial proof.'
),
(
  'MARKETPLACE_LISTING',
  'COMMERCIAL_PROOF',
  true,
  'Licensed marketplace financial/listing evidence. Required commercial class for current public validation.'
)
on conflict(evidence_type)
do update set
  evidence_class=excluded.evidence_class,
  counts_for_public_validation=excluded.counts_for_public_validation,
  notes=excluded.notes,
  updated_at=now();

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

create or replace view opportunity_rank_current as
select
  m.opportunity_id,
  m.slug,
  m.title,
  m.category,
  m.china_fit,
  m.solo_founder_fit,
  m.content_prior,
  m.github_repo_count,
  m.github_top5_rank_score,
  m.market_listing_count,
  m.avg_monthly_profit,
  m.avg_profit_margin,
  m.avg_listing_multiple,
  m.avg_hours_per_week,
  m.evidence_count,
  m.source_count,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='HEAT') as heat_score,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='CONTENT') as content_score,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='BUILD') as build_score,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='BUSINESS') as business_score,
  case
    when coalesce(ec.technical_evidence_count,0)>0
     and coalesce(ec.commercial_evidence_count,0)>0
      then 'MULTI_SOURCE'
    else 'SINGLE_SOURCE'
  end as resonance_status,
  (
    coalesce(ec.technical_evidence_count,0)>0
    and coalesce(ec.commercial_evidence_count,0)>0
    and m.evidence_count>=5
  ) as public_ready,
  m.sold_status_count,
  m.sold_sample_ready,
  m.median_sold_status_days_on_market,
  m.median_sold_status_annual_profit,
  m.sold_activity_score,
  coalesce(ec.technical_evidence_count,0) as technical_evidence_count,
  coalesce(ec.commercial_evidence_count,0) as commercial_evidence_count,
  coalesce(ec.demand_evidence_count,0) as demand_evidence_count,
  coalesce(ec.validation_class_count,0) as validation_class_count,
  case
    when coalesce(ec.technical_evidence_count,0)>0
     and coalesce(ec.commercial_evidence_count,0)>0
      then 'TECH_PLUS_COMMERCIAL'
    when coalesce(ec.commercial_evidence_count,0)>0
      then 'COMMERCIAL_ONLY'
    when coalesce(ec.technical_evidence_count,0)>0
      then 'TECHNICAL_ONLY'
    else 'INSUFFICIENT'
  end as validation_class
from opportunity_metrics_v01 m
left join opportunity_evidence_class_counts_v01 ec
  on ec.opportunity_id=m.opportunity_id;

alter view opportunity_rank_current set (security_invoker=true);

create or replace view public_opportunity_catalog_v01 as
select
  o.id as opportunity_id,
  o.slug,
  o.title,
  o.category,
  o.thesis,
  o.problem,
  o.target_customer,
  o.business_model,
  o.china_fit,
  o.solo_founder_fit,
  r.github_repo_count,
  r.market_listing_count,
  r.source_count,
  r.evidence_count,
  r.heat_score,
  r.content_score,
  r.build_score,
  r.business_score,
  r.resonance_status,
  r.public_ready,
  case when r.public_ready then 'OPPORTUNITY' else 'WATCH' end as visibility_state,
  round((
    coalesce(r.heat_score,0)*0.30 +
    coalesce(r.content_score,0)*0.20 +
    coalesce(r.build_score,0)*0.25 +
    coalesce(r.business_score,0)*0.25
  )::numeric,2) as overall_score,
  o.updated_at,
  (
    select max(ss.calculated_at)
    from score_snapshots ss
    where ss.opportunity_id=o.id
      and ss.score_version='OPP_V0.2'
  ) as score_updated_at,
  r.sold_status_count,
  r.sold_sample_ready,
  r.median_sold_status_days_on_market,
  r.median_sold_status_annual_profit,
  r.sold_activity_score,
  r.technical_evidence_count,
  r.commercial_evidence_count,
  r.demand_evidence_count,
  r.validation_class_count,
  r.validation_class
from opportunities o
join opportunity_rank_current r on r.opportunity_id=o.id
where o.status='ACTIVE';

alter view public_opportunity_catalog_v01 set (security_invoker=true);

comment on table evidence_class_rules is
'R8.7 explicit evidence semantics. Adding a future source/evidence type does not automatically satisfy public validation.';
comment on view opportunity_evidence_class_counts_v01 is
'Counts validation evidence by semantic class, independent from raw source count.';
comment on view opportunity_rank_current is
'R8.7 public_ready requires technical evidence + commercial proof + >=5 total active evidence. Two trend sources cannot substitute for commercial proof.';
