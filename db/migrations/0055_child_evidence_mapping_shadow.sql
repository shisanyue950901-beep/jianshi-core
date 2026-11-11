-- P4.5B Staging-only child opportunity evidence mapping engine.
-- Converts P4.5A human-audited marketplace semantics into repeatable rules.
-- No public publication, no OPP_V0.2/public_ready changes, no Production schedule.

create table if not exists child_opportunity_shadow_registry (
  child_slug text primary key,
  parent_opportunity_id uuid not null references opportunities(id) on delete restrict,
  current_title text not null,
  recommended_title text not null,
  archetype text not null check (archetype in ('SOFTWARE','CONTENT_ASSET','COMMERCE_ASSET')),
  editorial_decision text not null,
  publication_state text not null default 'DRAFT' check (publication_state in ('DRAFT','REVIEWED','PUBLISHED')),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists child_marketplace_mapping_rules (
  id uuid primary key default gen_random_uuid(),
  rule_code text not null unique,
  child_slug text not null references child_opportunity_shadow_registry(child_slug) on delete cascade,
  source_id uuid not null references data_sources(id) on delete restrict,
  any_monetizations text[] not null default '{}'::text[],
  all_monetizations text[] not null default '{}'::text[],
  excluded_monetizations text[] not null default '{}'::text[],
  title_contains_all text[] not null default '{}'::text[],
  require_nonempty_niches boolean not null default false,
  confidence text not null check (confidence in ('HIGH','MEDIUM','LOW')),
  auto_approve boolean not null default false,
  rule_version text not null,
  active boolean not null default true,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists child_marketplace_evidence_matches (
  id uuid primary key default gen_random_uuid(),
  child_slug text not null references child_opportunity_shadow_registry(child_slug) on delete cascade,
  listing_id uuid not null references marketplace_listings(id) on delete cascade,
  rule_id uuid not null references child_marketplace_mapping_rules(id) on delete cascade,
  source_id uuid not null references data_sources(id) on delete restrict,
  mapping_confidence text not null check (mapping_confidence in ('HIGH','MEDIUM','LOW')),
  review_status text not null check (review_status in ('AUTO_APPROVED','REVIEW_REQUIRED','REJECTED')),
  active boolean not null default true,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique(child_slug,listing_id,rule_id)
);

create index if not exists idx_child_mapping_rules_child
  on child_marketplace_mapping_rules(child_slug,active);
create index if not exists idx_child_mapping_rules_source
  on child_marketplace_mapping_rules(source_id,active);
create index if not exists idx_child_evidence_matches_child_active
  on child_marketplace_evidence_matches(child_slug,active);
create index if not exists idx_child_evidence_matches_listing_active
  on child_marketplace_evidence_matches(listing_id,active);
create index if not exists idx_child_evidence_matches_review
  on child_marketplace_evidence_matches(review_status,active);

alter table child_opportunity_shadow_registry enable row level security;
alter table child_marketplace_mapping_rules enable row level security;
alter table child_marketplace_evidence_matches enable row level security;

revoke all on child_opportunity_shadow_registry,child_marketplace_mapping_rules,
  child_marketplace_evidence_matches from public,anon,authenticated;
grant select,insert,update,delete on child_opportunity_shadow_registry,
  child_marketplace_mapping_rules,child_marketplace_evidence_matches to service_role;

insert into child_opportunity_shadow_registry(
  child_slug,parent_opportunity_id,current_title,recommended_title,archetype,editorial_decision
)
select x.child_slug,o.id,x.current_title,x.recommended_title,x.archetype,x.editorial_decision
from (
  values
  ('vertical-micro-saas','solo-saas','垂直行业 Micro SaaS','垂直行业 SaaS','SOFTWARE','RENAME_AND_WORTH_RESEARCH'),
  ('affiliate-seo-content-site','affiliate-content','联盟营销 / SEO 内容站','联盟营销 / 内容站','CONTENT_ASSET','RENAME_AND_WORTH_RESEARCH'),
  ('amazon-fba-niche-brand','ecommerce-brands','Amazon FBA 细分品牌','Amazon FBA 细分品牌','COMMERCE_ASSET','WORTH_RESEARCH'),
  ('youtube-niche-media','creator-media','YouTube 垂直媒体资产','YouTube 垂直媒体资产','CONTENT_ASSET','WORTH_RESEARCH'),
  ('digital-product-business','creator-media','数字产品业务','数字产品业务','CONTENT_ASSET','WORTH_RESEARCH'),
  ('newsletter-media-business','creator-media','Newsletter 订阅媒体','Newsletter 订阅媒体','CONTENT_ASSET','WORTH_RESEARCH_LOW_CONFIDENCE'),
  ('amazon-kdp-publishing','affiliate-content','Amazon KDP 数字出版','Amazon KDP 数字出版','CONTENT_ASSET','WORTH_RESEARCH'),
  ('crossborder-dtc-brand','ecommerce-brands','跨境 DTC / 独立站品牌','非 Amazon 电商品牌','COMMERCE_ASSET','RENAME_AND_WORTH_RESEARCH')
) as x(child_slug,parent_slug,current_title,recommended_title,archetype,editorial_decision)
join opportunities o on o.slug=x.parent_slug
on conflict(child_slug) do update set
  parent_opportunity_id=excluded.parent_opportunity_id,
  current_title=excluded.current_title,
  recommended_title=excluded.recommended_title,
  archetype=excluded.archetype,
  editorial_decision=excluded.editorial_decision,
  updated_at=now();

insert into child_marketplace_mapping_rules(
  rule_code,child_slug,source_id,any_monetizations,all_monetizations,
  excluded_monetizations,title_contains_all,require_nonempty_niches,
  confidence,auto_approve,rule_version,notes
)
select x.rule_code,x.child_slug,ds.id,x.any_monetizations,x.all_monetizations,
       x.excluded_monetizations,x.title_contains_all,x.require_nonempty_niches,
       x.confidence,x.auto_approve,'P45B_V1',x.notes
from data_sources ds
cross join (
  values
  ('P45B_SAAS_VERTICAL','vertical-micro-saas',
    array['SaaS']::text[],array[]::text[],array[]::text[],array[]::text[],true,
    'MEDIUM',false,'Structured SaaS monetization plus non-empty niche. Human review retained because SaaS alone does not fully prove verticality.'),
  ('P45B_AFFILIATE_CONTENT_SITE','affiliate-seo-content-site',
    array['Affiliate','Amazon Associates','Display Advertising']::text[],array[]::text[],array[]::text[],array['Site']::text[],false,
    'HIGH',true,'Site title plus direct affiliate/ad monetization. Recommended child title removes unsupported SEO claim.'),
  ('P45B_AMAZON_FBA','amazon-fba-niche-brand',
    array['Amazon FBA']::text[],array[]::text[],array[]::text[],array[]::text[],false,
    'HIGH',true,'Exact structured Amazon FBA monetization.'),
  ('P45B_YOUTUBE_MEDIA','youtube-niche-media',
    array['YouTube']::text[],array[]::text[],array[]::text[],array[]::text[],false,
    'HIGH',true,'Exact structured YouTube monetization.'),
  ('P45B_DIGITAL_PRODUCT','digital-product-business',
    array['Digital Product']::text[],array[]::text[],array[]::text[],array[]::text[],false,
    'HIGH',true,'Exact structured Digital Product monetization.'),
  ('P45B_NEWSLETTER_MEDIA','newsletter-media-business',
    array['Newsletter']::text[],array[]::text[],array[]::text[],array[]::text[],false,
    'HIGH',true,'Exact structured Newsletter monetization; opportunity-level confidence remains low because sample count is small.'),
  ('P45B_AMAZON_KDP','amazon-kdp-publishing',
    array['Amazon KDP']::text[],array[]::text[],array[]::text[],array[]::text[],false,
    'HIGH',true,'Exact structured Amazon KDP monetization.'),
  ('P45B_NON_AMAZON_ECOMMERCE','crossborder-dtc-brand',
    array['eCommerce']::text[],array[]::text[],array['Amazon FBA','Amazon FBM']::text[],array[]::text[],false,
    'HIGH',true,'Exact eCommerce monetization excluding Amazon FBA/FBM. Recommended child title removes unsupported cross-border/DTC/site claims.')
) as x(
  rule_code,child_slug,any_monetizations,all_monetizations,
  excluded_monetizations,title_contains_all,require_nonempty_niches,
  confidence,auto_approve,notes
)
where ds.code='empire_flippers'
on conflict(rule_code) do update set
  child_slug=excluded.child_slug,
  source_id=excluded.source_id,
  any_monetizations=excluded.any_monetizations,
  all_monetizations=excluded.all_monetizations,
  excluded_monetizations=excluded.excluded_monetizations,
  title_contains_all=excluded.title_contains_all,
  require_nonempty_niches=excluded.require_nonempty_niches,
  confidence=excluded.confidence,
  auto_approve=excluded.auto_approve,
  rule_version=excluded.rule_version,
  notes=excluded.notes,
  active=true,
  updated_at=now();

create or replace function refresh_child_marketplace_evidence_v01()
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_active_matches integer;
  v_auto integer;
  v_review integer;
  v_children integer;
  v_sources integer;
begin
  -- Fail closed: mark old active matches inactive before re-evaluating current source data.
  update child_marketplace_evidence_matches
  set active=false,last_seen_at=now()
  where active=true;

  insert into child_marketplace_evidence_matches(
    child_slug,listing_id,rule_id,source_id,mapping_confidence,review_status,
    active,first_seen_at,last_seen_at
  )
  select
    r.child_slug,
    ml.id,
    r.id,
    ml.source_id,
    r.confidence,
    case when r.auto_approve and r.confidence='HIGH'
      then 'AUTO_APPROVED'
      else 'REVIEW_REQUIRED'
    end,
    true,
    now(),
    now()
  from child_marketplace_mapping_rules r
  join child_opportunity_shadow_registry c
    on c.child_slug=r.child_slug and c.active=true
  join marketplace_listings ml
    on ml.source_id=r.source_id and ml.active=true
  where r.active=true
    and (
      cardinality(r.any_monetizations)=0
      or exists(
        select 1
        from jsonb_array_elements_text(ml.monetizations) m(value)
        where m.value=any(r.any_monetizations)
      )
    )
    and (
      cardinality(r.all_monetizations)=0
      or not exists(
        select 1
        from unnest(r.all_monetizations) req
        where not exists(
          select 1
          from jsonb_array_elements_text(ml.monetizations) m(value)
          where m.value=req
        )
      )
    )
    and (
      cardinality(r.excluded_monetizations)=0
      or not exists(
        select 1
        from jsonb_array_elements_text(ml.monetizations) m(value)
        where m.value=any(r.excluded_monetizations)
      )
    )
    and (
      cardinality(r.title_contains_all)=0
      or not exists(
        select 1
        from unnest(r.title_contains_all) token
        where coalesce(ml.public_title,'') not ilike '%' || token || '%'
      )
    )
    and (
      r.require_nonempty_niches=false
      or jsonb_array_length(ml.niches)>0
    )
  on conflict(child_slug,listing_id,rule_id) do update set
    source_id=excluded.source_id,
    mapping_confidence=excluded.mapping_confidence,
    review_status=excluded.review_status,
    active=true,
    last_seen_at=now();

  select count(*) into v_active_matches
  from child_marketplace_evidence_matches where active=true;

  select count(*) into v_auto
  from child_marketplace_evidence_matches
  where active=true and review_status='AUTO_APPROVED';

  select count(*) into v_review
  from child_marketplace_evidence_matches
  where active=true and review_status='REVIEW_REQUIRED';

  select count(distinct child_slug) into v_children
  from child_marketplace_evidence_matches where active=true;

  select count(distinct source_id) into v_sources
  from child_marketplace_evidence_matches where active=true;

  return jsonb_build_object(
    'rule_version','P45B_V1',
    'active_matches',v_active_matches,
    'auto_approved',v_auto,
    'review_required',v_review,
    'matched_children',v_children,
    'commercial_source_diversity',v_sources,
    'publication_changed',false,
    'scoring_changed',false
  );
end;
$$;

revoke all on function refresh_child_marketplace_evidence_v01()
  from public,anon,authenticated;
grant execute on function refresh_child_marketplace_evidence_v01()
  to service_role;

create or replace view child_evidence_mapping_summary_v01
with (security_invoker=true) as
select
  c.child_slug,
  c.recommended_title,
  c.archetype,
  c.editorial_decision,
  count(m.id) filter(where m.active) as active_matches,
  count(m.id) filter(where m.active and m.review_status='AUTO_APPROVED') as auto_approved_matches,
  count(m.id) filter(where m.active and m.review_status='REVIEW_REQUIRED') as review_required_matches,
  count(distinct m.source_id) filter(where m.active) as source_diversity,
  max(m.last_seen_at) filter(where m.active) as last_mapped_at
from child_opportunity_shadow_registry c
left join child_marketplace_evidence_matches m on m.child_slug=c.child_slug
where c.active=true
group by c.child_slug,c.recommended_title,c.archetype,c.editorial_decision;

create or replace view child_evidence_review_queue_v01
with (security_invoker=true) as
select
  m.id as match_id,
  m.child_slug,
  c.recommended_title,
  ml.id as listing_id,
  ml.public_title,
  ml.monetizations,
  ml.niches,
  r.rule_code,
  r.rule_version,
  m.mapping_confidence,
  m.review_status,
  m.last_seen_at,
  'RULE_REQUIRES_HUMAN_CONFIRMATION'::text as review_reason
from child_marketplace_evidence_matches m
join child_opportunity_shadow_registry c on c.child_slug=m.child_slug
join child_marketplace_mapping_rules r on r.id=m.rule_id
join marketplace_listings ml on ml.id=m.listing_id
where m.active=true
  and m.review_status='REVIEW_REQUIRED';

revoke all on child_evidence_mapping_summary_v01,child_evidence_review_queue_v01
  from public,anon,authenticated;
grant select on child_evidence_mapping_summary_v01,child_evidence_review_queue_v01
  to service_role;

comment on table child_marketplace_mapping_rules is
'P4.5B service-role-only mapping rules converted from the first human child-evidence audit. Rules classify evidence only; they cannot publish opportunities.';
comment on table child_marketplace_evidence_matches is
'P4.5B shadow evidence matches. Same listing may support more than one child, but never increases source diversity.';
comment on function refresh_child_marketplace_evidence_v01() is
'Idempotent P4.5B rule refresh. Intended for later collector/scheduler hook; P4.5B does not create a Production schedule.';
