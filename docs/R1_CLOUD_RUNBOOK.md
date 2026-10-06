# R1 Cloud Runbook

## Staging first
1. Create Supabase Free project: `jianshi-staging`.
2. Apply `0001_core.sql` then `0002_marketplace.sql`.
3. Seed source registry.
4. Test RED gate by attempting `acquire + auto_collect=true`; expected DB exception.
5. Insert one Empire Flippers fixture listing and two different snapshots.
6. Verify duplicate snapshot hash is rejected.
7. Run pg_dump backup and restore to temporary database.
8. Only after all PASS create/apply same migrations to `jianshi-prod`.

## Production safety
- Never expose service-role key in browser.
- Collector gets only required write permissions.
- Public website reads curated views, not raw_items.
- Raw source payloads remain private.
