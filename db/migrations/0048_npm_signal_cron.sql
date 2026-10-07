-- P4.1 npm signal collector schedule.
-- Internal collector is JWT-protected and invoked with the project's
-- publishable key, consistent with existing internal scheduled Edge calls.

do $$
declare
  existing_job bigint;
begin
  select jobid into existing_job
  from cron.job
  where jobname='jianshi-npm-signals-6h'
  limit 1;

  if existing_job is not null then
    perform cron.unschedule(existing_job);
  end if;
end;
$$;

select cron.schedule(
  'jianshi-npm-signals-6h',
  '27 */6 * * *',
  $cron$
  select net.http_post(
    url := (select decrypted_secret from vault.decrypted_secrets where name='jianshi_project_url')
           || '/functions/v1/collect-npm-signals',
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
