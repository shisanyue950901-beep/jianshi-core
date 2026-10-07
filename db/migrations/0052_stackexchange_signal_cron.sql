-- P4.1.2 Stack Exchange product-value hold.
-- Legal/source-policy status remains GREEN, but the observed recent signal
-- density is too low to justify scheduled production collection.
-- This migration explicitly disables collection and removes any schedule.

do $$
declare
  existing_job bigint;
begin
  select jobid into existing_job
  from cron.job
  where jobname='jianshi-stackexchange-signals-6h'
  limit 1;

  if existing_job is not null then
    perform cron.unschedule(existing_job);
  end if;
end;
$$;

update data_sources
set
  auto_collect=false,
  rate_limit_note='P4.1.2 HOLD_LOW_SIGNAL: official API is allowed, but recent opportunity-relevant tag density is too low for scheduled collection.',
  updated_at=now()
where code='stack_exchange';

update external_signal_queries q
set
  enabled=false,
  notes=concat_ws(' | ',nullif(q.notes,''),'P4.1.2 HOLD_LOW_SIGNAL after real Staging density check'),
  updated_at=now()
from data_sources ds
where q.source_id=ds.id
  and ds.code='stack_exchange'
  and q.query_type='STACKEXCHANGE_TAG_COUNT';

comment on table external_signal_queries is
'Generic external signal query registry. Stack Exchange query definitions are retained but disabled after P4.1.2 real-data density validation.';
