-- Normalize current GREEN policy rows to the expanded R7.6 policy contract.

insert into source_policies(
  source_id,policy_url,reviewed_at,commercial_use_allowed,
  automated_collection_allowed,redisplay_allowed,fulltext_storage_allowed,
  internal_research_allowed,derived_public_analytics_allowed,
  written_permission_required,allowed_use_scope,policy_basis,notes,evidence_hash
)
select ds.id,p.policy_url,'2026-10-06T15:50:00Z'::timestamptz,
       true,true,true,false,true,true,false,
       p.allowed_use_scope,p.policy_basis,p.notes,
       encode(digest(ds.code || '|' || p.policy_url || '|GREEN|2026-10-06','sha256'),'hex')
from (
  values
  ('empire_flippers','https://empireflippers.com/marketplace-api/',
   'OFFICIAL_API_SYNDICATION',
   'OFFICIAL_API_EXPLICIT_SYNDICATION_PERMISSION',
   'Marketplace API explicitly permits syndicating listings on your own website/email list and building a meta-marketplace; rate limit <=1 req/s.'),
  ('github','https://docs.github.com/en/rest',
   'PUBLIC_REPOSITORY_METADATA_API',
   'OFFICIAL_PUBLIC_API',
   'Use only public repository metadata under GitHub API terms and rate limits; no private repository access.')
) as p(code,policy_url,allowed_use_scope,policy_basis,notes)
join data_sources ds on ds.code=p.code;

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
     or r.commercial_use_allowed is not true
     or r.automated_collection_allowed is not true
     or r.redisplay_allowed is not true
     or r.derived_public_analytics_allowed is not true then
    raise exception 'PUBLICATION_FORBIDDEN_BY_SOURCE_POLICY: %',p_source_code;
  end if;
  return true;
end;
$$;

revoke all on function assert_source_publication_allowed_v01(text) from public,anon,authenticated;
