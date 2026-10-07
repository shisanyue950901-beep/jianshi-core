-- P4.1.2 scheduled Stack Exchange shadow demand collection.

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

select cron.schedule(
  'jianshi-stackexchange-signals-6h',
  '37 */6 * * *',
  $cron$
  select net.http_post(
    url := (select decrypted_secret from vault.decrypted_secrets where name='jianshi_project_url')
           || '/functions/v1/collect-stackexchange-signals',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'apikey',(select decrypted_secret from vault.decrypted_secrets where name='jianshi_publishable_key'),
      'Authorization','Bearer ' || (select decrypted_secret from vault.decrypted_secrets where name='jianshi_publishable_key')
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 30000
  );
  $cron$
);
