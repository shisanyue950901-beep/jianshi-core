-- R7.9: upstream provenance inheritance.
-- A public aggregator/API cannot "launder" a restricted upstream marketplace into GREEN use.

insert into data_sources(
  code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,
  raw_storage_policy,refresh_interval_minutes,rate_limit_note,updated_at
)
values (
  'foundersprime','FoundersPrime','https://www.foundersprime.com',
  'YELLOW','OFFICIAL_PUBLIC_API_UPSTREAM_RESTRICTED',false,false,
  'NO_PRODUCTION_MARKETPLACE_STORAGE_UNTIL_UPSTREAM_RIGHTS_VERIFIED',
  null,'Public API advertises 100 req/min; production disabled pending upstream sublicense review',now()
)
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
select
  ds.id,
  'https://www.foundersprime.com/terms',
  '2026-10-06T16:35:00Z'::timestamptz,
  null,false,false,false,true,false,true,
  'PUBLIC_API_RESEARCH_ONLY_UNTIL_UPSTREAM_SUBLICENSE_VERIFIED',
  'OFFICIAL_PUBLIC_API_WITH_RESTRICTED_UPSTREAM_PROVENANCE',
  'FoundersPrime explicitly supports public API reading/indexing/citation with attribution, but its /api/v1/startups audit currently resolves entirely to Acquire.com and TrustMRR. JianShi requires proof of upstream sublicensing or source-specific permission before production use.',
  encode(digest('foundersprime|upstream-provenance|2026-10-07','sha256'),'hex')
from data_sources ds
where ds.code='foundersprime';

create table if not exists source_provenance_rules (
  id uuid primary key default gen_random_uuid(),
  aggregator_source_id uuid not null references data_sources(id) on delete cascade,
  upstream_label text not null,
  upstream_source_id uuid references data_sources(id) on delete restrict,
  policy_mode text not null
    check (policy_mode in ('INHERIT','EXPLICIT_ALLOW','BLOCK')),
  written_permission_reference text,
  reviewed_at timestamptz not null default now(),
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(aggregator_source_id,upstream_label)
);

create table if not exists source_provenance_audits (
  id uuid primary key default gen_random_uuid(),
  aggregator_source_id uuid not null references data_sources(id) on delete cascade,
  api_path text not null,
  sample_count integer not null check(sample_count>=0),
  upstream_counts jsonb not null default '{}'::jsonb,
  audit_result text not null
    check (audit_result in ('PASS','PASS_WITH_BLOCKS','BLOCKED','INCOMPLETE')),
  audited_at timestamptz not null default now(),
  notes text,
  evidence_hash text,
  created_at timestamptz not null default now()
);

alter table source_provenance_rules enable row level security;
alter table source_provenance_audits enable row level security;
revoke all on source_provenance_rules,source_provenance_audits from anon,authenticated;

insert into source_provenance_rules(
  aggregator_source_id,upstream_label,upstream_source_id,policy_mode,reviewed_at,notes
)
select a.id,'Acquire.com',u.id,'INHERIT','2026-10-06T16:35:00Z'::timestamptz,
       'FoundersPrime startup record inherits Acquire.com restrictions unless written sublicense evidence is reviewed.'
from data_sources a
join data_sources u on u.code='acquire'
where a.code='foundersprime'
on conflict (aggregator_source_id,upstream_label) do update set
  upstream_source_id=excluded.upstream_source_id,
  policy_mode=excluded.policy_mode,
  reviewed_at=excluded.reviewed_at,
  notes=excluded.notes,
  updated_at=now();

insert into source_provenance_rules(
  aggregator_source_id,upstream_label,upstream_source_id,policy_mode,reviewed_at,notes
)
select a.id,'TrustMRR',u.id,'INHERIT','2026-10-06T16:35:00Z'::timestamptz,
       'FoundersPrime startup record inherits TrustMRR restrictions unless written sublicense evidence is reviewed.'
from data_sources a
join data_sources u on u.code='trustmrr'
where a.code='foundersprime'
on conflict (aggregator_source_id,upstream_label) do update set
  upstream_source_id=excluded.upstream_source_id,
  policy_mode=excluded.policy_mode,
  reviewed_at=excluded.reviewed_at,
  notes=excluded.notes,
  updated_at=now();

insert into source_provenance_audits(
  aggregator_source_id,api_path,sample_count,upstream_counts,audit_result,audited_at,notes,evidence_hash
)
select
  ds.id,
  '/api/v1/startups?limit=100',
  1150,
  '{"Acquire.com":618,"TrustMRR":532}'::jsonb,
  'BLOCKED',
  '2026-10-06T16:35:00Z'::timestamptz,
  'Live Staging audit: all 1,150 returned startup rows were attributed to upstream sources already RED/YELLOW in JianShi. No row is eligible for production publication.',
  encode(digest('foundersprime|1150|Acquire.com:618|TrustMRR:532|2026-10-07','sha256'),'hex')
from data_sources ds
where ds.code='foundersprime'
  and not exists (
    select 1 from source_provenance_audits a
    where a.aggregator_source_id=ds.id
      and a.evidence_hash=encode(digest('foundersprime|1150|Acquire.com:618|TrustMRR:532|2026-10-07','sha256'),'hex')
  );

insert into source_permission_requests(
  source_id,request_status,requested_scopes,contact_channel,notes
)
select ds.id,'DRAFT',
  '["AUTOMATED_API_OR_FEED","HISTORICAL_SNAPSHOT_STORAGE","DERIVED_ANALYTICS","PUBLIC_SUMMARY_DISPLAY","COMMERCIAL_PRODUCT_USE","UPSTREAM_SUBLICENSE_CONFIRMATION"]'::jsonb,
  'support@foundersprime.com',
  'Request written confirmation that FoundersPrime is authorized to sublicense/re-display Acquire.com and TrustMRR sourced startup fields in third-party commercial products, or request an API filter limited to direct/licensed origins.'
from data_sources ds
where ds.code='foundersprime'
  and not exists (
    select 1 from source_permission_requests spr
    where spr.source_id=ds.id
      and spr.request_status in ('DRAFT','SENT','APPROVED','PARTIAL_APPROVAL')
  );

create or replace view source_provenance_effective_v01 as
select
  a.code as aggregator_code,
  r.upstream_label,
  u.code as upstream_source_code,
  r.policy_mode,
  a.source_status as aggregator_status,
  a.auto_collect as aggregator_auto_collect,
  a.redisplay_allowed as aggregator_redisplay_allowed,
  u.source_status as upstream_status,
  u.auto_collect as upstream_auto_collect,
  u.redisplay_allowed as upstream_redisplay_allowed,
  r.written_permission_reference,
  r.reviewed_at,
  r.notes
from source_provenance_rules r
join data_sources a on a.id=r.aggregator_source_id
left join data_sources u on u.id=r.upstream_source_id;

alter view source_provenance_effective_v01 set (security_invoker=true);

create or replace function assert_aggregated_item_publication_allowed_v01(
  p_aggregator_code text,
  p_upstream_label text
)
returns boolean
language plpgsql
security definer
set search_path=public
as $$
declare
  agg data_sources%rowtype;
  rule source_provenance_rules%rowtype;
  upstream_code text;
begin
  select * into agg
  from data_sources
  where code=p_aggregator_code;

  if not found then
    raise exception 'UNKNOWN_AGGREGATOR_SOURCE: %',p_aggregator_code;
  end if;

  -- First, the aggregator itself must be production-eligible.
  perform assert_source_publication_allowed_v01(p_aggregator_code);

  select * into rule
  from source_provenance_rules
  where aggregator_source_id=agg.id
    and lower(upstream_label)=lower(p_upstream_label);

  if not found then
    raise exception 'UNKNOWN_UPSTREAM_PROVENANCE: % / %',p_aggregator_code,p_upstream_label;
  end if;

  if rule.policy_mode='BLOCK' then
    raise exception 'UPSTREAM_PUBLICATION_BLOCKED: % / %',p_aggregator_code,p_upstream_label;
  end if;

  if rule.policy_mode='EXPLICIT_ALLOW' then
    if coalesce(rule.written_permission_reference,'')='' then
      raise exception 'EXPLICIT_ALLOW_REQUIRES_WRITTEN_EVIDENCE: % / %',p_aggregator_code,p_upstream_label;
    end if;
    return true;
  end if;

  if rule.upstream_source_id is null then
    raise exception 'UPSTREAM_SOURCE_UNRESOLVED: % / %',p_aggregator_code,p_upstream_label;
  end if;

  select code into upstream_code
  from data_sources
  where id=rule.upstream_source_id;

  perform assert_source_publication_allowed_v01(upstream_code);
  return true;
end;
$$;

revoke all on function assert_aggregated_item_publication_allowed_v01(text,text)
  from public,anon,authenticated;

comment on table source_provenance_rules is
'R7.9 upstream rights inheritance. Aggregator APIs never override upstream restrictions without reviewed written evidence.';
comment on table source_provenance_audits is
'Observed upstream provenance distribution for aggregator APIs. Audit rows are policy evidence, not production marketplace data.';
