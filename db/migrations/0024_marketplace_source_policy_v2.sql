-- R7.6 Marketplace source policy hardening.
-- "Can fetch" is not equivalent to "can commercialize". Non-GREEN sources
-- remain fail-closed for automated collection and public redisplay.

alter table source_policies
  add column if not exists internal_research_allowed boolean not null default false,
  add column if not exists derived_public_analytics_allowed boolean not null default false,
  add column if not exists written_permission_required boolean not null default false,
  add column if not exists allowed_use_scope text,
  add column if not exists policy_basis text;

insert into data_sources(
  code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,
  raw_storage_policy,refresh_interval_minutes,rate_limit_note,updated_at
)
values
('deal_slide','DealSlide','https://dealslide.com','RED','MANUAL_RESEARCH_ONLY',false,false,'NO_AUTOMATED_STORAGE',null,'Automated access prohibited by Terms',now()),
('trustmrr','TrustMRR','https://trustmrr.com','YELLOW','OFFICIAL_API_RESTRICTED',false,false,'NO_PRODUCT_STORAGE_UNTIL_WRITTEN_PERMISSION',null,'API available; public/customer-facing use restricted',now()),
('catchbuys','CatchBuys','https://catchbuys.com','YELLOW','OFFICIAL_API_TERMS_PENDING',false,false,'NO_PRODUCT_STORAGE_UNTIL_TERMS_AND_UPSTREAM_RIGHTS_VERIFIED',null,'60 req/min advertised; production disabled pending policy review',now()),
('acquirebase','AcquireBase','https://acquirebase.com','YELLOW','PUBLIC_WEB_REVIEW_REQUIRED',false,false,'NO_AUTOMATED_STORAGE_UNTIL_WRITTEN_PERMISSION',null,'No explicit automation/republication license found',now())
on conflict (code) do update set
  name=excluded.name,
  homepage_url=excluded.homepage_url,
  source_status=excluded.source_status,
  access_method=excluded.access_method,
  auto_collect=excluded.auto_collect,
  redisplay_allowed=excluded.redisplay_allowed,
  raw_storage_policy=excluded.raw_storage_policy,
  refresh_interval_minutes=excluded.refresh_interval_minutes,
  rate_limit_note=excluded.rate_limit_note,
  updated_at=now();

insert into source_policies(
  source_id,policy_url,reviewed_at,commercial_use_allowed,
  automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
  internal_research_allowed,derived_public_analytics_allowed,
  written_permission_required,allowed_use_scope,policy_basis,notes,evidence_hash
)
select ds.id,p.policy_url,'2026-10-06T15:47:00Z'::timestamptz,
       p.commercial_use_allowed,p.automated_collection_allowed,p.redisplay_allowed,
       p.fulltext_storage_allowed,p.internal_research_allowed,
       p.derived_public_analytics_allowed,p.written_permission_required,
       p.allowed_use_scope,p.policy_basis,p.notes,
       encode(digest(
          ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-06',
          'sha256'
       ),'hex')
from (
  values
  ('acquire','https://acquire.com/buyerseller/',false,false,false,false,true,false,true,
   'MANUAL_POLICY_AND_MARKET_RESEARCH_ONLY',
   'OFFICIAL_TERMS_EXPLICIT_PROHIBITION',
   'Buyer & Seller Terms last modified 2026-03-18 prohibit scraping/data extraction, automatic queries, cross-domain repost/display, and competitive-product use without written permission.'),
  ('deal_slide','https://dealslide.com/terms',false,false,false,false,true,false,true,
   'MANUAL_POLICY_AND_MARKET_RESEARCH_ONLY',
   'OFFICIAL_TERMS_EXPLICIT_PROHIBITION',
   'Terms last updated 2025-04-18 prohibit automated access, scraping, reproducing and republishing the Website or content.'),
  ('trustmrr','https://trustmrr.com/terms',false,false,false,false,true,false,true,
   'PRIVATE_INTERNAL_RESEARCH_AFTER_ACCOUNT_AUTHORIZATION_ONLY',
   'OFFICIAL_API_WITH_PUBLIC_USE_RESTRICTIONS',
   'Official API exists, but public display, bulk export/republication, customer-facing product use and AI/recommendation use require prior written permission.'),
  ('catchbuys','https://catchbuys.com/terms',null,false,false,false,true,false,true,
   'EVALUATE_API_AND_REQUEST_WRITTEN_COMMERCIAL_PERMISSION',
   'API_MARKETING_SUPPORTS_DATA_PRODUCTS_BUT_TERMS_NOT_FULLY_VERIFIED',
   'API page advertises newsletters, deal-flow trackers, alerting and data products; keep YELLOW until Terms and upstream redistribution rights are verified in writing.'),
  ('acquirebase','https://acquirebase.com/terms',null,false,false,false,true,false,true,
   'MANUAL_RESEARCH_ONLY_PENDING_WRITTEN_PERMISSION',
   'PUBLIC_LISTINGS_WITHOUT_EXPLICIT_REUSE_LICENSE',
   'Public listings expose MRR/profit/asking price, but current Terms do not clearly grant automated collection, historical storage or commercial republication rights.'),
  ('sideprojectors','https://www.sideprojectors.com/v4/legal/terms-of-service',null,false,false,false,true,false,true,
   'MANUAL_RESEARCH_ONLY_PENDING_POLICY_REVIEW',
   'PUBLIC_MARKETPLACE_POLICY_SCOPE_UNRESOLVED',
   'Keep fail-closed until automation and redistribution rights are clearly verified.')
) as p(code,policy_url,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
       internal_research_allowed,derived_public_analytics_allowed,written_permission_required,
       allowed_use_scope,policy_basis,notes)
join data_sources ds on ds.code=p.code;

drop view if exists source_policy_effective_v01;
create view source_policy_effective_v01 as
select distinct on (ds.id)
  ds.id as source_id,
  ds.code,
  ds.name,
  ds.source_status,
  ds.access_method,
  ds.auto_collect,
  ds.redisplay_allowed as source_redisplay_allowed,
  sp.policy_url,
  sp.reviewed_at,
  sp.commercial_use_allowed,
  sp.automated_collection_allowed,
  sp.redisplay_allowed,
  sp.fulltext_storage_allowed,
  sp.internal_research_allowed,
  sp.derived_public_analytics_allowed,
  sp.written_permission_required,
  sp.allowed_use_scope,
  sp.policy_basis,
  sp.notes
from data_sources ds
left join source_policies sp on sp.source_id=ds.id
order by ds.id,sp.reviewed_at desc nulls last,sp.created_at desc nulls last;

alter view source_policy_effective_v01 set (security_invoker=true);

create or replace function assert_source_publication_allowed_v01(p_source_code text)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  r source_policy_effective_v01%rowtype;
begin
  select * into r from source_policy_effective_v01 where code=p_source_code;
  if not found then
    raise exception 'UNKNOWN_SOURCE: %',p_source_code;
  end if;
  if r.source_status <> 'GREEN'
     or r.auto_collect is not true
     or r.source_redisplay_allowed is not true
     or r.automated_collection_allowed is not true
     or r.redisplay_allowed is not true then
    raise exception 'PUBLICATION_FORBIDDEN_BY_SOURCE_POLICY: %',p_source_code;
  end if;
  return true;
end;
$$;

revoke all on function assert_source_publication_allowed_v01(text) from public,anon,authenticated;

comment on view source_policy_effective_v01 is
'Latest reviewed policy per source. Production collectors and publication paths must treat non-GREEN as fail-closed.';


create table if not exists source_permission_requests (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references data_sources(id) on delete cascade,
  request_status text not null default 'DRAFT'
    check (request_status in ('DRAFT','SENT','APPROVED','PARTIAL_APPROVAL','REJECTED','EXPIRED')),
  requested_scopes jsonb not null default '[]'::jsonb,
  approved_scopes jsonb,
  contact_channel text,
  contact_reference text,
  requested_at timestamptz,
  responded_at timestamptz,
  expires_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_source_permission_requests_source
  on source_permission_requests(source_id,created_at desc);

alter table source_permission_requests enable row level security;
revoke all on source_permission_requests from anon,authenticated;

insert into source_permission_requests(
  source_id,request_status,requested_scopes,contact_channel,notes
)
select ds.id,'DRAFT',
       '["AUTOMATED_API_OR_FEED","HISTORICAL_SNAPSHOT_STORAGE","DERIVED_ANALYTICS","PUBLIC_SUMMARY_DISPLAY","COMMERCIAL_PRODUCT_USE"]'::jsonb,
       case ds.code
         when 'acquire' then 'support@acquire.com / partnership contact'
         when 'trustmrr' then 'official contact / API owner'
         when 'catchbuys' then 'official contact / API owner'
         when 'acquirebase' then 'atta@acquirebase.com'
         when 'sideprojectors' then 'official contact'
       end,
       'R7.6 licensing outreach draft; no automated collection before written approval.'
from data_sources ds
where ds.code in ('acquire','trustmrr','catchbuys','acquirebase','sideprojectors')
  and not exists (
    select 1 from source_permission_requests spr
    where spr.source_id=ds.id and spr.request_status in ('DRAFT','SENT','APPROVED','PARTIAL_APPROVAL')
  );

comment on table source_permission_requests is
'Tracks written licensing/permission outreach. Approval does not auto-enable a source; registry and policy review must still be explicitly updated.';
