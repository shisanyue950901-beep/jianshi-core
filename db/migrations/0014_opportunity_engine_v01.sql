create or replace function refresh_opportunity_evidence_v01()
returns integer
language plpgsql
security definer
set search_path=public
as $$
declare
  active_count integer;
begin
  update opportunity_evidence
  set active=false
  where rule_version='OPP_V0.1';

  -- GitHub: AI Agent
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select o.id,gr.source_id,'GITHUB_REPOSITORY',gr.id,1.0,'github_query_ai_agents','OPP_V0.1',true,now()
  from opportunities o
  join github_discovery_queries q on q.code='ai_agents'
  join github_repository_discoveries gd on gd.query_id=q.id
  join github_repositories gr on gr.id=gd.github_repository_id
  where o.slug='ai-agent-tools'
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set active=true,last_seen_at=now(),weight=excluded.weight,rule_code=excluded.rule_code;

  -- GitHub: LLM
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select o.id,gr.source_id,'GITHUB_REPOSITORY',gr.id,1.0,'github_query_llm','OPP_V0.1',true,now()
  from opportunities o
  join github_discovery_queries q on q.code='llm'
  join github_repository_discoveries gd on gd.query_id=q.id
  join github_repositories gr on gr.id=gd.github_repository_id
  where o.slug='llm-tools'
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set active=true,last_seen_at=now(),weight=excluded.weight,rule_code=excluded.rule_code;

  -- GitHub: SaaS
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select o.id,gr.source_id,'GITHUB_REPOSITORY',gr.id,1.0,'github_query_saas','OPP_V0.1',true,now()
  from opportunities o
  join github_discovery_queries q on q.code='saas'
  join github_repository_discoveries gd on gd.query_id=q.id
  join github_repositories gr on gr.id=gd.github_repository_id
  where o.slug='solo-saas'
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set active=true,last_seen_at=now(),weight=excluded.weight,rule_code=excluded.rule_code;

  -- Marketplace: SaaS
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select o.id,ml.source_id,'MARKETPLACE_LISTING',ml.id,1.25,'market_monetization_saas','OPP_V0.1',true,now()
  from opportunities o
  cross join marketplace_listings ml
  where o.slug='solo-saas'
    and ml.active=true
    and ml.monetizations ? 'SaaS'
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set active=true,last_seen_at=now(),weight=excluded.weight,rule_code=excluded.rule_code;

  -- Marketplace: eCommerce / Amazon / Dropshipping
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select o.id,ml.source_id,'MARKETPLACE_LISTING',ml.id,1.0,'market_monetization_ecommerce','OPP_V0.1',true,now()
  from opportunities o
  cross join marketplace_listings ml
  where o.slug='ecommerce-brands'
    and ml.active=true
    and ml.monetizations ?| array['Amazon FBA','Amazon FBM','eCommerce','DropShipping']
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set active=true,last_seen_at=now(),weight=excluded.weight,rule_code=excluded.rule_code;

  -- Marketplace: affiliate/content
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select o.id,ml.source_id,'MARKETPLACE_LISTING',ml.id,1.0,'market_monetization_affiliate_content','OPP_V0.1',true,now()
  from opportunities o
  cross join marketplace_listings ml
  where o.slug='affiliate-content'
    and ml.active=true
    and ml.monetizations ?| array['Affiliate','Amazon Associates','Display Advertising']
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set active=true,last_seen_at=now(),weight=excluded.weight,rule_code=excluded.rule_code;

  -- Marketplace: creator/media
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select o.id,ml.source_id,'MARKETPLACE_LISTING',ml.id,1.0,'market_monetization_creator_media','OPP_V0.1',true,now()
  from opportunities o
  cross join marketplace_listings ml
  where o.slug='creator-media'
    and ml.active=true
    and ml.monetizations ?| array['YouTube','Newsletter','Digital Product','Info Product']
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set active=true,last_seen_at=now(),weight=excluded.weight,rule_code=excluded.rule_code;

  select count(*) into active_count
  from opportunity_evidence
  where rule_version='OPP_V0.1' and active=true;

  return active_count;
end;
$$;

revoke all on function refresh_opportunity_evidence_v01() from public,anon,authenticated;

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
   (case when coalesce(m.market_listing_count,0)>0 then 1 else 0 end)) as source_count
from opportunities o
join opportunity_profiles p on p.opportunity_id=o.id and p.engine_version='OPP_V0.1'
left join github_agg g on g.opportunity_id=o.id
left join market_agg m on m.opportunity_id=o.id
where o.status='ACTIVE';

alter view opportunity_metrics_v01 set (security_invoker=true);

create or replace view opportunity_scored_v01 as
with c as (
  select
    m.*,
    least(100.0,greatest(0.0,m.github_top5_rank_score)) as github_strength,
    least(100.0,greatest(0.0,
      case when m.market_listing_count>0
           then 100.0 * ln(m.market_listing_count + 1.0) / ln(50.0 + 1.0)
           else 0.0 end
    )) as market_activity_score,
    least(100.0,greatest(0.0,
      case when m.avg_monthly_profit>0
           then 100.0 * ln(m.avg_monthly_profit + 1.0) / ln(50000.0 + 1.0)
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
    end as business_score_raw,
    github_strength*0.30 + solo_founder_fit*0.25 + china_fit*0.20 + market_activity_score*0.25 as build_score_raw
  from c
)
select
  s.*,
  round(heat_score_raw::numeric,2) as heat_score,
  round(business_score_raw::numeric,2) as business_score,
  round(build_score_raw::numeric,2) as build_score,
  round((heat_score_raw*0.45 + content_prior*0.35 + evidence_breadth_score*0.20)::numeric,2) as content_score
from s;

alter view opportunity_scored_v01 set (security_invoker=true);

create or replace function refresh_opportunity_scores_v01()
returns jsonb
language plpgsql
security definer
set search_path=public
as $$
declare
  evidence_count integer;
  inserted_count integer;
begin
  evidence_count := refresh_opportunity_evidence_v01();

  with scores as (
    select opportunity_id,'HEAT'::score_kind as score_kind,heat_score as score,
           jsonb_build_object(
             'github_repo_count',github_repo_count,
             'market_listing_count',market_listing_count,
             'github_strength',github_strength,
             'market_activity_score',market_activity_score,
             'source_count',source_count
           ) as reason_json
    from opportunity_scored_v01
    union all
    select opportunity_id,'BUSINESS'::score_kind,business_score,
           jsonb_build_object(
             'avg_monthly_profit',avg_monthly_profit,
             'avg_profit_margin',avg_profit_margin,
             'avg_listing_multiple',avg_listing_multiple,
             'market_listing_count',market_listing_count
           )
    from opportunity_scored_v01
    union all
    select opportunity_id,'BUILD'::score_kind,build_score,
           jsonb_build_object(
             'github_strength',github_strength,
             'solo_founder_fit',solo_founder_fit,
             'china_fit',china_fit,
             'market_activity_score',market_activity_score
           )
    from opportunity_scored_v01
    union all
    select opportunity_id,'CONTENT'::score_kind,content_score,
           jsonb_build_object(
             'heat_score',heat_score,
             'content_prior',content_prior,
             'evidence_breadth_score',evidence_breadth_score,
             'evidence_count',evidence_count
           )
    from opportunity_scored_v01
  )
  insert into score_snapshots(opportunity_id,score_kind,score,score_version,reason_json)
  select s.opportunity_id,s.score_kind,s.score,'OPP_V0.1',s.reason_json
  from scores s
  where not exists (
    select 1
    from latest_scores ls
    where ls.opportunity_id=s.opportunity_id
      and ls.score_kind=s.score_kind
      and ls.score_version='OPP_V0.1'
      and abs(ls.score-s.score)<0.01
  );

  get diagnostics inserted_count = row_count;

  return jsonb_build_object(
    'engine_version','OPP_V0.1',
    'active_evidence',evidence_count,
    'score_snapshots_inserted',inserted_count
  );
end;
$$;

revoke all on function refresh_opportunity_scores_v01() from public,anon,authenticated;

create or replace view opportunity_rank_current as
select
  m.*,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='HEAT') as heat_score,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='CONTENT') as content_score,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='BUILD') as build_score,
  (select ls.score from latest_scores ls
   where ls.opportunity_id=m.opportunity_id and ls.score_kind='BUSINESS') as business_score,
  case when m.source_count>=2 then 'MULTI_SOURCE' else 'SINGLE_SOURCE' end as resonance_status,
  (m.source_count>=2 and m.evidence_count>=5) as public_ready
from opportunity_metrics_v01 m;

alter view opportunity_rank_current set (security_invoker=true);
