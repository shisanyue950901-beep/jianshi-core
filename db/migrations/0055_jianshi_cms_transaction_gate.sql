-- F2.1 G1-D / staging ONLY. Private, transactional CMS kernel.
-- No HTTP endpoint, no browser grants, no production publication.
-- All write functions fail closed unless BOTH CMS+Auth and all Auth E2E gates pass.
-- The future trusted server must verify JWT/session and never accept role/user IDs
-- directly from a browser; service_role keys must remain server-only.
create table if not exists jianshi_cms.editor_grants (
  actor_user_id uuid primary key references auth.users(id) on delete cascade,
  permission text not null check (permission in ('EDITOR','REVIEWER','PUBLISHER','ADMIN')),
  active boolean not null default false,
  granted_at timestamptz not null default now()
);
alter table jianshi_cms.editor_grants enable row level security;
alter table jianshi_cms.editor_grants force row level security;
revoke all on jianshi_cms.editor_grants from PUBLIC, anon, authenticated;
grant select, insert, update on jianshi_cms.editor_grants to service_role;

-- A constrained append-only audit log; existing review events gain an EDIT verb.
alter table jianshi_cms.review_events
  drop constraint if exists review_events_actor_action_check;
alter table jianshi_cms.review_events
  add constraint review_events_actor_action_check check
  (actor_action in ('CREATE','EDIT','SUBMIT','APPROVE','REJECT','PUBLISH',
                    'RETRACT','ARCHIVE','RESTORE'));

create or replace function jianshi_cms.ensure_write_gate(
  p_actor uuid,
  p_needed text[]
) returns text
language plpgsql security invoker
set search_path = ''
as $$
declare
  v_role text;
begin
  if not (
    coalesce((select enabled from public.product_feature_flags where feature_key='cms_editor'),false)
    and coalesce((select enabled from public.product_feature_flags where feature_key='account_auth'),false)
    and public.auth_launch_ready_v01()
  ) then
    raise exception 'CMS_WRITE_DISABLED' using errcode='42501';
  end if;
  if current_user <> 'service_role' then
    raise exception 'CMS_TRUSTED_SERVER_ONLY' using errcode='42501';
  end if;
  if p_actor is null or p_needed is null or array_length(p_needed,1) is null then
    raise exception 'CMS_PERMISSION_DENIED' using errcode='42501';
  end if;
  select permission into v_role
    from jianshi_cms.editor_grants
    where actor_user_id=p_actor and active=true;
  if v_role is null or not (v_role=any(p_needed) or v_role='ADMIN') then
    raise exception 'CMS_PERMISSION_DENIED' using errcode='42501';
  end if;
  return v_role;
end;
$$;

create or replace function jianshi_cms.create_draft(
  p_actor uuid,
  p_content_key text,
  p_content_type text,
  p_private_content jsonb,
  p_sources_private jsonb,
  p_request_id uuid
) returns uuid
language plpgsql security invoker
set search_path=''
as $$
declare
  v_id uuid;
begin
  perform jianshi_cms.ensure_write_gate(p_actor,array['EDITOR']);
  if p_request_id is null or p_content_key is null
    or length(p_content_key) not between 6 and 100
    or p_private_content is null or jsonb_typeof(p_private_content)<>'object'
    or p_sources_private is null or jsonb_typeof(p_sources_private)<>'array'
    or length(p_private_content::text)>30000 then
    raise exception 'CMS_INVALID_DRAFT' using errcode='22023';
  end if;
  insert into jianshi_cms.content_items
     (content_key,content_type,owner_user_id,current_revision,workflow_state)
    values(p_content_key,p_content_type,p_actor,1,'DRAFT')
    returning id into v_id;
  insert into jianshi_cms.content_revisions
     (item_id,revision,author_user_id,content_private,source_evidence_private)
    values(v_id,1,p_actor,p_private_content,p_sources_private);
  insert into jianshi_cms.review_events
     (item_id,revision,from_state,to_state,actor_user_id,actor_action,request_id)
    values(v_id,1,'NONE','DRAFT',p_actor,'CREATE',p_request_id);
  return v_id;
end;
$$;

create or replace function jianshi_cms.edit_draft(
  p_actor uuid,
  p_item_id uuid,
  p_expected_revision integer,
  p_private_content jsonb,
  p_sources_private jsonb,
  p_rights_declared boolean,
  p_facts_checked boolean,
  p_request_id uuid
) returns integer
language plpgsql security invoker
set search_path=''
as $$
declare
  v_item jianshi_cms.content_items%rowtype;
  v_new integer;
begin
  perform jianshi_cms.ensure_write_gate(p_actor,array['EDITOR']);
  if p_item_id is null or p_expected_revision is null
    or p_request_id is null or p_private_content is null
    or jsonb_typeof(p_private_content)<>'object'
    or p_sources_private is null or jsonb_typeof(p_sources_private)<>'array'
    or p_rights_declared is null or p_facts_checked is null
    or length(p_private_content::text)>30000 then
    raise exception 'CMS_INVALID_EDIT' using errcode='22023';
  end if;
  select * into v_item from jianshi_cms.content_items
    where id=p_item_id for update;
  if not found or v_item.owner_user_id<>p_actor then
    raise exception 'CMS_OWNER_DENIED' using errcode='42501';
  end if;
  if v_item.workflow_state<>'DRAFT' then
    raise exception 'CMS_DRAFT_LOCKED' using errcode='22023';
  end if;
  if v_item.current_revision<>p_expected_revision then
    raise exception 'CMS_STALE_REVISION' using errcode='40001';
  end if;
  v_new:=v_item.current_revision+1;
  insert into jianshi_cms.content_revisions
    (item_id,revision,author_user_id,content_private,source_evidence_private,
     rights_declared,facts_checked)
    values(p_item_id,v_new,p_actor,p_private_content,p_sources_private,
           p_rights_declared,p_facts_checked);
  update jianshi_cms.content_items
    set current_revision=v_new,last_edit_at=now()
    where id=p_item_id;
  insert into jianshi_cms.review_events
    (item_id,revision,from_state,to_state,actor_user_id,actor_action,request_id)
    values(p_item_id,v_new,'DRAFT','DRAFT',p_actor,'EDIT',p_request_id);
  return v_new;
end;
$$;

-- No new users or test drafts are seeded. The function reads the current
-- immutable revision, row-locks the item, and commits state+audit+projection
-- together or rolls the entire transaction back.
create or replace function jianshi_cms.change_review_state(
  p_actor uuid,
  p_item_id uuid,
  p_expected_revision integer,
  p_to_state text,
  p_request_id uuid,
  p_reason text default null
) returns integer
language plpgsql security invoker
set search_path=''
as $$
declare
  v_item jianshi_cms.content_items%rowtype;
  v_rev jianshi_cms.content_revisions%rowtype;
  v_role text;
  v_action text;
  v_new integer;
  v_event bigint;
  v_src jsonb;
  v_safe_sources jsonb:='[]'::jsonb;
  v_published jsonb;
begin
  -- Feature gate is checked first even for unidentified callers.
  perform jianshi_cms.ensure_write_gate(p_actor,array['EDITOR','REVIEWER','PUBLISHER']);
  if p_actor is null or p_item_id is null or p_expected_revision is null
    or p_to_state is null or p_request_id is null
    or p_reason is not null and length(p_reason)>1800 then
    raise exception 'CMS_INVALID_TRANSITION' using errcode='22023';
  end if;
  select permission into v_role from jianshi_cms.editor_grants
    where actor_user_id=p_actor and active;
  select * into v_item from jianshi_cms.content_items
    where id=p_item_id for update;
  if not found then
    raise exception 'CMS_NOT_FOUND' using errcode='22023';
  end if;
  if v_item.current_revision<>p_expected_revision then
    raise exception 'CMS_STALE_REVISION' using errcode='40001';
  end if;

  if v_item.workflow_state='DRAFT' and p_to_state='IN_REVIEW'
    or v_item.workflow_state='REJECTED' and p_to_state='DRAFT'
    or v_item.workflow_state='UNPUBLISHED' and p_to_state='IN_REVIEW' then
    if p_actor<>v_item.owner_user_id or v_role not in ('EDITOR','ADMIN') then
      raise exception 'CMS_OWNER_DENIED' using errcode='42501';
    end if;
    v_action:=case when p_to_state='DRAFT' then 'RESTORE' else 'SUBMIT' end;
  elsif v_item.workflow_state='IN_REVIEW' and p_to_state in ('APPROVED','REJECTED') then
    if v_role not in ('REVIEWER','ADMIN') or p_actor=v_item.owner_user_id then
      raise exception 'CMS_INDEPENDENT_REVIEW_REQUIRED' using errcode='42501';
    end if;
    v_action:=case when p_to_state='APPROVED' then 'APPROVE' else 'REJECT' end;
  elsif v_item.workflow_state='APPROVED' and p_to_state='PUBLISHED'
    or v_item.workflow_state='PUBLISHED' and p_to_state='UNPUBLISHED' then
    if v_role not in ('PUBLISHER','ADMIN') or p_actor=v_item.owner_user_id then
      raise exception 'CMS_PUBLISHER_DENIED' using errcode='42501';
    end if;
    v_action:=case when p_to_state='PUBLISHED' then 'PUBLISH' else 'RETRACT' end;
  else
    raise exception 'CMS_ILLEGAL_TRANSITION' using errcode='22023';
  end if;

  select * into v_rev from jianshi_cms.content_revisions
    where item_id=p_item_id and revision=v_item.current_revision;
  if not found then
    raise exception 'CMS_REVISION_MISSING' using errcode='22023';
  end if;

  if p_to_state in ('APPROVED','PUBLISHED') then
    if not v_rev.rights_declared or not v_rev.facts_checked
      or v_rev.source_evidence_private='[]'::jsonb then
      raise exception 'CMS_EVIDENCE_OR_RIGHTS_MISSING' using errcode='22023';
    end if;
    if exists(select 1 from jianshi_cms.media_rights m
       where m.item_id=p_item_id and
       (m.license_basis='UNVERIFIED' or not m.usage_consent
        or m.security_scan_state<>'PASSED' or m.checked_by is null)) then
      raise exception 'CMS_MEDIA_RIGHTS_NOT_READY' using errcode='22023';
    end if;
  end if;

  -- Public projection allowlist constructed inside the transaction.
  if p_to_state='PUBLISHED' then
    if jsonb_typeof(v_rev.content_private->'source_refs') <> 'array'
      or jsonb_array_length(v_rev.content_private->'source_refs')=0
      or jsonb_typeof(v_rev.content_private->'tags') <> 'array'
      or length(coalesce(v_rev.content_private->>'title',''))<2
      or length(coalesce(v_rev.content_private->>'summary',''))<8 then
      raise exception 'CMS_INVALID_PUBLIC_PROJECTION' using errcode='22023';
    end if;
    for v_src in select value from jsonb_array_elements(v_rev.content_private->'source_refs') loop
      if jsonb_typeof(v_src)<>'object' then
        raise exception 'CMS_SOURCE_UNSAFE' using errcode='22023';
      end if;
      if v_src->>'kind'='PUBLIC_URL' then
        if (v_src - 'kind' - 'url')<>'{}'::jsonb
          or coalesce(v_src->>'url','') !~ '^https://[a-zA-Z0-9.-]+(/[^?#[:space:]@]*)?$'
          or length(v_src->>'url')>1000 then
          raise exception 'CMS_SOURCE_UNSAFE' using errcode='22023';
        end if;
        v_safe_sources:=v_safe_sources||jsonb_build_array(
          jsonb_build_object('kind','PUBLIC_URL','url',v_src->>'url'));
      elsif v_src->>'kind'='AUTHOR_ORIGINAL' then
        if (v_src - 'kind' - 'description')<>'{}'::jsonb
          or length(coalesce(v_src->>'description','')) not between 1 and 300 then
          raise exception 'CMS_SOURCE_UNSAFE' using errcode='22023';
        end if;
        v_safe_sources:=v_safe_sources||jsonb_build_array(
          jsonb_build_object('kind','AUTHOR_ORIGINAL','description',v_src->>'description'));
      else
        raise exception 'CMS_SOURCE_UNSAFE' using errcode='22023';
      end if;
    end loop;
    v_published:=jsonb_build_object(
      'content_id',v_item.content_key,
      'content_type',v_item.content_type,
      'title',v_rev.content_private->>'title',
      'summary',v_rev.content_private->>'summary',
      'category',v_rev.content_private->>'category',
      'tags',v_rev.content_private->'tags',
      'language',v_rev.content_private->>'language',
      'source_refs',v_safe_sources,
      'source_verified_at',v_rev.content_private->>'source_verified_at',
      'revision',v_item.current_revision+1,
      'published_at',to_char(current_date,'YYYY-MM-DD')
    );
  end if;

  v_new:=v_item.current_revision+1;
  insert into jianshi_cms.content_revisions
    (item_id,revision,author_user_id,content_private,source_evidence_private,
     rights_declared,facts_checked)
    values(p_item_id,v_new,v_rev.author_user_id,v_rev.content_private,
           v_rev.source_evidence_private,v_rev.rights_declared,v_rev.facts_checked);
  update jianshi_cms.content_items
    set current_revision=v_new, workflow_state=p_to_state, last_edit_at=now(),
      last_reviewer_id=case when p_to_state in ('APPROVED','REJECTED') then p_actor
        when p_to_state='IN_REVIEW' then null else last_reviewer_id end,
      published_at=case when p_to_state='PUBLISHED' then now() else published_at end
    where id=p_item_id;
  insert into jianshi_cms.review_events
    (item_id,revision,from_state,to_state,actor_user_id,actor_action,
     reason_private,request_id)
    values(p_item_id,v_new,v_item.workflow_state,p_to_state,p_actor,v_action,
           p_reason,p_request_id)
    returning id into v_event;

  if p_to_state='PUBLISHED' then
    insert into jianshi_cms.publication_snapshots
      (item_id,revision,public_allowlist_json,source_verified,rights_verified,
       review_event_id,lifecycle)
      values(p_item_id,v_new,v_published,true,true,v_event,'STAGED');
  elsif p_to_state='UNPUBLISHED' then
    update jianshi_cms.publication_snapshots
      set lifecycle='RETRACTED' where item_id=p_item_id and lifecycle='STAGED';
  end if;
  return v_new;
end;
$$;

-- Never callable by anon, authenticated, PUBLIC, or Data API public schema.
revoke all on function jianshi_cms.ensure_write_gate(uuid,text[]) from PUBLIC,anon,authenticated;
revoke all on function jianshi_cms.create_draft(uuid,text,text,jsonb,jsonb,uuid) from PUBLIC,anon,authenticated;
revoke all on function jianshi_cms.edit_draft(uuid,uuid,integer,jsonb,jsonb,boolean,boolean,uuid) from PUBLIC,anon,authenticated;
revoke all on function jianshi_cms.change_review_state(uuid,uuid,integer,text,uuid,text) from PUBLIC,anon,authenticated;
grant execute on function jianshi_cms.ensure_write_gate(uuid,text[]) to service_role;
grant execute on function jianshi_cms.create_draft(uuid,text,text,jsonb,jsonb,uuid) to service_role;
grant execute on function jianshi_cms.edit_draft(uuid,uuid,integer,jsonb,jsonb,boolean,boolean,uuid) to service_role;
grant execute on function jianshi_cms.change_review_state(uuid,uuid,integer,text,uuid,text) to service_role;

comment on function jianshi_cms.change_review_state(uuid,uuid,integer,text,uuid,text)
is 'Private staging transaction: CMS+Auth gate, role, owner, revision, rights, audit and staged public allowlist. Not an exposed endpoint.';
