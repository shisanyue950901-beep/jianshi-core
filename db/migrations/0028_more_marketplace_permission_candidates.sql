-- R7.9 additional acquisition-marketplace candidates.
-- All remain fail-closed until explicit commercial data permission.

insert into data_sources(
  code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,
  raw_storage_policy,refresh_interval_minutes,rate_limit_note,updated_at
)
values
('fe_international','FE International','https://www.feinternational.com','RED',
 'MANUAL_RESEARCH_OR_WRITTEN_LICENSE',false,false,'NO_AUTOMATED_STORAGE',null,
 'Platform Terms prohibit competitive intelligence and data extraction absent written permission',now()),
('investors_club','Investors Club','https://investors.club','YELLOW',
 'PUBLIC_WEB_REVIEW_REQUIRED',false,false,'NO_AUTOMATED_STORAGE_UNTIL_WRITTEN_PERMISSION',null,
 'Public listings available; commercial aggregation/republication rights unresolved',now()),
('motion_invest','Motion Invest','https://www.motioninvest.com','YELLOW',
 'PUBLIC_WEB_REVIEW_REQUIRED',false,false,'NO_AUTOMATED_STORAGE_UNTIL_WRITTEN_PERMISSION',null,
 'No public API/reuse license verified',now())
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
select ds.id,p.policy_url,'2026-10-06T16:25:00Z'::timestamptz,
       p.commercial_use_allowed,p.automated_collection_allowed,p.redisplay_allowed,
       p.fulltext_storage_allowed,p.internal_research_allowed,
       p.derived_public_analytics_allowed,p.written_permission_required,
       p.allowed_use_scope,p.policy_basis,p.notes,
       encode(digest(ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-06','sha256'),'hex')
from (
  values
  ('fe_international','https://www.feinternational.com/legal-md/buyer-seller-terms-of-use',
   false,false,false,false,true,false,true,
   'MANUAL_POLICY_RESEARCH_ONLY_PENDING_WRITTEN_PERMISSION',
   'OFFICIAL_TERMS_EXPLICIT_EXTRACTION_AND_COMPETITIVE_INTELLIGENCE_PROHIBITION',
   '2026 Platform Terms prohibit benchmarking/competitive intelligence and scraping/crawling/harvesting/extracting marketplace data by automated or manual means without express written permission.'),
  ('investors_club','https://investors.club/terms-and-conditions/',
   null,false,false,false,true,false,true,
   'MANUAL_RESEARCH_ONLY_PENDING_WRITTEN_PERMISSION',
   'PROPRIETARY_CONTENT_WITHOUT_COMMERCIAL_REUSE_LICENSE',
   'Public listings and price/listing history are useful, but platform Content is proprietary and no commercial aggregation/republication license was identified.'),
  ('motion_invest','https://www.motioninvest.com/terms-of-service',
   null,false,false,false,true,false,true,
   'MANUAL_RESEARCH_ONLY_PENDING_WRITTEN_PERMISSION',
   'PUBLIC_MARKETPLACE_WITHOUT_VERIFIED_API_OR_REUSE_LICENSE',
   'Public marketplace exposes income, traffic and asking price for websites/YouTube assets, but no public API or commercial reuse license was verified.')
) as p(code,policy_url,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
       internal_research_allowed,derived_public_analytics_allowed,written_permission_required,
       allowed_use_scope,policy_basis,notes)
join data_sources ds on ds.code=p.code;

insert into source_permission_requests(
  source_id,request_status,requested_scopes,contact_channel,notes
)
select ds.id,'DRAFT',
       '["AUTOMATED_API_OR_FEED","HISTORICAL_SNAPSHOT_STORAGE","DERIVED_ANALYTICS","PUBLIC_SUMMARY_DISPLAY","COMMERCIAL_PRODUCT_USE"]'::jsonb,
       case ds.code
         when 'fe_international' then 'fecapitalinfo@feinternational.com / official support'
         when 'investors_club' then 'official contact form / support'
         when 'motion_invest' then 'legal@motioninvest.com'
       end,
       'R7.9 permission outreach draft; production collection remains disabled.'
from data_sources ds
where ds.code in ('fe_international','investors_club','motion_invest')
  and not exists (
    select 1 from source_permission_requests spr
    where spr.source_id=ds.id
      and spr.request_status in ('DRAFT','SENT','APPROVED','PARTIAL_APPROVAL')
  );

comment on table source_permission_requests is
'Written permission pipeline for acquisition-marketplace data. Approval never auto-enables collection.';
