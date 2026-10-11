-- JIANSHI 2.0 / P4.48 private matchmaking foundation (staging-first).
-- NOT A PUBLIC API. Do not expose this schema in Supabase Data API.
-- Identity/authentication V8.6 gate stays OFF. No customer submissions are accepted.
-- Run on jianshi-staging and verify privilege/RLS before considering production.

create schema if not exists jianshi_v2;
revoke all on schema jianshi_v2 from public, anon, authenticated;
grant usage on schema jianshi_v2 to service_role;

create table if not exists jianshi_v2.organizations (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null references auth.users(id) on delete cascade,
    display_name text not null check (char_length(display_name) between 2 and 120),
    business_category text check (business_category is null or char_length(business_category) <= 80),
    verification_status text not null default 'PENDING'
        check (verification_status in ('PENDING','VERIFIED','REJECTED','SUSPENDED')),
    verification_note_private text check (verification_note_private is null or char_length(verification_note_private) <= 2000),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists jianshi_v2.creator_profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references auth.users(id) on delete cascade,
    public_display_name text not null check (char_length(public_display_name) between 2 and 80),
    skill_summary_private text not null default '' check (char_length(skill_summary_private) <= 1500),
    review_status text not null default 'DRAFT'
        check (review_status in ('DRAFT','PENDING','APPROVED','REJECTED','SUSPENDED')),
    visibility_consent boolean not null default false,
    reviewed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists jianshi_v2.portfolio_items (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references jianshi_v2.creator_profiles(id) on delete cascade,
    title text not null check (char_length(title) between 2 and 120),
    work_summary_private text not null check (char_length(work_summary_private) between 10 and 3000),
    work_kind text not null default 'PRACTICE'
        check (work_kind in ('PRACTICE','PERSONAL','CLIENT_AUTHORIZED')),
    rights_confirmed boolean not null default false,
    review_status text not null default 'DRAFT'
        check (review_status in ('DRAFT','PENDING','APPROVED','REJECTED')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists jianshi_v2.service_requests (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid not null references jianshi_v2.organizations(id) on delete cascade,
    created_by uuid not null references auth.users(id) on delete cascade,
    title text not null check (char_length(title) between 5 and 140),
    category text not null check (char_length(category) between 2 and 80),
    brief_private text not null check (char_length(brief_private) between 20 and 6000),
    approved_public_summary text check (approved_public_summary is null or char_length(approved_public_summary) <= 1500),
    delivery_notes_private text check (delivery_notes_private is null or char_length(delivery_notes_private) <= 2000),
    rights_confirmed boolean not null default false,
    review_status text not null default 'DRAFT'
        check (review_status in ('DRAFT','PENDING','APPROVED','REJECTED','SUSPENDED')),
    publication_status text not null default 'PRIVATE'
        check (publication_status in ('PRIVATE','PUBLISHED','CLOSED')),
    published_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint service_request_publication_guard
        check (publication_status <> 'PUBLISHED'
               or (review_status = 'APPROVED'
                   and rights_confirmed = true
                   and approved_public_summary is not null
                   and char_length(approved_public_summary) >= 20))
);

create table if not exists jianshi_v2.request_applications (
    id uuid primary key default gen_random_uuid(),
    request_id uuid not null references jianshi_v2.service_requests(id) on delete cascade,
    creator_user_id uuid not null references auth.users(id) on delete cascade,
    pitch_private text not null check (char_length(pitch_private) between 20 and 2500),
    application_status text not null default 'PENDING'
        check (application_status in ('PENDING','SHORTLISTED','DECLINED','WITHDRAWN','ACCEPTED')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(request_id,creator_user_id)
);

create table if not exists jianshi_v2.moderation_events (
    id bigint generated always as identity primary key,
    reviewed_by uuid references auth.users(id) on delete set null,
    entity_kind text not null check (entity_kind in ('ORGANIZATION','CREATOR','WORK','REQUEST','APPLICATION')),
    entity_id uuid not null,
    action_code text not null check (action_code in ('APPROVE','REJECT','SUSPEND','RESTORE','CLOSE')),
    private_reason text not null check (char_length(private_reason) between 3 and 1500),
    created_at timestamptz not null default now()
);

create index if not exists idx_v2_org_owner on jianshi_v2.organizations(owner_user_id);
create index if not exists idx_v2_work_profile on jianshi_v2.portfolio_items(profile_id,created_at desc);
create index if not exists idx_v2_requests_org on jianshi_v2.service_requests(organization_id,created_at desc);
create index if not exists idx_v2_requests_review on jianshi_v2.service_requests(review_status,publication_status);
create index if not exists idx_v2_applications_creator on jianshi_v2.request_applications(creator_user_id,created_at desc);
create index if not exists idx_v2_events_entity on jianshi_v2.moderation_events(entity_kind,entity_id,created_at desc);

-- Defense in depth: RLS + FORCE RLS everywhere; NO end-user policies yet.
-- Even authenticated users must not access an enterprise's unreviewed demand.
alter table jianshi_v2.organizations enable row level security;
alter table jianshi_v2.organizations force row level security;
alter table jianshi_v2.creator_profiles enable row level security;
alter table jianshi_v2.creator_profiles force row level security;
alter table jianshi_v2.portfolio_items enable row level security;
alter table jianshi_v2.portfolio_items force row level security;
alter table jianshi_v2.service_requests enable row level security;
alter table jianshi_v2.service_requests force row level security;
alter table jianshi_v2.request_applications enable row level security;
alter table jianshi_v2.request_applications force row level security;
alter table jianshi_v2.moderation_events enable row level security;
alter table jianshi_v2.moderation_events force row level security;

revoke all on all tables in schema jianshi_v2 from public, anon, authenticated;
revoke all on all sequences in schema jianshi_v2 from public, anon, authenticated;
grant select, insert, update, delete on all tables in schema jianshi_v2 to service_role;
grant usage, select on all sequences in schema jianshi_v2 to service_role;

-- Staging-only schema is deliberately not wired to any Edge Function or
-- browser. A separately reviewed backend will enforce identity ownership,
-- verified enterprise members, rate limits, moderation, and audit transitions.
comment on schema jianshi_v2 is
    'Private, non-Data-API JIANSHI V2 staging matchmaking foundation; locked before Auth E2E gates.';
comment on table jianshi_v2.service_requests is
    'Private company requirements. Never render brief_private; publication requires approved_public_summary.';
comment on table jianshi_v2.request_applications is
    'Confidential creator applications. Not accessible through public site or anonymous client.';

-- The switch stays OFF even if this migration is applied to another environment.
insert into public.product_feature_flags(feature_key,enabled,reason)
values ('v2_matchmaking',false,'P4.48 staged private schema only; Auth launch and E2E not accepted')
on conflict(feature_key) do update set enabled=false,
    reason='P4.48 staged private schema only; Auth launch and E2E not accepted',
    updated_at=now();
