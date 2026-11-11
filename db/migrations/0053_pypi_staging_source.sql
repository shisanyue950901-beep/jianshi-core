-- P4.1.4 PyPI Staging-only source validation.
-- This migration is intended for Staging evaluation first.
-- It does not alter OPP_V0.2, public_ready, Auth or public feed.

insert into data_sources(
  code,name,homepage_url,source_status,access_method,auto_collect,redisplay_allowed,
  raw_storage_policy,refresh_interval_minutes,rate_limit_note,updated_at
)
values(
  'pypi',
  'Python Package Index (PyPI)',
  'https://pypi.org',
  'GREEN',
  'OFFICIAL_RSS_PLUS_JSON_API',
  true,
  true,
  'LIMITED_PUBLIC_PACKAGE_METADATA_ONLY_NO_PACKAGE_CONTENT',
  360,
  'Use official RSS for new/update discovery; JSON metadata requests serialized/batched with identifiable User-Agent and cache-aware cadence.',
  now()
)
on conflict(code) do update set
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
select ds.id,
       'https://policies.python.org/pypi.org/Terms-of-Service/',
       '2026-10-07T08:45:00Z'::timestamptz,
       true,true,true,false,true,true,false,
       'OFFICIAL_RSS_AND_JSON_API_LIMITED_PUBLIC_PACKAGE_METADATA_AND_DERIVED_AGGREGATES',
       'PYPI_OFFICIAL_API_TERMS_AND_PUBLIC_API_DOCUMENTATION',
       'P4.1.4 stores limited package metadata and derived category signals only. Package archives, README/full descriptions, user identities and deprecated JSON downloads are excluded. BigQuery download statistics are not used in this Staging experiment.',
       encode(digest('pypi|official-rss-json|2026-10-07-P414','sha256'),'hex')
from data_sources ds
where ds.code='pypi'
  and not exists (
    select 1 from source_policies sp
    where sp.source_id=ds.id
      and sp.evidence_hash=encode(digest('pypi|official-rss-json|2026-10-07-P414','sha256'),'hex')
  );

insert into evidence_class_rules(
  evidence_type,evidence_class,counts_for_public_validation,notes
)
values(
  'PYPI_PACKAGE',
  'TECHNICAL_SUPPLY',
  false,
  'PyPI public package/release metadata. P4.1.4 Staging shadow only; does not replace GitHub technical validation or commercial proof.'
)
on conflict(evidence_type) do update set
  evidence_class=excluded.evidence_class,
  counts_for_public_validation=false,
  notes=excluded.notes,
  updated_at=now();

insert into external_signal_queries(
  source_id,code,query_type,query_spec,evidence_type,enabled,notes
)
select ds.id,x.code,'PYPI_RSS',
       jsonb_build_object('feed_url',x.feed_url,'max_items',40),
       'PYPI_PACKAGE',true,x.notes
from data_sources ds
cross join (
  values
  ('pypi_newest','https://pypi.org/rss/packages.xml','Official Newest Packages feed; candidate discovery'),
  ('pypi_updates','https://pypi.org/rss/updates.xml','Official Latest Updates feed; release activity')
) as x(code,feed_url,notes)
where ds.code='pypi'
on conflict(code) do update set
  query_spec=excluded.query_spec,
  evidence_type=excluded.evidence_type,
  enabled=true,
  notes=excluded.notes,
  updated_at=now();

comment on table external_signal_queries is
'Generic external signal query registry. P4.1.4 adds PyPI official RSS discovery in Staging shadow mode.';
