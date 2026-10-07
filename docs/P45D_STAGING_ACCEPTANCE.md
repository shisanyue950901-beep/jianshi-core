# P4.5D 垂直行业 SaaS Review Queue — Staging Acceptance

日期：2026-10-07

## 结论

```
P45D_CI = PASS_RUN_169
P45D_STAGING_MIGRATION_0058 = PASS
P45D_STAGING_MIGRATION_0059 = PASS

P45D_RULESET_VERSION = P45D_V1

P45D_ORIGINAL_REVIEW_ROWS = 6
P45D_AUTO_APPROVED = 4
P45D_REVIEW_REQUIRED = 1
P45D_EXCLUDED_FROM_SAAS = 1

P45D_TOTAL_ACTIVE_MATCHES = 161
P45D_TOTAL_AUTO_APPROVED = 160
P45D_TOTAL_REVIEW_REQUIRED = 1
P45D_SOURCE_DIVERSITY = 1

P45D_REAL_EMPIRE_TRIGGER = PASS
P45D_AUDIT_RULE_VERSION = PASS_P45D_V1
P45D_PRODUCTION_CHANGE = FALSE

P45D_FINAL = PASS_STAGING
```

## 六条人工审计结果

### 4 条：升级为 HIGH / AUTO_APPROVED

共同特征：

- monetizations 包含 SaaS
- niches 非空
- Marketplace 主标题明确为 `SaaS Business in the ... Niche`

新规则：

`P45D_SAAS_PRIMARY_TITLE`

这些样本以后无需逐条人工审核。

### 1 条：继续 REVIEW_REQUIRED

主标题：

`Subscription Business in the Business Niche`

结构化 monetization：
- Subscription
- SaaS

虽然存在 SaaS 变现，但 Marketplace 主业务分类并非明确 SaaS Business。

新规则：

`P45D_SAAS_SUBSCRIPTION_MIXED`

状态：
- MEDIUM
- REVIEW_REQUIRED

这类混合业务以后仍进入人工 Review Queue。

### 1 条：从垂直行业 SaaS 映射中剔除

主标题：

`Digital Product Business in the Legal Niche`

monetizations：
- Digital Product
- SaaS

该资产已经直接支持“数字产品业务”。

仅因为 monetization 同时出现 SaaS，不能让系统把它自动当成“垂直行业 SaaS”直接证据。

因此：
- 不建立 SaaS 正向规则；
- 旧宽泛规则停用后，该 match 自动 inactive；
- 不需要手工维护负向黑名单。

## 旧规则关闭

`P45B_SAAS_VERTICAL`

已设为 inactive。

原因：

旧规则：

`SaaS monetization + niche non-empty`

过宽，会同时吸收：
- Primary SaaS
- Subscription-primary
- Digital Product-primary

P4.5D 改为根据主要商业分类做正向规则。

## Staging 最终映射

| 具体机会 | Active | Auto | Review |
|---|---:|---:|---:|
| 联盟营销 / 内容站 | 11 | 11 | 0 |
| Amazon FBA 细分品牌 | 77 | 77 | 0 |
| Amazon KDP 数字出版 | 11 | 11 | 0 |
| 非 Amazon 电商品牌 | 24 | 24 | 0 |
| 数字产品业务 | 15 | 15 | 0 |
| Newsletter 订阅媒体 | 2 | 2 | 0 |
| 垂直行业 SaaS | 5 | 4 | 1 |
| YouTube 垂直媒体资产 | 16 | 16 | 0 |

总计：

- active = 161
- auto approved = 160
- review required = 1

自动处理率：

`160 / 161 = 99.38%`

注意：
这里表示“当前 Evidence Match 的自动处理率”，不等于 Opportunity 已完成商业验证，也不等于“值得做”。

## Ruleset Audit 修复

P4.5D 发现：

旧 refresh 结果仍硬编码：

`rule_version = P45B_V1`

虽然映射行为正确，但审计版本会失真。

0059 已修复：

- 增加 `child_evidence_mapping_ruleset_version_v01()`
- 当前 effective ruleset = `P45D_V1`
- refresh 同时返回：
  - rule_version = P45D_V1
  - ruleset_version = P45D_V1
- 新 Mapping Audit 使用 P45D_V1

真实 Empire Collector 再跑 1 页：

- HTTP 200
- fetched = 100
- accepted = 100
- new snapshots = 0
- mapping hook = SUCCESS
- audit rule_version = P45D_V1
- mapping result = 161 / 160 / 1

因此审计语义与实际规则一致。

## 当前人工负担

当前 161 条 active evidence match：

- 160 条自动处理
- 1 条人工 Review

从日常维护角度，当前 Empire 子机会证据映射已经基本自动化。

人工职责缩小到：

1. 混合商业模式；
2. 新规则首次出现；
3. 新子机会第一次规则设计；
4. 抽样审计自动规则；
5. 商业判断与最终编辑结论。

## 原则冻结

```
AUTO_EVIDENCE_MATCH != AUTO_OPPORTUNITY_VALIDATION
MULTI_MONETIZATION != MULTI_CHILD_AUTO_VALIDATION
PRIMARY_BUSINESS_CLASSIFICATION_MATTERS = TRUE
AMBIGUOUS_CASES_STAY_REVIEWABLE = TRUE
```

不为了追求 100% 自动化而牺牲证据精度。

## Production

重新确认 Production：

- child marketplace mapping rules = 不存在
- child evidence mapping runs = 不存在
- P45D ruleset version function = 不存在

因此：

`P45D_PRODUCTION_CHANGE = FALSE`

## 下一阶段建议

P4.5A-D 已经证明：

- 人工审计可以转成机器规则；
- Empire 数据更新可以自动触发；
- 高确定证据可以自动维护；
- 模糊证据进入 Review Queue；
- 规则可以通过人工反馈逐步收紧。

从主线优先级看，不建议继续在映射引擎上深挖。

下一步应回到用户可见产品：

> **开始制作第一批 8 个具体创业机会的用户详情内容。**

其中状态统一保持：
- 值得研究
- 不直接宣称值得做
- 明确显示证据来源和当前不确定性。
