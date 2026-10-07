-- P3.2 China entrepreneur interpretation layer.
-- Validation-stage only. No user profiles or personal data.

create table if not exists opportunity_china_interpretations (
  opportunity_id uuid primary key references opportunities(id) on delete cascade,
  audience text not null default 'CHINA_INDIVIDUAL_ENTREPRENEUR'
    check (audience='CHINA_INDIVIDUAL_ENTREPRENEUR'),
  recommended_market text not null default 'UNKNOWN'
    check (recommended_market in ('CHINA','GLOBAL','BOTH','UNKNOWN')),
  opportunity_translation text,
  why_it_matters_for_china_founder text,
  domestic_execution_path text,
  global_execution_path text,
  capital_intensity text not null default 'UNKNOWN'
    check (capital_intensity in ('LOW','MEDIUM','HIGH','UNKNOWN')),
  mvp_complexity text not null default 'UNKNOWN'
    check (mvp_complexity in ('LOW','MEDIUM','HIGH','UNKNOWN')),
  acquisition_difficulty text not null default 'UNKNOWN'
    check (acquisition_difficulty in ('LOW','MEDIUM','HIGH','UNKNOWN')),
  localization_needs jsonb not null default '[]'::jsonb,
  execution_steps jsonb not null default '[]'::jsonb,
  risk_notes jsonb not null default '[]'::jsonb,
  evidence_refs jsonb not null default '[]'::jsonb,
  confidence text not null default 'LOW'
    check (confidence in ('LOW','MEDIUM','HIGH')),
  review_status text not null default 'DRAFT'
    check (review_status in ('DRAFT','REVIEWED','PUBLISHED')),
  reviewed_at timestamptz,
  updated_at timestamptz not null default now()
);

alter table opportunity_china_interpretations enable row level security;
revoke all on opportunity_china_interpretations from public,anon,authenticated;
grant select,insert,update on opportunity_china_interpretations to service_role;

create or replace view opportunity_china_interpretation_shadow_v01
with (security_invoker=true)
as
select
  o.id as opportunity_id,
  o.slug,
  o.title,
  o.china_fit,
  o.solo_founder_fit,
  i.audience,
  i.recommended_market,
  i.opportunity_translation,
  i.why_it_matters_for_china_founder,
  i.domestic_execution_path,
  i.global_execution_path,
  i.capital_intensity,
  i.mvp_complexity,
  i.acquisition_difficulty,
  i.localization_needs,
  i.execution_steps,
  i.risk_notes,
  i.evidence_refs,
  i.confidence,
  i.review_status,
  i.reviewed_at,
  i.updated_at
from opportunities o
left join opportunity_china_interpretations i on i.opportunity_id=o.id
where o.status='ACTIVE';

revoke all on opportunity_china_interpretation_shadow_v01 from public,anon,authenticated;
grant select on opportunity_china_interpretation_shadow_v01 to service_role;

create or replace view public_china_entrepreneur_interpretation_v01
with (security_invoker=true)
as
select
  o.slug,
  o.title,
  o.china_fit,
  o.solo_founder_fit,
  i.recommended_market,
  i.opportunity_translation,
  i.why_it_matters_for_china_founder,
  i.domestic_execution_path,
  i.global_execution_path,
  i.capital_intensity,
  i.mvp_complexity,
  i.acquisition_difficulty,
  i.localization_needs,
  i.execution_steps,
  i.risk_notes,
  i.confidence,
  i.reviewed_at
from opportunities o
join opportunity_china_interpretations i on i.opportunity_id=o.id
where o.status='ACTIVE'
  and i.review_status='PUBLISHED'
  and i.reviewed_at is not null;

revoke all on public_china_entrepreneur_interpretation_v01 from public,anon,authenticated;
grant select on public_china_entrepreneur_interpretation_v01 to service_role;

comment on table opportunity_china_interpretations is
'P3.2 editorial interpretation layer for Chinese individual entrepreneurs. Draft content does not affect opportunity scoring or validation.';
comment on view opportunity_china_interpretation_shadow_v01 is
'Internal validation-stage interpretation view.';
comment on view public_china_entrepreneur_interpretation_v01 is
'Fail-closed future projection; not wired to public feed in P3.2.';