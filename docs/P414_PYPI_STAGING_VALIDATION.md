# P4.1.4 PyPI Staging 验证

日期：2026-10-07
状态：PASS_STAGING_CONDITIONAL

## 范围

本阶段只验证 PyPI 是否值得成为见势的新项目发现源。

不会：
- 推 Production
- 开 Cron
- 修改 OPP_V0.2
- 修改 public_ready
- 直接创建新的 Opportunity
- 使用 BigQuery
- 保存 package 文件 / README / 完整描述
- 使用已废弃的 JSON downloads 字段

## 官方接入方式

发现：
- Newest Packages RSS
- Latest Updates RSS

补充 metadata：
- PyPI JSON API

原因：
PyPI 官方文档建议周期检查新包/更新时优先使用 RSS；JSON API 适合单项目 metadata。

## 本阶段保存

- package name
- latest version
- requires_python
- license_expression
- 最多 25 个 classifier
- 最多 12 个 project URLs
- keyword count（不存原始 keywords）
- 由 transient summary/keywords/classifier 计算出的候选类别

候选类别：
- AI_AGENT
- AUTOMATION
- DATA_ANALYTICS
- SAAS_INFRA
- ECOMMERCE
- CREATOR_MEDIA
- MARKETING_GROWTH
- DEVTOOLS

这些类别只是候选发现辅助，不进入评分。

## Staging 验收

必须满足：
- RSS 正常返回
- >= 20 个有效 package metadata
- JSON metadata success rate >= 80%
- package_content_stored = false
- deprecated_json_downloads_used = false
- scoring_changed = false

产品价值另行观察：
- candidate_match_rate
- candidate_categories 分布
- 是否能发现当前 GitHub/npm 之外的新 Opportunity Cluster

技术 Gate PASS 不代表 Production PASS。
如果信息密度或类别质量不足，允许像 Stack Exchange 一样 HOLD。


## Staging 实测结果

2026-10-07 首次真实运行：

- RSS items = 80
- unique discovered = 76
- accepted package metadata = 60
- metadata success rate = 100%
- parser errors = 0
- new snapshots = 60
- candidate count = 26
- candidate match rate = 43.33%
- package_content_stored = false
- deprecated_json_downloads_used = false
- BigQuery used = false
- scoring_changed = false

候选类别：

- DEVTOOLS = 18
- AI_AGENT = 8
- DATA_ANALYTICS = 4
- SAAS_INFRA = 3
- CREATOR_MEDIA = 2
- AUTOMATION = 1
- ECOMMERCE = 0
- MARKETING_GROWTH = 0

## 增量价值审计

26 个 candidate 中：

- 带 GitHub URL = 19
- 带非 GitHub URL = 8
- 只有非 GitHub URL = 1
- 无 project URL = 0

说明 PyPI 当前更适合：

1. 补 Python 生态技术供给；
2. 发现新发布/新更新的 Python 项目；
3. 给 GitHub 项目增加“已进入包生态”的独立信号；

而不是单独承担“发现商业项目”的职责。

## 最终 Staging 判断

```
P414_TECHNICAL_GATE = PASS
P414_SIGNAL_DENSITY = PASS
P414_METADATA_QUALITY = PASS
P414_INCREMENTAL_DISCOVERY = MEDIUM
P414_GITHUB_OVERLAP = HIGH
P414_COMMERCIAL_PROOF = NONE
P414_PRODUCTION_PROMOTION = HOLD_FOR_REFINEMENT
P414_PRODUCTION_CHANGE = FALSE
```

进入 Production 前至少再解决：

- 减少 DEVTOOLS / AI 偏置；
- 增加 candidate quality filter，降低关键词误命中；
- 明确 PyPI 与 GitHub 的去重/互证语义；
- 评估是否值得引入 BigQuery download trend 作为 adoption signal。

因此 PR 保持未合并，不在本阶段推 Production。
