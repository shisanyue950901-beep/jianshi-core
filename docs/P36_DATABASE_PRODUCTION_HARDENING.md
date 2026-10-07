# P3.6 数据库生产硬化与灾备运行手册

日期：2026-10-07  
状态：IMPLEMENTING  
范围：验证阶段免费方案，不升级 Supabase 付费计划，不开启 PITR。

## 1. 目标

P3.6 处理四类数据库底座债务：

1. 缺失的 Foreign Key 覆盖索引。
2. Auth 私有表 RLS 的 InitPlan 性能告警。
3. 数据库容量与连接数预警。
4. 独立于 Supabase 控制面的逻辑备份、校验与恢复路径。

不改变：
- OPP_V0.2
- public_ready
- Source Policy
- Auth launch flag
- Newsletter launch flag
- 任何业务数据语义

## 2. 当前容量基线

2026-10-07 Production 实测：

- PostgreSQL 17.11
- DB size：约 17 MB
- 当前 Supabase：Free
- 当前 Free 数据库额度假设：500 MiB
- max_connections：60
- 当前连接：约 17
- 活跃连接：约 1
- Buffer cache hit：99.98%
- temp spill：0
- deadlock：0
- conflict：0
- 最近 24h Edge 5xx：0

结论：当前不是容量瓶颈。

## 3. 容量阈值

内部统一阈值：

- HEALTHY：< 70%
- WARNING：>= 70%
- CRITICAL：>= 90%

当前 Free 500 MiB 假设对应：

- WARNING：350 MiB
- CRITICAL：450 MiB

连接数同样按 70% / 90% 分级。

服务端检查函数：

`database_capacity_health_v01(p_database_limit_bytes bigint)`

默认参数 524288000 bytes，仅允许 `service_role` 执行。

升级 Supabase 或磁盘额度以后，不应继续把 500 MiB 当真实上限；调用函数时必须传入新的实际额度，随后更新 `config/database_operations_v1.json`。

## 4. 索引硬化

新增覆盖索引：

- opportunity_github_query_map(query_id)
- saved_opportunities(opportunity_id)
- source_provenance_audits(aggregator_source_id)
- source_provenance_rules(upstream_source_id)

目的：消除当前 Advisor 的 4 个 unindexed_foreign_keys INFO，并避免数据量扩大后的删除/Join 性能问题。

## 5. RLS 性能硬化

20 条 Auth RLS 策略从：

`user_id = auth.uid()`

优化为：

`user_id = (select auth.uid())`

以及同类 `id = (select auth.uid())` / EXISTS 子查询。

这是性能优化，不是权限放宽。语义仍然是“当前登录用户只能访问自己的私有行”。

涉及：

- user_profiles
- saved_opportunities
- watchlists
- watchlist_items
- alert_preferences
- user_alert_events

目标：消除 `auth_rls_initplan` Warning。

## 6. Backup 设计

### 当前验证期

备份目标：

`Supabase PostgreSQL → encrypted pg_dump → private GitHub Actions artifact`

这是验证期的第二副本，不是最终企业级灾备。

文件：

- ops/db/backup_postgres.sh
- ops/db/verify_backup.sh
- ops/db/restore_postgres.sh
- .github/workflows/database-backup.yml

### 默认关闭

Workflow 只有在 GitHub Repository Variable：

`JIANSHI_DB_BACKUP_ENABLED=true`

时才执行。

还需要 GitHub Secrets：

- `JIANSHI_DATABASE_URL`
- `JIANSHI_BACKUP_PASSPHRASE`

密钥不得写入仓库、Issue、PR、聊天或日志。

当前 P3.6 不自动创建这些 Secret，因此首次真实备份状态必须保持：

`READY_NOT_ARMED`

直到安全配置完成。

## 7. Backup 内容

备份脚本使用 PostgreSQL custom-format logical dump：

- no owner
- no ACL
- 可迁移
- 可用 pg_restore 检查
- AES-256-CBC + PBKDF2 加密
- SHA256 manifest

注意：

PostgreSQL dump 可以保留数据库中的应用/Auth 等逻辑数据，但 **Supabase Storage 的实际对象字节不属于 PostgreSQL dump**。

当前 Production Storage objects = 0，因此现在没有缺失文件数据的问题。

未来一旦允许用户上传：

- 项目附件
- Agent 包
- Demo
- 企业文档
- 交付文件

必须增加独立 Storage object backup；仅做 pg_dump 不够。

## 8. 恢复规则

恢复脚本默认拒绝执行。

必须显式设置：

`ALLOW_RESTORE=YES`

并提供：

`TARGET_DATABASE_URL`

恢复目标必须是：
- 隔离恢复环境
- 新数据库
- 灾备演练数据库

禁止直接指向 Production。

P3.6 不允许在 Production 做破坏性恢复演练。

## 9. 恢复演练流程

第一次 Backup 成功后：

1. 下载加密 artifact。
2. 校验 SHA256。
3. 解密到临时文件。
4. pg_restore --list 验证 archive 结构。
5. 在隔离 PostgreSQL / 新 Supabase recovery target 恢复。
6. 验证关键对象：
   - opportunities
   - opportunity_evidence
   - marketplace_listings
   - github_repositories
   - score_snapshots
   - auth users（若届时已有）
7. 验证关键 row count。
8. 验证 RLS / RPC。
9. 记录 RPO / RTO。
10. 销毁临时恢复环境。

没有真实备份前，`RESTORE_DRILL_STATUS` 必须保持 `PENDING_FIRST_BACKUP`。

## 10. RPO / RTO 建议

验证阶段目标，不作为 SLA：

- Backup cadence：Daily
- Backup retention：30 days
- 目标 RPO：<= 24h
- 首次 Restore Drill 后测量 RTO

未来进入真实企业数据/交易阶段：

- 升级 Production backup 方案
- 考虑 Supabase Pro daily backup / PITR
- 增加更独立的长期对象存储备份
- 定义正式 RPO / RTO

P3.6 不产生任何付费升级。

## 11. 数据迁移能力

见势继续依赖标准 PostgreSQL + Git migrations。

核心迁移路线：

- Supabase → 新 Supabase
- Supabase → 标准 PostgreSQL
- PostgreSQL → 其他托管 PostgreSQL
- 后期 Logical Replication → Analytics

Schema 的 Source of Truth 仍然是 GitHub migrations。

数据库备份不是 schema 管理替代品；二者职责不同：

- Migration：可重复构建结构
- Backup：恢复不可重建的数据

## 12. Auth 安全说明

当前 authenticated RPC 使用 SECURITY DEFINER 是有意设计：

- browser 不直接获得底层内部表权限
- RPC 内部使用 auth.uid()
- search_path 固定
- anon 无 execute
- authenticated 无 public schema CREATE

P3.6 不机械移除这些 RPC。

Auth 正式开放之前仍需完成现有 Auth Launch Gate A/B 隔离验收。

## 13. 当前冻结

```
DATABASE_ENGINE = POSTGRESQL
DATABASE_VENDOR = SUPABASE_CURRENTLY
MIGRATABLE = TRUE
CURRENT_CAPACITY = PASS
PAID_UPGRADE = NOT_REQUIRED_VALIDATION_STAGE

FK_INDEX_HARDENING = IMPLEMENTED
RLS_INITPLAN_HARDENING = IMPLEMENTED
CAPACITY_MONITOR = IMPLEMENTED_SERVICE_ROLE_ONLY

BACKUP_AUTOMATION = READY_NOT_ARMED
BACKUP_ENCRYPTION = REQUIRED
BACKUP_SECOND_COPY = GITHUB_PRIVATE_ARTIFACT
BACKUP_RETENTION = 30_DAYS
RESTORE_GUARD = ALLOW_RESTORE_REQUIRED
RESTORE_DRILL = PENDING_FIRST_BACKUP

STORAGE_OBJECT_BACKUP = REQUIRED_WHEN_STORAGE_NONZERO
PITR = DEFERRED_UNTIL_PAID_PRODUCTION_NEED
```
