# P4.5C Collector → Evidence Mapping 自动触发 — Staging Acceptance

日期：2026-10-07

## 结论

```
P45C_CI = PASS_RUN_164
P45C_STAGING_MIGRATION_0057 = PASS
P45C_STAGING_EMPIRE_COLLECTOR_DEPLOY = PASS
P45C_REAL_TRIGGER_TEST = PASS

P45C_TRIGGER_SOURCE = EMPIRE_FLIPPERS_COLLECTOR
P45C_TRIGGER_CONDITION = PIPELINE_SUCCESS_ONLY
P45C_MAPPING_AUDIT = PASS
P45C_REPEAT_TRIGGER_IDEMPOTENT = PASS
P45C_NON_EMPIRE_TRIGGER_GATE = PASS_SKIPPED

P45C_ACTIVE_MATCHES = 162
P45C_AUTO_APPROVED = 156
P45C_REVIEW_REQUIRED = 6
P45C_SOURCE_DIVERSITY = 1

P45C_FAILURE_ISOLATION_CONTRACT = PASS
P45C_PRODUCTION_CHANGE = FALSE

P45C_FINAL = PASS_STAGING
```

## 真实 Collector 触发测试

Staging 使用受控参数：

- active_max_pages = 1
- include_sold = false

Empire Collector 真实结果：

- HTTP = 200
- quality_status = PASS
- fetched = 100
- accepted = 100
- parser_errors = 0
- new_snapshots = 100
- pipeline status = SUCCESS

Collector 成功后自动返回：

```json
{
  "child_evidence_mapping_hook": {
    "ok": true,
    "status": "SUCCESS"
  }
}
```

Mapping result：

- matched children = 8
- active matches = 162
- auto approved = 156
- review required = 6
- commercial source diversity = 1
- publication changed = false
- scoring changed = false

因此：

```
EMPIRE_SUCCESS
→ MAPPING_AUTO_TRIGGER
→ SUCCESS
```

已在真实 Staging 链路成立。

## Audit

新增：

- child_evidence_mapping_runs
- child_evidence_mapping_run_audit_v01
- run_child_evidence_mapping_hook_v01(run_id)

真实触发产生独立 audit record：

- trigger type = EMPIRE_FLIPPERS_COLLECTOR
- status = SUCCESS
- rule version = P45B_V1
- error = null

映射运行与数据源 Collector run 分开记录。

## Trigger 幂等

对同一个成功 Empire pipeline run 再次调用 hook：

- mapping 再次正常完成
- audit_id 保持同一个
- trigger_run_id 对应 audit row count = 1
- 不产生重复 audit run

`P45C_REPEAT_TRIGGER_IDEMPOTENT = PASS`

## 非 Empire Gate

使用一个成功的：

`PYPI_SIGNAL_COLLECTOR`

调用相同 hook。

结果：

```
status = SKIPPED
reason = TRIGGER_NOT_ELIGIBLE
```

因此其他 Collector 不会误触发 Empire child mapping。

## 失败隔离

代码合同：

```
MAPPING_FAILURE != COLLECTOR_FAILURE
```

映射内部使用 exception isolation：

- refresh 失败 → mapping audit = FAILED
- hook 返回 FAILED 数据
- 不向 Empire Collector 抛出数据库异常

Edge Collector 本身也对 RPC error / client exception 做 catch。

Empire HTTP 状态仍严格由：

`gatePass ? 200 : 503`

决定，而不是由 mapping hook 决定。

本阶段没有故意破坏 Staging 数据库来制造 runtime mapping failure；失败隔离通过 CI/代码合同与数据库 exception boundary 验收，不虚构真实失败样本。

## 安全

child_evidence_mapping_runs：

- RLS enabled
- anon = no access
- authenticated = no access
- service_role only

新 hook：

- anon = no execute
- authenticated = no execute
- service_role only

Security Advisor 没有新增高严重问题。

RLS-no-policy INFO 是内部 fail-closed 设计。

## 性能

P4.5B 的 3 个 FK 缺索引已经全部修复。

P4.5C 新 audit 表：
- trigger_run_id = unique index
- trigger_source_id = covering index

最新 Advisor：

`unindexed_foreign_keys = 0`

unused-index INFO 属于刚上线 Staging 的正常状态。

## Production

重新确认 Production：

- child_evidence_mapping_runs = 不存在
- run_child_evidence_mapping_hook_v01(uuid) = 不存在
- child_marketplace_evidence_matches = 不存在

所以 P4.5B/C 目前仍是纯 Staging。

## 当前自动化程度

到 P4.5C 为止：

```
Empire Collector
→ 自动采集
→ 自动清洗
→ 自动更新 listing
→ 自动触发 child evidence mapping
→ 自动更新 high-confidence evidence
→ medium-confidence 自动进入 Review Queue
→ 自动记录 mapping audit
```

日常不再需要人工逐条维护 Empire evidence mapping。

人工只需要：
- Review Queue
- 新规则首次审计
- 异常/边界情况

## 下一阶段

如果继续，下一小步应是 P4.5D：

> 对 6 条垂直行业 SaaS Review Queue 做第一次人工审核，并把审核结果固化成更精确的自动规则或保持人工规则。

P4.5D 仍可只做 Staging，不必立即推 Production。
