-- F2.1 G2-E / STAGING ONLY. Additive, private, fail-closed restoration contract.
-- This is NOT published CMS. Requires pre-existing account_auth, cms_editor,
-- all eight Auth launch gates and a trusted service_role caller.
-- Do not deploy to production without separate authorization.
--
-- Restoring OLD CONTENT is NOT undoing a PUBLISHED snapshot:
-- only DRAFT/REJECTED; append new revision; clear rights/facts attestations;
-- explicitly re-edit, re-submit, independently review and publish later.
create or replace function jianshi_cms.restore_draft_revision(
  p_actor uuid,
  p_item_id uuid,
  p_expected_revision integer,
  p_source_revision integer,
  p_request_id uuid
) returns integer
language plpgsql security invoker
set search_path = ''
as $$
declare
  v_item jianshi_cms.content_items%rowtype;
  v_source jianshi_cms.content_revisions%rowtype;
  v_new integer;
begin
  -- Always check the production-safe feature gate before reading any private row.
  perform jianshi_cms.ensure_write_gate(p_actor, array['EDITOR']);
  if p_actor is null or p_item_id is null or p_request_id is null
     or p_expected_revision is null or p_expected_revision < 1
     or p_source_revision is null or p_source_revision < 1 then
    raise exception 'CMS_INVALID_RESTORE' using errcode='22023';
  end if;

  select * into v_item from jianshi_cms.content_items
    where id = p_item_id for update;
  if not found or v_item.owner_user_id <> p_actor then
    raise exception 'CMS_OWNER_DENIED' using errcode='42501';
  end if;
  if v_item.workflow_state not in ('DRAFT','REJECTED') then
    raise exception 'CMS_RESTORE_REQUIRES_DRAFT' using errcode='22023';
  end if;
  if v_item.current_revision <> p_expected_revision then
    raise exception 'CMS_STALE_REVISION' using errcode='40001';
  end if;
  if p_source_revision >= v_item.current_revision then
    raise exception 'CMS_INVALID_SOURCE_REVISION' using errcode='22023';
  end if;
  if exists (
    select 1 from jianshi_cms.review_events
      where item_id = p_item_id and request_id = p_request_id
  ) then
    raise exception 'CMS_DUPLICATE_REQUEST' using errcode='23505';
  end if;
  -- Defense in depth: an active public projection must never coexist with
  -- a private historical restore. Retraction requires a separate transition.
  if exists (
    select 1 from jianshi_cms.publication_snapshots
      where item_id = p_item_id and lifecycle = 'STAGED'
  ) then
    raise exception 'CMS_ACTIVE_PUBLICATION_BLOCKS_RESTORE' using errcode='42501';
  end if;
  select * into v_source from jianshi_cms.content_revisions
    where item_id = p_item_id and revision = p_source_revision;
  if not found then
    raise exception 'CMS_SOURCE_REVISION_NOT_FOUND' using errcode='22023';
  end if;

  v_new := v_item.current_revision + 1;
  -- The historical revision is immutable. Source references are private and
  -- copied verbatim only into a new private draft. Provenance is re-attested
  -- through the existing edit_draft path before an approval is possible.
  insert into jianshi_cms.content_revisions
    (item_id, revision, author_user_id, content_private,
     source_evidence_private, rights_declared, facts_checked)
    values (p_item_id, v_new, p_actor,
            v_source.content_private, v_source.source_evidence_private,
            false, false);

  update jianshi_cms.content_items
    set current_revision = v_new, workflow_state = 'DRAFT',
        last_reviewer_id = null, published_at = null, last_edit_at = now()
    where id = p_item_id and current_revision = p_expected_revision;
  if not found then
    raise exception 'CMS_STALE_REVISION' using errcode='40001';
  end if;
  insert into jianshi_cms.review_events
    (item_id, revision, from_state, to_state, actor_user_id,
     actor_action, reason_private, request_id)
    values (p_item_id, v_new, v_item.workflow_state, 'DRAFT',
            p_actor, 'RESTORE', 'HISTORICAL_REVISION_REQUIRES_FRESH_REVIEW',
            p_request_id);
  return v_new;
end;
$$;

revoke all on function
  jianshi_cms.restore_draft_revision(uuid,uuid,integer,integer,uuid)
  from PUBLIC, anon, authenticated;
grant execute on function
  jianshi_cms.restore_draft_revision(uuid,uuid,integer,integer,uuid)
  to service_role;
comment on function jianshi_cms.restore_draft_revision(uuid,uuid,integer,integer,uuid)
is 'STAGING ONLY: append-only historical draft restoration, fresh evidence and rights review required. service_role only, CMS/Auth gates remain closed.';
