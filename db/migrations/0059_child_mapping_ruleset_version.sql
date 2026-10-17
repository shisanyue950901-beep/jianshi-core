-- P4.5D ruleset audit version hardening.
-- Centralize the effective child-evidence mapping ruleset version so audit
-- results do not report the superseded P45B_V1 after SaaS refinement.

create or replace function child_evidence_mapping_ruleset_version_v01()
returns text
language sql
immutable
as $$
  select 'P45D_V1'::text;
$$;

revoke all on function child_evidence_mapping_ruleset_version_v01()
  from public,anon,authenticated;
grant execute on function child_evidence_mapping_ruleset_version_v01()
  to service_role;

alter table child_evidence_mapping_runs
  alter column rule_version
  set default child_evidence_mapping_ruleset_version_v01();

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
  v_ruleset_version text;
begin
  v_ruleset_version := child_evidence_mapping_ruleset_version_v01();

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
    'rule_version',v_ruleset_version,
    'ruleset_version',v_ruleset_version,
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

comment on function child_evidence_mapping_ruleset_version_v01() is
'Current effective child-evidence mapping ruleset version. P4.5D centralizes audit versioning here.';
