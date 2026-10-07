# P4.1.4 PyPI Staging 验证

日期：2026-10-07
状态：STAGING_CANDIDATE

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
