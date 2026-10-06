-- R5 public projection: curated, derived, read-only surfaces only.
-- Raw/private tables remain inaccessible to public clients.

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
    coalesce(r.heat_score,0) * 0.30 +
    coalesce(r.content_score,0) * 0.20 +
    coalesce(r.build_score,0) * 0.25 +
    coalesce(r.business_score,0) * 0.25
  )::numeric,2) as overall_score,
  o.updated_at,
  (
    select max(ss.calculated_at)
    from score_snapshots ss
    where ss.opportunity_id=o.id
      and ss.score_version='OPP_V0.1'
  ) as score_updated_at
from opportunities o
join opportunity_rank_current r on r.opportunity_id=o.id
where o.status='ACTIVE';

alter view public_opportunity_catalog_v01 set (security_invoker=true);

create or replace view public_github_evidence_v01 as
select
  oe.opportunity_id,
  gr.id as github_repository_id,
  gr.full_name,
  gr.description,
  gr.html_url,
  gh.language,
  gh.stars,
  gh.forks,
  gh.quality_score,
  gh.heat_score,
  gh.rank_score,
  oe.rule_code,
  oe.last_seen_at
from opportunity_evidence oe
join github_repositories gr on gr.id=oe.entity_id
join github_hot_current gh on gh.github_repository_id=gr.id
where oe.active=true
  and oe.rule_version='OPP_V0.1'
  and oe.evidence_type='GITHUB_REPOSITORY';

alter view public_github_evidence_v01 set (security_invoker=true);

create or replace view public_market_evidence_v01 as
select
  oe.opportunity_id,
  ml.id as marketplace_listing_id,
  ml.listing_number,
  ml.public_title,
  ml.listing_status,
  ml.listing_price,
  ml.unpriced,
  ml.average_monthly_net_profit,
  ml.average_monthly_gross_revenue,
  ml.profit_margin,
  ml.listing_multiple,
  ml.annual_listing_multiple,
  ml.hours_worked_per_week,
  ml.monetizations,
  ml.niches,
  ml.source_url,
  oe.rule_code,
  oe.last_seen_at
from opportunity_evidence oe
join marketplace_listings ml on ml.id=oe.entity_id
where oe.active=true
  and oe.rule_version='OPP_V0.1'
  and oe.evidence_type='MARKETPLACE_LISTING'
  and ml.active=true;

alter view public_market_evidence_v01 set (security_invoker=true);

create or replace view public_system_stats_v01 as
select
  (select count(*) from marketplace_listings where active=true) as marketplace_listings,
  (select count(*) from github_repositories where archived=false and is_fork=false) as github_repositories,
  (select count(*) from signals) as signals,
  (select count(*) from public_opportunity_catalog_v01 where public_ready=true) as validated_opportunities,
  (select count(*) from public_opportunity_catalog_v01 where public_ready=false) as watch_opportunities,
  (select max(finished_at) from pipeline_runs where status='SUCCESS' and quality_gate_status='PASS') as latest_pipeline_at;

alter view public_system_stats_v01 set (security_invoker=true);

comment on view public_opportunity_catalog_v01 is
'R5 curated public projection. OPPORTUNITY requires conservative multi-source Gate; WATCH is explicitly single-source observation.';
