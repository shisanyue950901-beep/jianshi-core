-- F2.1 G1-I: STAGING-ONLY privacy-preserving permissions audit.
-- Read-only catalog/feature-flag aggregate; no user rows, JWTs, private CMS data,
-- network source requests, or privilege changes. Run only on jianshi-staging.
WITH private_tables AS (
  SELECT n.nspname AS schema_name,
         count(*) AS table_count,
         count(*) FILTER (WHERE c.relrowsecurity AND c.relforcerowsecurity) AS force_rls_count,
         count(*) FILTER (WHERE has_table_privilege('anon',c.oid,'SELECT')
                            OR has_table_privilege('authenticated',c.oid,'SELECT')
                            OR has_table_privilege('authenticated',c.oid,'INSERT')
                            OR has_table_privilege('authenticated',c.oid,'UPDATE')
                            OR has_table_privilege('authenticated',c.oid,'DELETE')) AS untrusted_grant_count
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE c.relkind='r' AND n.nspname IN ('jianshi_cms','jianshi_v2')
   GROUP BY n.nspname
), private_policies AS (
  SELECT count(*) AS private_policy_count
  FROM pg_policies WHERE schemaname IN ('jianshi_cms','jianshi_v2')
), schema_checks AS (
  SELECT NOT has_schema_privilege('anon','jianshi_cms','USAGE')
     AND NOT has_schema_privilege('authenticated','jianshi_cms','USAGE')
     AND NOT has_schema_privilege('anon','jianshi_v2','USAGE')
     AND NOT has_schema_privilege('authenticated','jianshi_v2','USAGE') AS deny_untrusted_usage
), rpc_checks AS (
  SELECT count(*) AS count_rpcs,
         bool_and(NOT has_function_privilege('anon',p.oid,'EXECUTE')
                  AND NOT has_function_privilege('authenticated',p.oid,'EXECUTE')
                  AND has_function_privilege('service_role',p.oid,'EXECUTE')) AS deny_untrusted_rpc
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname='public'
     AND p.proname IN ('cms_internal_session_v01','cms_internal_write_v01')
), feature_checks AS (
  SELECT count(*) AS feature_count,
         bool_and(NOT enabled) AS all_three_closed
    FROM public.product_feature_flags
   WHERE feature_key IN ('account_auth','cms_editor','v2_matchmaking')
)
SELECT
  (SELECT count(*) FROM private_tables) AS schema_count,
  (SELECT sum(table_count) FROM private_tables) AS total_private_tables,
  (SELECT sum(force_rls_count) FROM private_tables) AS force_rls_tables,
  (SELECT sum(untrusted_grant_count) FROM private_tables) AS untrusted_table_grants,
  (SELECT private_policy_count FROM private_policies) AS private_policy_count,
  (SELECT deny_untrusted_usage FROM schema_checks) AS schema_usage_closed,
  (SELECT count_rpcs FROM rpc_checks) AS internal_rpc_count,
  (SELECT deny_untrusted_rpc FROM rpc_checks) AS internal_rpc_closed,
  (SELECT feature_count FROM feature_checks) AS closed_feature_count,
  (SELECT all_three_closed FROM feature_checks) AS features_closed,
  CASE WHEN
    (SELECT count(*) FROM private_tables)=2
    AND (SELECT sum(table_count) FROM private_tables)=12
    AND (SELECT sum(force_rls_count) FROM private_tables)=12
    AND (SELECT sum(untrusted_grant_count) FROM private_tables)=0
    AND (SELECT private_policy_count FROM private_policies)=0
    AND (SELECT deny_untrusted_usage FROM schema_checks)
    AND (SELECT count_rpcs FROM rpc_checks)=2
    AND (SELECT deny_untrusted_rpc FROM rpc_checks)
    AND (SELECT feature_count FROM feature_checks)=3
    AND (SELECT all_three_closed FROM feature_checks)
  THEN 'PASS_DENY_BY_DEFAULT' ELSE 'FAIL_CLOSED_REVIEW_REQUIRED' END AS verdict;
