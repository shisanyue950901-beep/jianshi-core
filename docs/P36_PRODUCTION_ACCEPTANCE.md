# P3.6 数据库生产硬化 Production 验收

日期：2026-10-07

## 结论

```
P36_CODE = PASS_MAIN
P36_PR = PASS_MERGED_41
P36_CI = PASS_RUN_111
P36_STAGING_MIGRATION = PASS
P36_STAGING_PERF_HARDENING = PASS
P36_PRODUCTION_MIGRATION = PASS
P36_PRODUCTION_PERF_HARDENING = PASS
P36_CAPACITY_MONITOR = PASS
P36_AUTH_FEATURE_FLAG = CLOSED_UNCHANGED
P36_BACKUP_TOOLING = PASS_READY_NOT_ARMED
P36_RESTORE_DRILL = PENDING_FIRST_REAL_BACKUP
P36_PAID_UPGRADE = NOT_REQUIRED
P36_FINAL = PASS_VALIDATION_GRADE
```

## Production 容量

0046 上线后实测：

- database_bytes = 18,446,003
- database_used_pct = 3.52%
- database_state = HEALTHY
- max_connections = 60
- current_connections = 11
- active_connections = 1
- connection_used_pct = 18.33%
- connection_state = HEALTHY

当前容量阈值：

- WARNING >= 70%
- CRITICAL >= 90%

## 性能硬化

Production 已确认 4 个 Foreign Key 覆盖索引存在：

- idx_opportunity_github_query_map_query_id
- idx_saved_opportunities_opportunity_id
- idx_source_provenance_audits_aggregator_source_id
- idx_source_provenance_rules_upstream_source_id

Supabase Performance Advisor 在 0046 后：

- unindexed_foreign_keys = 0
- auth_rls_initplan = 0
- 剩余仅 unused_index INFO

新增索引刚创建且当前数据量很小，因此被 Advisor 标记为 unused 是正常现象，不应在缺乏长期统计前删除。

## RLS

20 条用户私有数据 RLS 已改为 InitPlan-friendly 形式：

`auth.uid()` → `(select auth.uid())`

权限语义保持不变。

涉及：

- user_profiles
- saved_opportunities
- watchlists
- watchlist_items
- alert_preferences
- user_alert_events

## Auth

`product_feature_flags.account_auth = false`

P3.6 没有开启账户系统，也没有绕过既有 Auth Launch Gate。

## 安全 Advisor

0046 后没有新增高严重级别安全问题。

剩余项目：

1. `rls_enabled_no_policy` INFO  
   内部 service-role-only / fail-closed 表的既有设计。

2. `pg_net` extension in public WARN  
   现有 Cron / HTTP 依赖，P3.6 不移动。

3. 11 个 authenticated SECURITY DEFINER RPC WARN  
   为当前窄 account API 的有意设计；其 auth.uid() 范围、固定 search_path、anon execute revoke 已单独审计。正式 Auth 上线前仍需 A/B 隔离 E2E。

## Backup / DR

新增：

- ops/db/backup_postgres.sh
- ops/db/verify_backup.sh
- ops/db/restore_postgres.sh
- .github/workflows/database-backup.yml
- config/database_operations_v1.json
- docs/P36_DATABASE_PRODUCTION_HARDENING.md

Backup 特性：

- pg_dump custom format
- no owner / no ACL
- AES-256-CBC + PBKDF2
- SHA256 manifest
- restore fail-closed
- GitHub private artifact retention = 30 days

当前状态：

`BACKUP_AUTOMATION = READY_NOT_ARMED`

原因：尚未安全配置 GitHub Repository Variable / Secrets：

- JIANSHI_DB_BACKUP_ENABLED=true
- JIANSHI_DATABASE_URL
- JIANSHI_BACKUP_PASSPHRASE

因此目前不能声称已经存在独立真实备份。

首次真实 Backup 成功后，必须进行隔离 Restore Drill，之后才能把：

`RESTORE_DRILL = PASS`

## Storage

当前 Production Storage objects = 0。

因此 PostgreSQL logical backup 暂时覆盖当前不可替代业务数据的主体。未来只要 Storage 非 0，就必须增加独立 Object Backup，数据库 dump 不等于 Storage 文件备份。

## 冻结

```
DATABASE_ENGINE = POSTGRESQL
DATABASE_CURRENT_CAPACITY = PASS
DATABASE_SCALE_PATH = PASS
DATABASE_MIGRATABILITY = PASS

FK_INDEX_HARDENING = PASS
RLS_INITPLAN_HARDENING = PASS
CAPACITY_MONITORING = PASS

OFFSITE_BACKUP_TOOLING = PASS
OFFSITE_BACKUP_REAL_COPY = PENDING_SECRET_ARMING
RESTORE_DRILL = PENDING_FIRST_BACKUP

SUPABASE_PRO_UPGRADE = DEFERRED
PITR = DEFERRED
```
