-- P4.5C Staging-only automatic mapping trigger and audit.
-- Empire collector success may invoke this hook. Mapping failure is isolated
-- and MUST NOT convert a successful source collection into a failed collection.

create table if not exists child_evidence_mapping_runs (
  id uuid primary key default gen_random_uuid(),
  trigger_run_id uuid not null unique references pipeline_runs(id) on delete cascade,
  trigger_source_id uuid not null references data_sources(id) on delete restrict,
  trigger_type text not null,
  status text not null check (status in ('RUNNING','SUCCESS','FAILED','SKIPPED')),
  rule_version text not null default 'P45B_V1',
  mapping_result jsonb not null default '{}'::jsonb,
  error_text text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_child_mapping_runs_source_time
  on child_evidence_mapping_runs(trigger_source_id,started_at desc);

alter table child_evidence_mapping_runs enable row level security;
revoke all on child_evidence_mapping_runs from public,anon,authenticated;
grant select,insert,update,delete on child_evidence_mapping_runs to service_role;

create or replace function run_child_evidence_mapping_hook_v01(p_trigger_run_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_run record;
  v_audit_id uuid;
  v_result jsonb;
  v_error text;
begin
  select pr.id,pr.source_id,pr.run_type,pr.status,ds.code as source_code
    into v_run
  from pipeline_runs pr
  join data_sources ds on ds.id=pr.source_id
  where pr.id=p_trigger_run_id;

  if not found then
    return jsonb_build_object(
      'ok',false,
      'status','SKIPPED',
      'reason','TRIGGER_RUN_NOT_FOUND'
    );
  end if;

  if v_run.run_type <> 'EMPIRE_FLIPPERS_COLLECTOR'
     or v_run.status <> 'SUCCESS'
     or v_run.source_code <> 'empire_flippers' then
    insert into child_evidence_mapping_runs(
      trigger_run_id,trigger_source_id,trigger_type,status,mapping_result,finished_at
    )
    values(
      v_run.id,v_run.source_id,v_run.run_type,'SKIPPED',
      jsonb_build_object(
        'reason','TRIGGER_NOT_ELIGIBLE',
        'source_code',v_run.source_code,
        'collector_status',v_run.status
      ),
      now()
    )
    on conflict(trigger_run_id) do update set
      status='SKIPPED',
      mapping_result=excluded.mapping_result,
      error_text=null,
      finished_at=now()
    returning id into v_audit_id;

    return jsonb_build_object(
      'ok',true,
      'status','SKIPPED',
      'audit_id',v_audit_id,
      'reason','TRIGGER_NOT_ELIGIBLE'
    );
  end if;

  insert into child_evidence_mapping_runs(
    trigger_run_id,trigger_source_id,trigger_type,status,started_at
  )
  values(v_run.id,v_run.source_id,v_run.run_type,'RUNNING',now())
  on conflict(trigger_run_id) do update set
    status='RUNNING',
    mapping_result='{}'::jsonb,
    error_text=null,
    started_at=now(),
    finished_at=null
  returning id into v_audit_id;

  begin
    v_result := refresh_child_marketplace_evidence_v01();

    update child_evidence_mapping_runs
    set
      status='SUCCESS',
      mapping_result=v_result,
      error_text=null,
      finished_at=now()
    where id=v_audit_id;

    return jsonb_build_object(
      'ok',true,
      'status','SUCCESS',
      'audit_id',v_audit_id,
      'mapping_result',v_result
    );
  exception when others then
    v_error := sqlstate || ':' || sqlerrm;

    update child_evidence_mapping_runs
    set
      status='FAILED',
      mapping_result=jsonb_build_object(
        'publication_changed',false,
        'scoring_changed',false
      ),
      error_text=left(v_error,2000),
      finished_at=now()
    where id=v_audit_id;

    -- Fail isolated: return FAILED as data instead of raising.
    return jsonb_build_object(
      'ok',false,
      'status','FAILED',
      'audit_id',v_audit_id,
      'error',left(v_error,500)
    );
  end;
end;
$$;

revoke all on function run_child_evidence_mapping_hook_v01(uuid)
  from public,anon,authenticated;
grant execute on function run_child_evidence_mapping_hook_v01(uuid)
  to service_role;

create or replace view child_evidence_mapping_run_audit_v01
with (security_invoker=true) as
select
  r.id,
  r.trigger_run_id,
  r.trigger_type,
  r.status,
  r.rule_version,
  r.mapping_result,
  r.error_text,
  r.started_at,
  r.finished_at,
  extract(epoch from (coalesce(r.finished_at,now())-r.started_at))::numeric(12,3) as duration_seconds
from child_evidence_mapping_runs r
order by r.started_at desc;

revoke all on child_evidence_mapping_run_audit_v01 from public,anon,authenticated;
grant select on child_evidence_mapping_run_audit_v01 to service_role;

comment on table child_evidence_mapping_runs is
'P4.5C internal audit log for collector-triggered child evidence refreshes. Mapping failure is isolated from source collector status.';
comment on function run_child_evidence_mapping_hook_v01(uuid) is
'P4.5C fail-isolated mapping hook. Eligible only for successful Empire Flippers collector runs; returns failure as data rather than raising.';
