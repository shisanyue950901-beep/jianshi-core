-- R7.5: expand GitHub discovery so existing commercial opportunities can obtain
-- a second independent evidence class without weakening the multi-source gate.

insert into github_discovery_queries(code,query_template,sort_by,order_by,per_page,notes)
values
('ecommerce','topic:ecommerce stars:>50 archived:false','stars','desc',50,'电商基础设施与开源电商项目'),
('affiliate_marketing','topic:affiliate-marketing stars:>20 archived:false','stars','desc',50,'联盟营销工具与开源项目'),
('newsletter','topic:newsletter stars:>50 archived:false','stars','desc',50,'Newsletter 与邮件媒体工具'),
('youtube','topic:youtube stars:>100 archived:false','stars','desc',50,'YouTube 创作者与视频工具')
on conflict (code) do update set
  query_template=excluded.query_template,
  sort_by=excluded.sort_by,
  order_by=excluded.order_by,
  per_page=excluded.per_page,
  notes=excluded.notes,
  enabled=true,
  updated_at=now();

create table if not exists opportunity_github_query_map (
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  query_id uuid not null references github_discovery_queries(id) on delete cascade,
  weight numeric(6,3) not null default 1.0,
  rule_code text not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(opportunity_id,query_id)
);

alter table opportunity_github_query_map enable row level security;
revoke all on opportunity_github_query_map from anon,authenticated;

insert into opportunity_github_query_map(opportunity_id,query_id,weight,rule_code)
select o.id,q.id,m.weight,m.rule_code
from (
  values
    ('ai-agent-tools','ai_agents',1.0::numeric,'github_query_ai_agents'),
    ('llm-tools','llm',1.0::numeric,'github_query_llm'),
    ('solo-saas','saas',1.0::numeric,'github_query_saas'),
    ('ecommerce-brands','ecommerce',0.95::numeric,'github_query_ecommerce'),
    ('affiliate-content','affiliate_marketing',0.90::numeric,'github_query_affiliate_marketing'),
    ('creator-media','newsletter',0.90::numeric,'github_query_newsletter'),
    ('creator-media','youtube',0.80::numeric,'github_query_youtube')
) as m(opportunity_slug,query_code,weight,rule_code)
join opportunities o on o.slug=m.opportunity_slug
join github_discovery_queries q on q.code=m.query_code
on conflict (opportunity_id,query_id) do update set
  weight=excluded.weight,
  rule_code=excluded.rule_code,
  active=true,
  updated_at=now();

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

  -- GitHub mappings are data-driven so adding a new discovery query does not
  -- require another hard-coded block in the scoring function.
  insert into opportunity_evidence(
    opportunity_id,source_id,evidence_type,entity_id,weight,rule_code,rule_version,active,last_seen_at
  )
  select
    m.opportunity_id,
    gr.source_id,
    'GITHUB_REPOSITORY',
    gr.id,
    m.weight,
    m.rule_code,
    'OPP_V0.1',
    true,
    now()
  from opportunity_github_query_map m
  join github_repository_discoveries gd on gd.query_id=m.query_id
  join github_repositories gr on gr.id=gd.github_repository_id
  where m.active=true
  on conflict (opportunity_id,evidence_type,entity_id,rule_version)
  do update set
    active=true,
    last_seen_at=now(),
    weight=greatest(opportunity_evidence.weight,excluded.weight),
    rule_code=excluded.rule_code;

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

comment on table opportunity_github_query_map is
'R7.5 data-driven mapping from official GitHub discovery queries to JianShi opportunity entities.';
