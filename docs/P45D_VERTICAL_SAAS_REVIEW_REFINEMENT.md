# P4.5D 垂直行业 SaaS Review Queue 审计

日期：2026-10-07
状态：IMPLEMENTING_STAGING_ONLY

## 目标

对 P4.5B/C 产生的 6 条 `垂直行业 SaaS` Review Queue 做首次人工审计，并把可重复判断固化成机器规则。

不推 Production，不改前台，不自动发布 Opportunity。

## 六条样本审计结论

现有 6 条都满足：
- monetizations 包含 SaaS
- niches 非空

但主业务标题分成三类：

### A. Primary SaaS — 4 条

标题明确为：

`... SaaS Business in the ... Niche`

共 4 条。

这些样本的 Marketplace 主分类和结构化 monetization 同时指向 SaaS，并带明确 niche。

决策：

`HIGH / AUTO_APPROVED`

新规则：

`P45D_SAAS_PRIMARY_TITLE`

条件：
- monetizations contains SaaS
- title contains "SaaS Business"
- niches non-empty

### B. Mixed Subscription + SaaS — 1 条

标题：

`... Subscription Business in the Business Niche`

同时 monetizations：
- Subscription
- SaaS

结构化字段说明 SaaS 是变现方式之一，但主标题不是 SaaS Business。

决策：

`MEDIUM / REVIEW_REQUIRED`

新规则：

`P45D_SAAS_SUBSCRIPTION_MIXED`

### C. Digital Product-primary + SaaS — 1 条

标题：

`... Digital Product Business in the Legal Niche`

monetizations：
- Digital Product
- SaaS

该 listing 已经是“数字产品业务”的直接证据。

仅因为它同时出现 SaaS，不应该让它自动成为“垂直行业 SaaS”的直接证据，否则会形成跨子机会语义膨胀。

决策：

`EXCLUDE_FROM_VERTICAL_SAAS_MAPPING`

不创建负向黑名单；通过关闭旧宽规则、只保留更精确的正向规则实现 fail-closed。

## 规则升级

旧规则：

`P45B_SAAS_VERTICAL`

由 P4.5D 设为 inactive。

替换为：

- P45D_SAAS_PRIMARY_TITLE → HIGH / AUTO
- P45D_SAAS_SUBSCRIPTION_MIXED → MEDIUM / REVIEW

规则版本：

`P45D_V1`

## 预期 Staging 结果

垂直行业 SaaS：

- 旧 active matches = 6
- 新 active matches = 5
- auto approved = 4
- review required = 1
- excluded = 1

全 8 个子机会：

- active matches：162 → 161
- auto approved：156 → 160
- review required：6 → 1
- source diversity：仍为 1

这里 active match 下降 1 是正确收紧，不是数据损失。

## 原则

```
MULTI_MONETIZATION != MULTI_CHILD_AUTO_VALIDATION
PRIMARY_BUSINESS_CLASSIFICATION_MATTERS = TRUE
POSITIVE_RULES_FAIL_CLOSED = TRUE
```

以后相同结构的新 listing 会自动套用 P45D_V1，不需要重复人工审同类样本。

只有新的混合分类模式才进入 Review Queue。
