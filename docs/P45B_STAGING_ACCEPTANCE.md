# P4.5B 子机会证据自动映射 — Staging Acceptance

日期：2026-10-07

## 结论

```
P45B_PR = OPEN_52
P45B_CI = PASS_RUN_160
P45B_STAGING_MIGRATION_0055 = PASS
P45B_STAGING_MIGRATION_0056 = PASS

P45B_RULE_VERSION = P45B_V1
P45B_CHILDREN = 8
P45B_ACTIVE_MATCHES = 162
P45B_AUTO_APPROVED = 156
P45B_REVIEW_REQUIRED = 6
P45B_SOURCE_DIVERSITY = 1

P45B_IDEMPOTENCY = PASS
P45B_DEACTIVATE_REACTIVATE = PASS
P45B_FK_INDEXES = PASS
P45B_SECURITY = PASS_FAIL_CLOSED_INTERNAL
P45B_PRODUCTION_CHANGE = FALSE

P45B_FINAL = PASS_STAGING
```

## 首次真实 Staging 映射

| 子机会 | Active | Auto Approved | Review | Source Diversity |
|---|---:|---:|---:|---:|
| 联盟营销 / 内容站 | 11 | 11 | 0 | 1 |
| Amazon FBA 细分品牌 | 77 | 77 | 0 | 1 |
| Amazon KDP 数字出版 | 11 | 11 | 0 | 1 |
| 非 Amazon 电商品牌 | 24 | 24 | 0 | 1 |
| 数字产品业务 | 15 | 15 | 0 | 1 |
| Newsletter 订阅媒体 | 2 | 2 | 0 | 1 |
| 垂直行业 SaaS | 6 | 0 | 6 | 1 |
| YouTube 垂直媒体资产 | 16 | 16 | 0 | 1 |

总计：
- active matches = 162
- auto approved = 156
- review required = 6

与 P4.5A 人工审计逐项一致。

## Review Queue

垂直行业 SaaS 保留 MEDIUM confidence。

规则：

`monetizations contains SaaS AND niches non-empty`

因为 SaaS + niche 能证明 SaaS 商业资产，但仍不足以完全自动证明“垂直行业 SaaS”的编辑语义。

因此 6 条进入：

`child_evidence_review_queue_v01`

其余 7 个高确定 structured monetization 规则自动批准 Evidence Match。

## 幂等

连续两次执行：

`refresh_child_marketplace_evidence_v01()`

结果完全一致：

- 162 active
- 156 auto approved
- 6 review
- 8 children
- source diversity 1

没有重复膨胀。

## Listing 生命周期

在 Staging 中选取 1 条 Amazon FBA listing 做受控测试：

1. active = false
2. refresh
3. FBA child match 从 77 → 76
4. 对应 match 自动 inactive
5. listing active 恢复 true
6. refresh
7. FBA child match 从 76 → 77
8. 对应 match 自动恢复 active

最终 Staging 原始 listing 状态已恢复。

结论：

`P45B_DEACTIVATE_REACTIVATE = PASS`

因此以后 source listing 新增、下架、恢复时，不需要人工逐条维护证据 match。

## 安全

内部表：
- child_opportunity_shadow_registry
- child_marketplace_mapping_rules
- child_marketplace_evidence_matches

全部：
- RLS enabled
- anon 无表权限
- authenticated 无表权限
- service_role only

Advisor 的 RLS-no-policy INFO 为 deliberate fail-closed。

没有新增高严重安全问题。

## 性能

初次 Advisor 发现 3 个 FK 缺覆盖索引。

0056 已补：

- parent_opportunity_id
- rule_id
- source_id

复查后：

`unindexed_foreign_keys = 0`

新索引当前显示 unused 属于正常现象，因为功能刚上线 Staging。

## Production

Production 已确认：

- child_opportunity_shadow_registry = 不存在
- child_marketplace_mapping_rules = 不存在
- child_marketplace_evidence_matches = 不存在
- refresh_child_marketplace_evidence_v01() = 不存在

因此 P4.5B 没有修改 Production。

## 自动化边界

P4.5B 已完成：

> 自动“怎么匹配证据”

但尚未完成：

> 每次 Collector 更新后自动“什么时候触发 refresh”

当前 Staging refresh 仍由验收过程显式调用。

下一小步 P4.5C 应只解决自动触发：

```
Empire Collector Success
→ refresh_child_marketplace_evidence_v01()
→ failure isolation
→ mapping run audit
```

在触发链通过 Staging 验收前，不推 Production、不自动发布子机会。
