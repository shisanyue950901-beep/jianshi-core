-- P3 high-quality commercial marketplace source layer.
-- Acquire-class sources are prioritized for licensing, but remain fail-closed
-- unless the latest source policy explicitly permits production use.

create table if not exists commercial_market_source_tiers (
  source_id uuid primary key references data_sources(id) on delete cascade,
  quality_tier text not null check (quality_tier in ('S','A','B')),
  strategic_priority smallint not null check (strategic_priority between 1 and 99),
  primary_segments text[] not null default '{}'::text[],
  inclusion_reason text not null,
  permission_route text,
  reviewed_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table commercial_market_source_tiers enable row level security;
revoke all on commercial_market_source_tiers from public,anon,authenticated;
grant select,insert,update on commercial_market_source_tiers to service_role;

insert into commercial_market_source_tiers(
  source_id,quality_tier,strategic_priority,primary_segments,
  inclusion_reason,permission_route,reviewed_at,updated_at
)
select ds.id,x.quality_tier,x.strategic_priority,x.primary_segments,
       x.inclusion_reason,x.permission_route,
       '2026-10-07T06:05:00Z'::timestamptz,now()
from (
  values
  ('empire_flippers','S'::text,1::smallint,array['CONTENT','ECOMMERCE','SAAS']::text[],
   'High-quality online business marketplace with official syndication API already approved for JianShi production.',
   'OFFICIAL_API_SYNDICATION_ALREADY_GREEN'),
  ('acquire','S'::text,2::smallint,array['SAAS','AI','ECOMMERCE','APP','MARKETPLACE']::text[],
   'Primary benchmark for JianShi: curated startup marketplace with public financial, business-model, tech-stack and acquisition fields.',
   'WRITTEN_DATA_LICENSE_OR_AUTHORIZED_PARTNER_FEED_REQUIRED'),
  ('fe_international','S'::text,3::smallint,array['SAAS','ECOMMERCE','CONTENT']::text[],
   'Professional M&A marketplace with structured financial and diligence workflow; high evidentiary quality.',
   'EXPRESS_WRITTEN_PERMISSION_OR_LICENSE_REQUIRED'),
  ('flippa','A'::text,4::smallint,array['SAAS','APP','ECOMMERCE','CONTENT']::text[],
   'Large marketplace with asking price, revenue/profit, multiples and Data Verified/Vetted signals; quality variance requires stronger weighting rules.',
   'EXPRESS_WRITTEN_CONSENT_REQUIRED'),
  ('microns','A'::text,5::smallint,array['MICRO_SAAS','AI','APP','SIDE_PROJECT']::text[],
   'Strong fit for one-person and micro-startup opportunities; focuses on revenue-generating projects and small exits.',
   'EXPRESS_PERMISSION_REQUIRED'),
  ('investors_club','A'::text,6::smallint,array['SAAS','ECOMMERCE','CONTENT']::text[],
   'Curated profitable online-business marketplace with useful public asking-price and financial fields.',
   'WRITTEN_COMMERCIAL_REUSE_PERMISSION_REQUIRED'),
  ('motion_invest','B'::text,7::smallint,array['CONTENT','WEBSITE','YOUTUBE']::text[],
   'Useful secondary market for profitable websites and YouTube assets, but narrower fit than S/A priority sources.',
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

-- Latest policy reviews based on official terms/help pages checked 2026-10-07.
insert into source_policies(
  source_id,policy_url,reviewed_at,commercial_use_allowed,
  automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
  internal_research_allowed,derived_public_analytics_allowed,
  written_permission_required,allowed_use_scope,policy_basis,notes,evidence_hash
)
select ds.id,p.policy_url,'2026-10-07T06:05:00Z'::timestamptz,
       p.commercial_use_allowed,p.automated_collection_allowed,p.redisplay_allowed,
       p.fulltext_storage_allowed,p.internal_research_allowed,
       p.derived_public_analytics_allowed,p.written_permission_required,
       p.allowed_use_scope,p.policy_basis,p.notes,
       encode(digest(ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-07-P3','sha256'),'hex')
from (
  values
  ('acquire','https://acquire.com/buyerseller/',
   false,false,false,false,true,false,true,
   'MANUAL_RESEARCH_AND_LICENSING_OUTREACH_ONLY',
   'OFFICIAL_TERMS_REQUIRE_WRITTEN_PERMISSION_FOR_EXTRACTION_AND_REDISPLAY',
   'Buyer & Seller Terms prohibit scraping/data extraction, automated queries, cross-domain repost/display and competitive-product use unless Acquire expressly permits it in writing.'),
  ('fe_international','https://www.feinternational.com/legal-md/buyer-seller-terms-of-use',
   false,false,false,false,true,false,true,
   'MANUAL_RESEARCH_AND_LICENSING_OUTREACH_ONLY',
   'OFFICIAL_TERMS_REQUIRE_EXPRESS_WRITTEN_PERMISSION',
   'Platform Terms prohibit benchmarking/competitive intelligence and scraping/crawling/harvesting/extraction from the marketplace unless FE International gives express written permission.'),
  ('flippa','https://flippa.com/terms-of-service/',
   false,false,false,false,true,false,true,
   'MANUAL_RESEARCH_AND_LICENSING_OUTREACH_ONLY',
   'OFFICIAL_TERMS_REQUIRE_EXPRESS_WRITTEN_CONSENT_FOR_DATA_MINING',
   'Terms prohibit data mining/robots or similar extraction of substantial parts and creating/publishing a database containing substantial parts without express written consent.'),
  ('microns','https://www.microns.io/privacy-policy',
   false,false,false,false,true,false,true,
   'MANUAL_RESEARCH_AND_LICENSING_OUTREACH_ONLY',
   'OFFICIAL_POLICY_REQUIRES_EXPRESS_PERMISSION_FOR_CRAWL_SCRAPE_SPIDER',
   'Microns policy says users may not crawl, scrape or spider any page of the Services without express permission.'),
  ('investors_club','https://investors.club/terms-and-conditions/',
   null,false,false,false,true,false,true,
   'MANUAL_RESEARCH_ONLY_PENDING_WRITTEN_COMMERCIAL_REUSE_PERMISSION',
   'PROPRIETARY_PLATFORM_DATA_WITHOUT_VERIFIED_REUSE_LICENSE',
   'Terms reserve rights in site technology/data and restrict automated copying; no explicit license for commercial aggregation or republication of listing data was identified.'),
  ('motion_invest','https://motioninvest.com/terms-of-service',
   null,false,false,false,true,false,true,
   'MANUAL_RESEARCH_ONLY_PENDING_WRITTEN_COMMERCIAL_REUSE_PERMISSION',
   'PUBLIC_MARKETPLACE_WITHOUT_VERIFIED_API_OR_REUSE_LICENSE',
   'Terms describe a proprietary digital-asset marketplace but do not grant an API, automated collection right, historical storage right or commercial republication license.')
) as p(code,policy_url,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
       internal_research_allowed,derived_public_analytics_allowed,written_permission_required,
       allowed_use_scope,policy_basis,notes)
join data_sources ds on ds.code=p.code
where not exists (
  select 1 from source_policies sp
  where sp.source_id=ds.id
    and sp.evidence_hash=encode(digest(ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-07-P3','sha256'),'hex')
);

-- Normalize access methods without changing fail-closed source status.
update data_sources set
  access_method='MANUAL_RESEARCH_OR_WRITTEN_LICENSE',
  auto_collect=false,
  redisplay_allowed=false,
  updated_at=now()
where code in ('acquire','fe_international','flippa','microns');

-- Add missing permission outreach drafts.
insert into source_permission_requests(
  source_id,request_status,requested_scopes,contact_channel,notes
)
select ds.id,'DRAFT',
  '["AUTOMATED_API_OR_FEED","HISTORICAL_SNAPSHOT_STORAGE","DERIVED_ANALYTICS","PUBLIC_SUMMARY_DISPLAY","COMMERCIAL_PRODUCT_USE"]'::jsonb,
  case ds.code
    when 'flippa' then 'support@flippa.com / official partnership contact'
    when 'microns' then 'support@microns.io'
  end,
  'P3 high-quality marketplace licensing draft. No automated collection, storage or public redisplay before written approval.'
from data_sources ds
where ds.code in ('flippa','microns')
  and not exists (
    select 1 from source_permission_requests spr
    where spr.source_id=ds.id
      and spr.request_status in ('DRAFT','SENT','APPROVED','PARTIAL_APPROVAL')
  );

-- Refresh contact route and priority notes for existing unsent drafts.
update source_permission_requests spr
set contact_channel=case ds.code
      when 'acquire' then 'support@acquire.com / Acquire partner program consultation'
      when 'fe_international' then 'support@feinternational.com / fecapitalinfo@feinternational.com'
      when 'flippa' then 'support@flippa.com / official partnership contact'
      when 'microns' then 'support@microns.io'
      when 'investors_club' then 'official contact form / support'
      when 'motion_invest' then 'legal@motioninvest.com'
      else spr.contact_channel end,
    notes='P3 high-quality commercial-source licensing draft; priority=' ||
      coalesce((select strategic_priority::text from commercial_market_source_tiers t where t.source_id=spr.source_id),'NA') ||
      '. Production remains fail-closed until written approval is reviewed.',
    updated_at=now()
from data_sources ds
where spr.source_id=ds.id
  and spr.request_status='DRAFT'
  and ds.code in ('acquire','fe_international','flippa','microns','investors_club','motion_invest');

create or replace view commercial_market_source_priority_v01
with (security_invoker=true)
as
select
  t.strategic_priority,
  t.quality_tier,
  ds.code,
  ds.name,
  t.primary_segments,
  t.inclusion_reason,
  t.permission_route,
  ds.source_status,
  ds.access_method,
  ds.auto_collect,
  ds.redisplay_allowed,
  sp.commercial_use_allowed,
  sp.automated_collection_allowed,
  sp.derived_public_analytics_allowed,
  sp.written_permission_required,
  sp.policy_basis,
  t.reviewed_at
from commercial_market_source_tiers t
join data_sources ds on ds.id=t.source_id
left join source_policy_effective_v01 sp on sp.source_id=ds.id
order by t.strategic_priority;

revoke all on commercial_market_source_priority_v01 from public,anon,authenticated;
grant select on commercial_market_source_priority_v01 to service_role;

comment on table commercial_market_source_tiers is
'P3 quality-first commercial marketplace shortlist. Quality tier prioritizes licensing effort; it never overrides source publication policy.';
comment on view commercial_market_source_priority_v01 is
'Internal P3 licensing priority view. Production eligibility remains governed by source policy gates, not quality tier.';
