-- P3.1 Commercial evidence quality shadow model.
-- Separates source QUALITY from source LEGAL ELIGIBILITY.
-- High-quality but unlicensed sources never affect production opportunity scores.

insert into data_sources(
  code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,
  raw_storage_policy,refresh_interval_minutes,rate_limit_note,updated_at
)
values
('quiet_light','Quiet Light','https://quietlight.com','YELLOW',
 'MANUAL_RESEARCH_OR_WRITTEN_LICENSE',false,false,'NO_AUTOMATED_STORAGE_UNTIL_WRITTEN_PERMISSION',null,
 'High-quality vetted brokerage; no public API/reuse license verified in 2026-10-07 review',now()),
('startupmkt','StartupMKT','https://startupmkt.com','YELLOW',
 'MANUAL_RESEARCH_OR_WRITTEN_LICENSE',false,false,'NO_AUTOMATED_STORAGE_UNTIL_WRITTEN_PERMISSION',null,
 'High-value verified-revenue startup marketplace; no public API/commercial reuse license verified in 2026-10-07 review',now())
on conflict (code) do update set
  name=excluded.name,
  homepage_url=excluded.homepage_url,
  source_status=excluded.source_status,
  access_method=excluded.access_method,
  auto_collect=excluded.auto_collect,
  redisplay_allowed=excluded.redisplay_allowed,
  raw_storage_policy=excluded.raw_storage_policy,
  rate_limit_note=excluded.rate_limit_note,
  updated_at=now();

insert into source_policies(
  source_id,policy_url,reviewed_at,commercial_use_allowed,
  automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
  internal_research_allowed,derived_public_analytics_allowed,
  written_permission_required,allowed_use_scope,policy_basis,notes,evidence_hash
)
select ds.id,p.policy_url,'2026-10-07T06:20:00Z'::timestamptz,
       null,false,false,false,true,false,true,
       p.allowed_use_scope,p.policy_basis,p.notes,
       encode(digest(ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-07-P31','sha256'),'hex')
from (
  values
  ('quiet_light','https://quietlight.com/listings/',
   'MANUAL_RESEARCH_ONLY_PENDING_WRITTEN_PERMISSION',
   'PUBLIC_VETTED_MARKETPLACE_WITHOUT_VERIFIED_DATA_LICENSE',
   'Quiet Light publicly describes its listings as vetted and exposes asking price/revenue/income, but no public API or third-party commercial redistribution license was verified in this review.'),
  ('startupmkt','https://startupmkt.com/for-sale',
   'MANUAL_RESEARCH_ONLY_PENDING_WRITTEN_PERMISSION',
   'PUBLIC_VERIFIED_REVENUE_MARKETPLACE_WITHOUT_VERIFIED_DATA_LICENSE',
   'StartupMKT publicly advertises startup acquisition listings and Stripe-verified revenue metrics, but no public API or third-party commercial redistribution license was verified in this review.')
) as p(code,policy_url,allowed_use_scope,policy_basis,notes)
join data_sources ds on ds.code=p.code
where not exists (
  select 1 from source_policies sp
  where sp.source_id=ds.id
    and sp.evidence_hash=encode(digest(ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-07-P31','sha256'),'hex')
);

-- Re-freeze strategic priority with two newly reviewed high-quality candidates.
insert into commercial_market_source_tiers(
  source_id,quality_tier,strategic_priority,primary_segments,
  inclusion_reason,permission_route,reviewed_at,updated_at
)
select ds.id,x.quality_tier,x.strategic_priority,x.primary_segments,
       x.inclusion_reason,x.permission_route,
       '2026-10-07T06:20:00Z'::timestamptz,now()
from (
  values
  ('empire_flippers','S'::text,1::smallint,array['CONTENT','ECOMMERCE','SAAS']::text[],
   'Official syndication API already approved for JianShi production.',
   'OFFICIAL_API_SYNDICATION_ALREADY_GREEN'),
  ('acquire','S'::text,2::smallint,array['SAAS','AI','ECOMMERCE','APP','MARKETPLACE']::text[],
   'Primary JianShi benchmark for curated startup acquisitions and structured commercial metrics.',
   'WRITTEN_DATA_LICENSE_OR_AUTHORIZED_PARTNER_FEED_REQUIRED'),
  ('fe_international','S'::text,3::smallint,array['SAAS','ECOMMERCE','CONTENT']::text[],
   'Professional M&A marketplace with high diligence quality.',
   'EXPRESS_WRITTEN_PERMISSION_OR_LICENSE_REQUIRED'),
  ('quiet_light','S'::text,4::smallint,array['SAAS','ECOMMERCE','CONTENT','AMAZON']::text[],
   'Vetted online-business brokerage with strong public financial fields and strict screening.',
   'WRITTEN_DATA_LICENSE_OR_AUTHORIZED_FEED_REQUIRED'),
  ('flippa','A'::text,5::smallint,array['SAAS','APP','ECOMMERCE','CONTENT']::text[],
   'Large marketplace with broad coverage and mixed verification quality.',
   'EXPRESS_WRITTEN_CONSENT_REQUIRED'),
  ('microns','A'::text,6::smallint,array['MICRO_SAAS','AI','APP','SIDE_PROJECT']::text[],
   'Strong one-person-company and micro-startup fit.',
   'EXPRESS_PERMISSION_REQUIRED'),
  ('startupmkt','A'::text,7::smallint,array['MICRO_SAAS','AI','APP','SIDE_PROJECT']::text[],
   'Direct startup acquisition marketplace with Stripe-verified revenue available on part of the catalog.',
   'WRITTEN_DATA_LICENSE_OR_AUTHORIZED_FEED_REQUIRED'),
  ('investors_club','A'::text,8::smallint,array['SAAS','ECOMMERCE','CONTENT']::text[],
   'Curated profitable online-business marketplace.',
   'WRITTEN_COMMERCIAL_REUSE_PERMISSION_REQUIRED'),
  ('motion_invest','B'::text,9::smallint,array['CONTENT','WEBSITE','YOUTUBE']::text[],
   'Useful secondary market for profitable websites and YouTube assets.',
   'WRITTEN_COMMERCIAL_REUSE_PERMISSION_REQUIRED')
) as x(code,quality_tier,strategic_priority,primary_segments,inclusion_reason,permission_route)
join data_sources ds on ds.code=x.code
on conflict (source_id) do update set
  quality_tier=excluded.quality_tier,
  strategic_priority=excluded.strategic_priority,
  primary_segments=excluded.primary_segments,
  inclusion_reason=excluded.inclusion_reason,
  permission_route=excluded.permission_route,
  reviewed_at=excluded.reviewed_at,
  updated_at=now();

insert into source_permission_requests(
  source_id,request_status,requested_scopes,contact_channel,notes
)
select ds.id,'DRAFT',
  '["AUTOMATED_API_OR_FEED","HISTORICAL_SNAPSHOT_STORAGE","DERIVED_ANALYTICS","PUBLIC_SUMMARY_DISPLAY","COMMERCIAL_PRODUCT_USE"]'::jsonb,
  case ds.code
    when 'quiet_light' then 'official contact / inquiries'
    when 'startupmkt' then 'official contact / founder outreach'
  end,
  'P3.1 high-quality marketplace licensing draft; no production data use before written approval.'
from data_sources ds
where ds.code in ('quiet_light','startupmkt')
  and not exists (
    select 1 from source_permission_requests spr
    where spr.source_id=ds.id
      and spr.request_status in ('DRAFT','SENT','APPROVED','PARTIAL_APPROVAL')
  );

create table if not exists commercial_source_quality_rules (
  source_id uuid primary key references data_sources(id) on delete cascade,
  quality_weight numeric(4,3) not null check (quality_weight>0 and quality_weight<=1),
  verification_mode text not null check (verification_mode in (
    'CURATED_BROKER_DILIGENCE',
    'PROFESSIONAL_MNA_DILIGENCE',
    'VETTED_MARKETPLACE',
    'MIXED_VERIFICATION',
    'CURATED_MICRO_MARKETPLACE',
    'PRIMARY_REVENUE_VERIFICATION_PARTIAL',
    'CURATED_MARKETPLACE',
    'SECONDARY_NICHE_MARKETPLACE',
    'UNKNOWN'
  )),
  notes text,
  reviewed_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table commercial_source_quality_rules enable row level security;
revoke all on commercial_source_quality_rules from public,anon,authenticated;
grant select,insert,update on commercial_source_quality_rules to service_role;

insert into commercial_source_quality_rules(
  source_id,quality_weight,verification_mode,notes,reviewed_at,updated_at
)
select ds.id,x.quality_weight,x.verification_mode,x.notes,
       '2026-10-07T06:20:00Z'::timestamptz,now()
from (
  values
  ('empire_flippers',1.000::numeric,'CURATED_BROKER_DILIGENCE','Current GREEN baseline; official API plus curated brokerage process.'),
  ('acquire',1.000::numeric,'VETTED_MARKETPLACE','Shadow-only until licensed. High-quality marketplace benchmark.'),
  ('fe_international',1.000::numeric,'PROFESSIONAL_MNA_DILIGENCE','Shadow-only until licensed. Professional M&A diligence.'),
  ('quiet_light',1.000::numeric,'CURATED_BROKER_DILIGENCE','Shadow-only until licensed. Public site states listings are vetted.'),
  ('flippa',0.850::numeric,'MIXED_VERIFICATION','Shadow-only until licensed. Large open marketplace with variable verification levels.'),
  ('microns',0.850::numeric,'CURATED_MICRO_MARKETPLACE','Shadow-only until licensed. Strong micro-startup fit.'),
  ('startupmkt',0.850::numeric,'PRIMARY_REVENUE_VERIFICATION_PARTIAL','Shadow-only until licensed. Public site advertises Stripe-verified revenue on verified records.'),
  ('investors_club',0.850::numeric,'CURATED_MARKETPLACE','Shadow-only until licensed. Curated marketplace.'),
  ('motion_invest',0.650::numeric,'SECONDARY_NICHE_MARKETPLACE','Shadow-only until licensed. Narrower secondary market.')
) as x(code,quality_weight,verification_mode,notes)
join data_sources ds on ds.code=x.code
on conflict (source_id) do update set
  quality_weight=excluded.quality_weight,
  verification_mode=excluded.verification_mode,
  notes=excluded.notes,
  reviewed_at=excluded.reviewed_at,
  updated_at=now();

create or replace view commercial_evidence_quality_shadow_v01
with (security_invoker=true)
as
with eligible as (
  select
    oe.opportunity_id,
    oe.entity_id,
    ds.id as source_id,
    ds.code as source_code,
    t.quality_tier,
    q.quality_weight,
    q.verification_mode
  from opportunity_evidence oe
  join marketplace_listings ml
    on oe.evidence_type='MARKETPLACE_LISTING'
   and ml.id=oe.entity_id
   and ml.active=true
  join data_sources ds on ds.id=ml.source_id
  join commercial_source_quality_rules q on q.source_id=ds.id
  left join commercial_market_source_tiers t on t.source_id=ds.id
  join source_policy_effective_v01 sp on sp.source_id=ds.id
  where oe.active=true
    and oe.rule_version='OPP_V0.1'
    and ds.source_status='GREEN'
    and ds.auto_collect=true
    and ds.redisplay_allowed=true
    and sp.commercial_use_allowed=true
    and sp.automated_collection_allowed=true
    and sp.redisplay_allowed=true
    and sp.derived_public_analytics_allowed=true
)
select
  o.id as opportunity_id,
  o.slug,
  count(distinct e.entity_id) as eligible_commercial_evidence_count,
  count(distinct e.source_id) as eligible_commercial_source_count,
  round(coalesce(sum(e.quality_weight),0)::numeric,2) as quality_weighted_evidence_count,
  round(coalesce(avg(e.quality_weight),0)::numeric,3) as avg_source_quality_weight,
  count(distinct e.source_id) filter (where e.quality_tier='S') as s_tier_source_count,
  count(distinct e.source_id) filter (where e.quality_tier='A') as a_tier_source_count,
  count(distinct e.source_id) filter (where e.quality_tier='B') as b_tier_source_count,
  array_remove(array_agg(distinct e.source_code order by e.source_code),null) as eligible_source_codes
from opportunities o
left join eligible e on e.opportunity_id=o.id
where o.status='ACTIVE'
group by o.id,o.slug;

revoke all on commercial_evidence_quality_shadow_v01 from public,anon,authenticated;
grant select on commercial_evidence_quality_shadow_v01 to service_role;

comment on table commercial_source_quality_rules is
'P3.1 source-quality priors for shadow analytics only. Quality never overrides legal/source-policy eligibility.';
comment on view commercial_evidence_quality_shadow_v01 is
'P3.1 shadow-only commercial evidence quality. Includes only currently GREEN/licensed sources and does not alter OPP_V0.2 scores or public_ready.';
