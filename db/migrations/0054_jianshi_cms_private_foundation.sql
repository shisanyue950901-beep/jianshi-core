-- JIANSHI F2.1 / G1-C: staging-only CMS foundation.
-- PRIVATE SCHEMA, NOT AN API, NO PUBLIC ACCESS, NO USER SUBMISSIONS.
-- Promotion to production must be separately approved after Auth E2E.
-- Do not expose jianshi_cms in PostgREST or Supabase API schemas.
create schema if not exists jianshi_cms;
revoke all on schema jianshi_cms from PUBLIC, anon, authenticated;
grant usage on schema jianshi_cms to service_role;

create table if not exists jianshi_cms.content_items (
  id uuid primary key default gen_random_uuid(),
  content_key text not null unique check (char_length(content_key) between 6 and 100),
  content_type text not null check (content_type in
    ('PROJECT_RESEARCH','SOLUTION_GUIDE','COURSE','LESSON','RESOURCE','EVENT','CASE_STUDY')),
  owner_user_id uuid not null references auth.users(id) on delete restrict,
  current_revision integer not null default 1 check (current_revision >= 1),
  workflow_state text not null default 'DRAFT' check (workflow_state in
    ('DRAFT','IN_REVIEW','APPROVED','REJECTED','PUBLISHED','UNPUBLISHED','ARCHIVED')),
  last_reviewer_id uuid references auth.users(id) on delete set null,
  published_at timestamptz,
  last_edit_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  check (last_reviewer_id is null or last_reviewer_id <> owner_user_id)
);

-- Append-only authored versions. Private JSON may contain unreleased text.
-- The service layer must use compare-and-swap current_revision in one transaction.
create table if not exists jianshi_cms.content_revisions (
  id bigint generated always as identity primary key,
  item_id uuid not null references jianshi_cms.content_items(id) on delete restrict,
  revision integer not null check (revision >= 1),
  author_user_id uuid not null references auth.users(id) on delete restrict,
  content_private jsonb not null check (jsonb_typeof(content_private) = 'object'),
  source_evidence_private jsonb not null default '[]'::jsonb
    check (jsonb_typeof(source_evidence_private) = 'array'),
  rights_declared boolean not null default false,
  facts_checked boolean not null default false,
  created_at timestamptz not null default now(),
  unique (item_id, revision)
);

-- Media identity and rights, not public storage paths or signed playback URLs.
create table if not exists jianshi_cms.media_rights (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references jianshi_cms.content_items(id) on delete restrict,
  private_asset_key text not null check (char_length(private_asset_key) between 5 and 320),
  media_kind text not null check (media_kind in ('IMAGE','VIDEO','AUDIO','DOCUMENT')),
  rights_owner_private text not null check (char_length(rights_owner_private) between 2 and 160),
  license_basis text not null default 'UNVERIFIED'
    check (license_basis in ('UNVERIFIED','OWNED','LICENSED')),
  usage_consent boolean not null default false,
  security_scan_state text not null default 'PENDING'
    check (security_scan_state in ('PENDING','PASSED','FAILED')),
  checked_by uuid references auth.users(id) on delete set null,
  checked_at timestamptz,
  created_at timestamptz not null default now(),
  unique (item_id, private_asset_key),
  check (license_basis = 'UNVERIFIED' or checked_by is not null)
);

-- Immutable audit history by privileges; no normal update/delete grants.
create table if not exists jianshi_cms.review_events (
  id bigint generated always as identity primary key,
  item_id uuid not null references jianshi_cms.content_items(id) on delete restrict,
  revision integer not null check (revision >= 1),
  from_state text not null,
  to_state text not null,
  actor_user_id uuid not null references auth.users(id) on delete restrict,
  actor_action text not null check (actor_action in
    ('SUBMIT','APPROVE','REJECT','PUBLISH','RETRACT','ARCHIVE','RESTORE')),
  reason_private text check (reason_private is null or char_length(reason_private) <= 1800),
  request_id uuid not null,
  created_at timestamptz not null default now(),
  unique(item_id, request_id)
);

-- Staging artefact ONLY. Never expose table or copy raw JSON into /web/dist/.
-- External publication will require an independently reviewed projection.
create table if not exists jianshi_cms.publication_snapshots (
  id bigint generated always as identity primary key,
  item_id uuid not null references jianshi_cms.content_items(id) on delete restrict,
  revision integer not null check (revision >= 1),
  public_allowlist_json jsonb not null check (jsonb_typeof(public_allowlist_json) = 'object'),
  source_verified boolean not null check (source_verified = true),
  rights_verified boolean not null check (rights_verified = true),
  review_event_id bigint not null references jianshi_cms.review_events(id) on delete restrict,
  lifecycle text not null default 'STAGED' check (lifecycle in ('STAGED','RETRACTED')),
  created_at timestamptz not null default now(),
  unique(item_id, revision)
);

create index if not exists idx_cms_owner on jianshi_cms.content_items(owner_user_id,workflow_state);
create index if not exists idx_cms_review_queue on jianshi_cms.content_items(workflow_state,last_edit_at desc);
create index if not exists idx_cms_versions on jianshi_cms.content_revisions(item_id,revision desc);
create index if not exists idx_cms_media_item on jianshi_cms.media_rights(item_id,license_basis);
create index if not exists idx_cms_audit_entity on jianshi_cms.review_events(item_id,created_at desc);
create index if not exists idx_cms_publication on jianshi_cms.publication_snapshots(item_id,lifecycle);

alter table jianshi_cms.content_items enable row level security;
alter table jianshi_cms.content_items force row level security;
alter table jianshi_cms.content_revisions enable row level security;
alter table jianshi_cms.content_revisions force row level security;
alter table jianshi_cms.media_rights enable row level security;
alter table jianshi_cms.media_rights force row level security;
alter table jianshi_cms.review_events enable row level security;
alter table jianshi_cms.review_events force row level security;
alter table jianshi_cms.publication_snapshots enable row level security;
alter table jianshi_cms.publication_snapshots force row level security;

-- No RLS policies for browser roles, no public EXECUTE functions.
revoke all on all tables in schema jianshi_cms from PUBLIC, anon, authenticated;
revoke all on all sequences in schema jianshi_cms from PUBLIC, anon, authenticated;
grant select, insert, update on jianshi_cms.content_items to service_role;
grant select, insert on jianshi_cms.content_revisions to service_role;
grant select, insert, update on jianshi_cms.media_rights to service_role;
grant select, insert on jianshi_cms.review_events to service_role;
grant select, insert, update on jianshi_cms.publication_snapshots to service_role;
grant usage, select on all sequences in schema jianshi_cms to service_role;

comment on schema jianshi_cms is
  'Private F2.1 G1-C staging editorial foundation. Not API exposed; closed until Auth E2E.';
comment on table jianshi_cms.publication_snapshots is
  'Internal staged projection, NOT permission to publish. Release remains gated separately.';

-- Do not activate CMS authentication or public content submissions.
insert into public.product_feature_flags(feature_key,enabled,reason)
values ('cms_editor',false,'F2.1 G1-C staging schema only; Auth E2E and API unauthorized')
on conflict(feature_key) do update set enabled=false,
 reason='F2.1 G1-C staging schema only; Auth E2E and API unauthorized',
 updated_at=now();
