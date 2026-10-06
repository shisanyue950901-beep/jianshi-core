-- R7.8 / OPP_V0.2
-- Sold-status activity is a weak auxiliary BUSINESS signal only.
-- It does NOT create a new source class and never represents transaction price.

create or replace view opportunity_sold_status_metrics_v01 as
with mapping as (
  select o.id as opportunity_id,m.monetizations
  from (
    values
      ('solo-saas',array['SaaS']::text[]),
      ('ecommerce-brands',array['Amazon FBA','Amazon FBM','eCommerce','DropShipping']::text[]),
      ('affiliate-content',array['Affiliate','Amazon Associates','Display Advertising']::text[]),
      ('creator-media',array['YouTube','Newsletter','Digital Product','Info Product']::text[])
  ) as m(slug,monetizations)
  join opportunities o on o.slug=m.slug
),
sold as (
  select
    m.opportunity_id,
    ml.id as marketplace_listing_id,
    ml.days_on_marketplace,
    ml.average_annual_net_profit
  from mapping m
  join marketplace_listings ml
    on ml.source_id=(select id from data_sources where code='empire_flippers')
   and ml.listing_status='Sold'
   and ml.monetizations ?| m.monetizations
),
agg as (
  select
    opportunity_id,
    count(distinct marketplace_listing_id) as sold_status_count,
    round(
      percentile_cont(0.5) within group(order by days_on_marketplace)
        filter (where days_on_marketplace is not null)::numeric,
      1
    ) as median_sold_status_days_on_market,
    round(
      percentile_cont(0.5) within group(order by average_annual_net_profit)
        filter (where average_annual_net_profit is not null)::numeric,
      2
    ) as median_sold_status_annual_profit
  from sold
  group by opportunity_id
)
select
  opportunity_id,
  sold_status_count,
  (sold_status_count>=5) as sold_sample_ready,
  median_sold_status_days_on_market,
  median_sold_status_annual_profit,
  round(
    case
      when sold_status_count>=5
        then least(100.0,100.0*ln(sold_status_count+1.0)/ln(26.0))
      else 0.0
    end::numeric,
    2
  ) as sold_activity_score
from agg;

alter view opportunity_sold_status_metrics_v01 set (security_invoker=true);

create or replace view opportunity_metrics_v01 as
with github_ranked as (
  select
    oe.opportunity_id,
    gh.rank_score,
    row_number() over (
      partition by oe.opportunity_id
      order by gh.rank_score desc, gh.stars desc
    ) as rn
  from opportunity_evidence oe
  join github_hot_current gh on gh.github_repository_id=oe.entity_id
  where oe.active=true
    and oe.rule_version='OPP_V0.1'
    and oe.evidence_type='GITHUB_REPOSITORY'
),
github_agg as (
  select
    opportunity_id,
    count(*) as github_repo_count,
    avg(rank_score) filter (where rn<=5) as github_top5_rank_score
  from github_ranked
  group by opportunity_id
),
market_agg as (
  select
    oe.opportunity_id,
    count(*) as market_listing_count,
    avg(ml.average_monthly_net_profit) filter (where ml.average_monthly_net_profit is not null) as avg_monthly_profit,
    avg(ml.profit_margin) filter (where ml.profit_margin is not null) as avg_profit_margin,
    avg(ml.listing_multiple) filter (where ml.listing_multiple is not null) as avg_listing_multiple,
    avg(ml.hours_worked_per_week) filter (where ml.hours_worked_per_week is not null) as avg_hours_per_week
  from opportunity_evidence oe
  join marketplace_listings ml on ml.id=oe.entity_id
  where oe.active=true
    and oe.rule_version='OPP_V0.1'
    and oe.evidence_type='MARKETPLACE_LISTING'
    and ml.active=true
  group by oe.opportunity_id
)
select
  o.id as opportunity_id,
  o.slug,
  o.title,
  o.category,
  o.china_fit,
  o.solo_founder_fit,
  p.content_prior,
  coalesce(g.github_repo_count,0) as github_repo_count,
  round(coalesce(g.github_top5_rank_score,0)::numeric,2) as github_top5_rank_score,
  coalesce(m.market_listing_count,0) as market_listing_count,
  round(coalesce(m.avg_monthly_profit,0)::numeric,2) as avg_monthly_profit,
  round(coalesce(m.avg_profit_margin,0)::numeric,2) as avg_profit_margin,
  round(coalesce(m.avg_listing_multiple,0)::numeric,2) as avg_listing_multiple,
  round(coalesce(m.avg_hours_per_week,0)::numeric,2) as avg_hours_per_week,
  (coalesce(g.github_repo_count,0)+coalesce(m.market_listing_count,0)) as evidence_count,
  ((case when coalesce(g.github_repo_count,0)>0 then 1 else 0 end) +
   (case when coalesce(m.market_listing_count,0)>0 then 1 else 0 end)) as source_count,
  coalesce(s.sold_status_count,0) as sold_status_count,
  coalesce(s.sold_sample_ready,false) as sold_sample_ready,
  s.median_sold_status_days_on_market,
  s.median_sold_status_annual_profit,
  coalesce(s.sold_activity_score,0)::numeric as sold_activity_score
from opportunities o
join opportunity_profiles p on p.opportunity_id=o.id and p.engine_version='OPP_V0.1'
left join github_agg g on g.opportunity_id=o.id
left join market_agg m on m.opportunity_id=o.id
left join opportunity_sold_status_metrics_v01 s on s.opportunity_id=o.id
where o.status='ACTIVE';

alter view opportunity_metrics_v01 set (security_invoker=true);

create or replace view opportunity_scored_v01 as
with c as (
  select
    m.*,
    least(100.0,greatest(0.0,m.github_top5_rank_score)) as github_strength,
    least(100.0,greatest(0.0,
      case when m.market_listing_count>0
           then 100.0 * ln(m.market_listing_count + 1.0) / ln(51.0)
           else 0.0 end
    )) as market_activity_score,
    least(100.0,greatest(0.0,
      case when m.avg_monthly_profit>0
           then 100.0 * ln(m.avg_monthly_profit + 1.0) / ln(50001.0)
           else 0.0 end
    )) as money_strength,
    least(100.0,greatest(0.0,m.avg_profit_margin)) as margin_strength,
    least(100.0,greatest(0.0,m.avg_listing_multiple * 2.0)) as multiple_strength,
    least(100.0,greatest(0.0,
      case when m.avg_hours_per_week>0
           then 100.0 - m.avg_hours_per_week * 3.0
           else m.solo_founder_fit end
    )) as runtime_solo_score,
    least(100.0,greatest(0.0,m.evidence_count * 5.0)) as evidence_breadth_score
  from opportunity_metrics_v01 m
),
s as (
  select
    c.*,
    case
      when github_strength>0 and market_activity_score>0
        then github_strength*0.55 + market_activity_score*0.45
      else greatest(github_strength,market_activity_score)
    end as heat_score_raw,
    case
      when market_listing_count>0
        then money_strength*0.35 + margin_strength*0.25 + multiple_strength*0.20 + market_activity_score*0.20
      else least(45.0,10.0 + github_strength*0.35)
    end as business_score_base,
    case
      when sold_sample_ready then least(5.0,sold_activity_score*0.05)
      else 0.0
    end as sold_activity_bonus,
    github_strength*0.30 + solo_founder_fit*0.25 + china_fit*0.20 + market_activity_score*0.25 as build_score_raw
  from c
)
select
  opportunity_id,
  slug,
  title,
  category,
  china_fit,
  solo_founder_fit,
  content_prior,
  github_repo_count,
  github_top5_rank_score,
  market_listing_count,
  avg_monthly_profit,
  avg_profit_margin,
  avg_listing_multiple,
  avg_hours_per_week,
  evidence_count,
  source_count,
  github_strength,
  market_activity_score,
  money_strength,
  margin_strength,
  multiple_strength,
  runtime_solo_score,
  evidence_breadth_score,
  heat_score_raw,
  least(100.0,business_score_base+sold_activity_bonus) as business_score_raw,
  build_score_raw,
  round(heat_score_raw::numeric,2) as heat_score,
  round(least(100.0,business_score_base+sold_activity_bonus)::numeric,2) as business_score,
  round(build_score_raw::numeric,2) as build_score,
  round((heat_score_raw*0.45 + content_prior*0.35 + evidence_breadth_score*0.20)::numeric,2) as content_score,
  sold_status_count,
  sold_sample_ready,
  median_sold_status_days_on_market,
  median_sold_status_annual_profit,
  sold_activity_score,
  round(sold_activity_bonus::numeric,2) as sold_activity_bonus,
  round(business_score_base::numeric,2) as business_score_base
from s;

alter view opportunity_scored_v01 set (security_invoker=true);

create or replace function refresh_opportunity_scores_v01()
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  active_evidence_total integer;
  inserted_count integer;
begin
  active_evidence_total := refresh_opportunity_evidence_v01();

  with scores as (
    select v.opportunity_id,'HEAT'::score_kind as score_kind,v.heat_score as score,
           jsonb_build_object(
             'github_repo_count',v.github_repo_count,
             'market_listing_count',v.market_listing_count,
             'github_strength',v.github_strength,
             'market_activity_score',v.market_activity_score,
             'source_count',v.source_count
           ) as reason_json
    from opportunity_scored_v01 v
    union all
    select v.opportunity_id,'BUSINESS'::score_kind,v.business_score,
           jsonb_build_object(
             'avg_monthly_profit',v.avg_monthly_profit,
             'avg_profit_margin',v.avg_profit_margin,
             'avg_listing_multiple',v.avg_listing_multiple,
             'market_listing_count',v.market_listing_count,
             'sold_status_count',v.sold_status_count,
             'sold_sample_ready',v.sold_sample_ready,
             'median_sold_status_days_on_market',v.median_sold_status_days_on_market,
             'median_sold_status_annual_profit',v.median_sold_status_annual_profit,
             'sold_activity_score',v.sold_activity_score,
             'sold_activity_bonus',v.sold_activity_bonus,
             'business_score_base',v.business_score_base,
             'sold_status_is_not_transaction_price',true
           )
    from opportunity_scored_v01 v
    union all
    select v.opportunity_id,'BUILD'::score_kind,v.build_score,
           jsonb_build_object(
             'github_strength',v.github_strength,
             'solo_founder_fit',v.solo_founder_fit,
             'china_fit',v.china_fit,
             'market_activity_score',v.market_activity_score
           )
    from opportunity_scored_v01 v
    union all
    select v.opportunity_id,'CONTENT'::score_kind,v.content_score,
           jsonb_build_object(
             'heat_score',v.heat_score,
             'content_prior',v.content_prior,
             'evidence_breadth_score',v.evidence_breadth_score,
             'evidence_count',v.evidence_count
           )
    from opportunity_scored_v01 v
  )
  insert into score_snapshots(opportunity_id,score_kind,score,score_version,reason_json)
  select s.opportunity_id,s.score_kind,s.score,'OPP_V0.2',s.reason_json
  from scores s
  where not exists (
    select 1
    from latest_scores ls
    where ls.opportunity_id=s.opportunity_id
      and ls.score_kind=s.score_kind
      and ls.score_version='OPP_V0.2'
      and abs(ls.score-s.score)<0.01
  );

  get diagnostics inserted_count = row_count;

  return jsonb_build_object(
    'engine_version','OPP_V0.2',
    'active_evidence',active_evidence_total,
    'score_snapshots_inserted',inserted_count
  );
end;
$$;

revoke all on function refresh_opportunity_scores_v01() from public,anon,authenticated;

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
  case when m.source_count>=2 then 'MULTI_SOURCE' else 'SINGLE_SOURCE' end as resonance_status,
  (m.source_count>=2 and m.evidence_count>=5) as public_ready,
  m.sold_status_count,
  m.sold_sample_ready,
  m.median_sold_status_days_on_market,
  m.median_sold_status_annual_profit,
  m.sold_activity_score
from opportunity_metrics_v01 m;

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
      and ss.score_version='OPP_V0.2'
  ) as score_updated_at,
  r.sold_status_count,
  r.sold_sample_ready,
  r.median_sold_status_days_on_market,
  r.median_sold_status_annual_profit,
  r.sold_activity_score
from opportunities o
join opportunity_rank_current r on r.opportunity_id=o.id
where o.status='ACTIVE';

alter view public_opportunity_catalog_v01 set (security_invoker=true);

comment on view opportunity_sold_status_metrics_v01 is
'R7.8 auxiliary Sold-status activity by opportunity. Sample gate >=5. Same Empire Flippers source; never increments source_count.';
comment on view opportunity_scored_v01 is
'OPP_V0.2: Sold-status activity may add at most 5 BUSINESS points when sample count >=5; no other score dimension receives the bonus.';
