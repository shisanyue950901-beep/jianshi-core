-- P4.1 Signal-source expansion foundation.
-- Quality-first, policy-first, fail-closed.
-- This migration registers additional signal sources and creates a generic
-- shadow signal layer. It does NOT change OPP_V0.2, public_ready, or public feed.

insert into data_sources(
  code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,
  raw_storage_policy,refresh_interval_minutes,rate_limit_note,updated_at
)
values
('npm','npm Public Registry','https://www.npmjs.com','GREEN','OFFICIAL_PUBLIC_API',true,true,
 'PUBLIC_PACKAGE_METADATA_AND_AGGREGATE_METRICS_ONLY',360,'Respect documented API limits and fair use',now()),
('stack_exchange','Stack Exchange / Stack Overflow API','https://api.stackexchange.com','GREEN','OFFICIAL_API_ATTRIBUTION_REQUIRED',true,true,
 'AGGREGATE_TAG_AND_QUESTION_METADATA_ONLY_NO_FULLTEXT',360,'Respect API throttles; use attribution',now()),
('hacker_news','Hacker News','https://news.ycombinator.com','YELLOW','OFFICIAL_API_POLICY_SCOPE_REVIEW',false,false,
 'NO_AUTOMATED_STORAGE_UNTIL_COMMERCIAL_REUSE_SCOPE_VERIFIED',null,'Official API has no rate limit; reuse scope still under review',now()),
('product_hunt','Product Hunt','https://www.producthunt.com','YELLOW','OFFICIAL_API_COMMERCIAL_PERMISSION_REQUIRED',false,false,
 'NO_COMMERCIAL_API_USE_WITHOUT_PERMISSION',null,'Commercial API use requires Product Hunt approval',now()),
('reddit','Reddit','https://www.reddit.com','RED','COMMERCIAL_CONTRACT_REQUIRED',false,false,
 'NO_AUTOMATED_COLLECTION_OR_STORAGE_WITHOUT_APPROVED_CONTRACT',null,'Commercial data use requires permission/contract; unauthorized scraping prohibited',now()),
('google_trends','Google Trends','https://trends.google.com','YELLOW','OFFICIAL_API_ALPHA_ACCESS_REQUIRED',false,false,
 'NO_AUTOMATED_COLLECTION_UNTIL_ALPHA_OR_GENERAL_API_ACCESS_GRANTED',null,'Official Trends API remains limited-access alpha',now())
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
select ds.id,p.policy_url,'2026-10-07T07:30:00Z'::timestamptz,
       p.commercial_use_allowed,p.automated_collection_allowed,p.redisplay_allowed,
       p.fulltext_storage_allowed,p.internal_research_allowed,
       p.derived_public_analytics_allowed,p.written_permission_required,
       p.allowed_use_scope,p.policy_basis,p.notes,
       encode(digest(ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-07-P41','sha256'),'hex')
from (
  values
  ('npm','https://docs.npmjs.com/policies/open-source-terms/',
   true,true,true,false,true,true,false,
   'PUBLIC_REGISTRY_API_PACKAGE_METADATA_AND_DERIVED_AGGREGATES',
   'OFFICIAL_PUBLIC_API_AND_OPEN_SOURCE_TERMS',
   'npm terms permit use of documented Public APIs and commercial/business use. JianShi limits collection to public package metadata and aggregate/search metrics; no user PII or package fulltext mirroring.'),
  ('stack_exchange','https://stackoverflow.com/legal/api-terms-of-use',
   true,true,true,false,true,true,false,
   'OFFICIAL_API_AGGREGATE_TAG_AND_QUESTION_METADATA_WITH_ATTRIBUTION',
   'OFFICIAL_API_TERMS_WITH_ATTRIBUTION',
   'Official API is available for programmatic use. JianShi will prefer aggregate tag/question metadata, honor throttles and attribution, and avoid storing full question bodies.'),
  ('hacker_news','https://github.com/HackerNews/API',
   null,false,false,false,true,false,true,
   'MANUAL_RESEARCH_PENDING_COMMERCIAL_REUSE_REVIEW',
   'OFFICIAL_PUBLIC_API_WITHOUT_VERIFIED_COMMERCIAL_REDISPLAY_SCOPE',
   'Official API exposes public HN data and currently documents no rate limit, but P4.1 did not identify an explicit commercial republication license. Keep YELLOW/fail-closed.'),
  ('product_hunt','https://api.producthunt.com/v2/docs',
   false,false,false,false,true,false,true,
   'MANUAL_RESEARCH_AND_PERMISSION_OUTREACH_ONLY',
   'OFFICIAL_API_EXPLICITLY_NONCOMMERCIAL_BY_DEFAULT',
   'Product Hunt API documentation explicitly states the API must not be used for commercial purposes by default and instructs businesses to contact Product Hunt for permission.'),
  ('reddit','https://redditinc.com/policies/developer-terms',
   false,false,false,false,true,false,true,
   'MANUAL_RESEARCH_AND_COMMERCIAL_CONTRACT_OUTREACH_ONLY',
   'OFFICIAL_TERMS_REQUIRE_PERMISSION_FOR_COMMERCIAL_DATA_USE',
   'Reddit commercial developer/data use requires permission and normally a separate agreement; unauthorized scraping is prohibited.'),
  ('google_trends','https://developers.google.com/search/apis/trends',
   null,false,false,false,true,false,true,
   'APPLY_FOR_OFFICIAL_ALPHA_ACCESS_THEN_REVIEW_TERMS',
   'OFFICIAL_API_LIMITED_ALPHA_ACCESS',
   'Google Trends API exists but remains limited-access alpha. Do not automate website scraping as a substitute.')
) as p(code,policy_url,commercial_use_allowed,automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
       internal_research_allowed,derived_public_analytics_allowed,written_permission_required,
       allowed_use_scope,policy_basis,notes)
join data_sources ds on ds.code=p.code
where not exists (
  select 1 from source_policies sp
  where sp.source_id=ds.id
    and sp.evidence_hash=encode(digest(ds.code || '|' || p.policy_url || '|' || p.policy_basis || '|2026-10-07-P41','sha256'),'hex')
);

-- New evidence types are shadow-only in P4.1 and cannot satisfy public_ready.
insert into evidence_class_rules(evidence_type,evidence_class,counts_for_public_validation,notes)
values
('NPM_PACKAGE','TECHNICAL_SUPPLY',false,'Public npm package/adoption metadata. Shadow-only in P4.1; does not replace GitHub technical validation.'),
('STACKEXCHANGE_TAG','DEMAND_SIGNAL',false,'Developer question/tag demand proxy. Shadow-only; does not satisfy public validation.'),
('HN_STORY','DEMAND_SIGNAL',false,'Hacker News discussion/product signal. Disabled pending policy review.'),
('PRODUCTHUNT_POST','DISTRIBUTION_SIGNAL',false,'Product launch/distribution signal. Disabled pending commercial permission.'),
('REDDIT_POST','DEMAND_SIGNAL',false,'Community demand signal. Disabled pending commercial contract.'),
('GOOGLE_TRENDS_TERM','DEMAND_SIGNAL',false,'Search-interest signal. Disabled until official API access is granted.')
on conflict(evidence_type) do update set
  evidence_class=excluded.evidence_class,
  counts_for_public_validation=excluded.counts_for_public_validation,
  notes=excluded.notes,
  updated_at=now();

-- Generic source signal layer. This keeps future product/demand/adoption sources
-- separate from core Opportunity scoring until they have enough history.
create table if not exists external_signal_queries (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references data_sources(id) on delete cascade,
  code text not null unique,
  query_type text not null,
  query_spec jsonb not null default '{}'::jsonb,
  evidence_type text not null references evidence_class_rules(evidence_type),
  enabled boolean not null default true,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists external_signal_entities (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references data_sources(id) on delete cascade,
  source_external_id text not null,
  entity_type text not null,
  title text not null,
  source_url text,
  metadata jsonb not null default '{}'::jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(source_id,source_external_id)
);

create table if not exists external_signal_discoveries (
  entity_id uuid not null references external_signal_entities(id) on delete cascade,
  query_id uuid not null references external_signal_queries(id) on delete cascade,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  primary key(entity_id,query_id)
);

create table if not exists external_signal_snapshots (
  id bigserial primary key,
  entity_id uuid not null references external_signal_entities(id) on delete cascade,
  source_id uuid not null references data_sources(id) on delete cascade,
  observed_at timestamptz not null,
  snapshot_hash text not null,
  metrics jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(entity_id,snapshot_hash)
);

create index if not exists idx_external_signal_queries_source
  on external_signal_queries(source_id,enabled);
create index if not exists idx_external_signal_entities_source_seen
  on external_signal_entities(source_id,last_seen_at desc);
create index if not exists idx_external_signal_discoveries_query
  on external_signal_discoveries(query_id,last_seen_at desc);
create index if not exists idx_external_signal_snapshots_entity_time
  on external_signal_snapshots(entity_id,observed_at desc);
create index if not exists idx_external_signal_snapshots_source_time
  on external_signal_snapshots(source_id,observed_at desc);

create table if not exists opportunity_external_query_map (
  opportunity_id uuid not null references opportunities(id) on delete cascade,
  query_id uuid not null references external_signal_queries(id) on delete cascade,
  weight numeric(6,3) not null default 1.0,
  rule_code text not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(opportunity_id,query_id)
);
create index if not exists idx_opportunity_external_query_map_query
  on opportunity_external_query_map(query_id);

alter table external_signal_queries enable row level security;
alter table external_signal_entities enable row level security;
alter table external_signal_discoveries enable row level security;
alter table external_signal_snapshots enable row level security;
alter table opportunity_external_query_map enable row level security;

revoke all on external_signal_queries,external_signal_entities,external_signal_discoveries,
  external_signal_snapshots,opportunity_external_query_map from public,anon,authenticated;
revoke all on sequence external_signal_snapshots_id_seq from public,anon,authenticated;
grant select,insert,update,delete on external_signal_queries,external_signal_entities,
  external_signal_discoveries,external_signal_snapshots,opportunity_external_query_map to service_role;
grant usage,select on sequence external_signal_snapshots_id_seq to service_role;

-- npm queries: first use existing opportunity taxonomy; broader candidate taxonomy
-- will be added only after observing real source data.
insert into external_signal_queries(source_id,code,query_type,query_spec,evidence_type,enabled,notes)
select ds.id,x.code,'NPM_SEARCH',
       jsonb_build_object('text',x.search_text,'size',50),
       'NPM_PACKAGE',true,x.notes
from data_sources ds
cross join (
  values
  ('npm_ai_agents','ai agent','AI Agent packages and frameworks'),
  ('npm_llm','llm openai','LLM SDKs, wrappers and application tooling'),
  ('npm_saas','saas billing auth','SaaS product infrastructure'),
  ('npm_ecommerce','shopify ecommerce','eCommerce and Shopify tooling'),
  ('npm_affiliate','affiliate marketing','Affiliate and marketing tooling'),
  ('npm_creator','newsletter youtube creator','Creator/newsletter/video tooling')
) as x(code,search_text,notes)
where ds.code='npm'
on conflict(code) do update set
  query_spec=excluded.query_spec,
  evidence_type=excluded.evidence_type,
  enabled=true,
  notes=excluded.notes,
  updated_at=now();

insert into opportunity_external_query_map(opportunity_id,query_id,weight,rule_code)
select o.id,q.id,x.weight,x.rule_code
from (
  values
  ('ai-agent-tools','npm_ai_agents',0.80::numeric,'npm_query_ai_agents'),
  ('llm-tools','npm_llm',0.80::numeric,'npm_query_llm'),
  ('solo-saas','npm_saas',0.65::numeric,'npm_query_saas'),
  ('ecommerce-brands','npm_ecommerce',0.60::numeric,'npm_query_ecommerce'),
  ('affiliate-content','npm_affiliate',0.55::numeric,'npm_query_affiliate'),
  ('creator-media','npm_creator',0.55::numeric,'npm_query_creator')
) as x(opportunity_slug,query_code,weight,rule_code)
join opportunities o on o.slug=x.opportunity_slug
join external_signal_queries q on q.code=x.query_code
on conflict(opportunity_id,query_id) do update set
  weight=excluded.weight,
  rule_code=excluded.rule_code,
  active=true,
  updated_at=now();

create or replace view opportunity_external_signal_shadow_v01
with (security_invoker=true) as
select
  m.opportunity_id,
  o.slug,
  ds.code as source_code,
  ecr.evidence_class,
  count(distinct d.entity_id) as entity_count,
  max(e.last_seen_at) as latest_seen_at,
  max(s.observed_at) as latest_snapshot_at
from opportunity_external_query_map m
join opportunities o on o.id=m.opportunity_id
join external_signal_queries q on q.id=m.query_id and q.enabled=true
join data_sources ds on ds.id=q.source_id
join evidence_class_rules ecr on ecr.evidence_type=q.evidence_type
left join external_signal_discoveries d on d.query_id=q.id
left join external_signal_entities e on e.id=d.entity_id
left join lateral (
  select max(es.observed_at) as observed_at
  from external_signal_snapshots es
  where es.entity_id=d.entity_id
) s on true
where m.active=true
group by m.opportunity_id,o.slug,ds.code,ecr.evidence_class;

revoke all on opportunity_external_signal_shadow_v01 from public,anon,authenticated;
grant select on opportunity_external_signal_shadow_v01 to service_role;

comment on table external_signal_queries is
'P4.1 generic source-query registry for product, demand and adoption signals. Non-GREEN sources remain disabled/fail-closed.';
comment on view opportunity_external_signal_shadow_v01 is
'P4.1 shadow-only external signal summary. Does not alter OPP_V0.2 or public_ready.';
