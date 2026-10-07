# P3 高质量商业数据源层 Production 验收

日期：2026-10-07

## 结论

```
P3_STRATEGY = ACQUIRE_CLASS_QUALITY_FIRST
P3_CODE = PASS_MAIN
P3_PR = PASS_MERGED_35
P3_CI = PASS_RUN_95
P3_STAGING_MIGRATION = PASS
P3_STAGING_FAIL_CLOSED = PASS
P3_PRODUCTION_MIGRATION = PASS
P3_PRODUCTION_FAIL_CLOSED = PASS
P3_PERMISSION_QUEUE = PASS
P3_OUTREACH_DRAFTS = PASS_NOT_SENT
P3_FINAL = PASS_PRODUCTION_POLICY_LAYER
```

## Production 质量优先级

1. S / Empire Flippers / GREEN / 已接入
2. S / Acquire.com / RED / 需书面许可
3. S / FE International / RED / 需书面许可
4. A / Flippa / RED / 需书面许可
5. A / Microns / RED / 需书面许可
6. A / Investors Club / YELLOW / 权利未明确
7. B / Motion Invest / YELLOW / 权利未明确

高质量等级只决定授权投入顺序，不覆盖 Source Policy。

## Production Gate 验收

除 Empire Flippers 外，首批候选全部保持：

- auto_collect = false
- redisplay_allowed = false
- automated_collection_allowed = false
- derived_public_analytics_allowed = false
- written_permission_required = true

因此 0043 上线不会触发任何新增自动采集或公开再分发。

## 授权队列

以下来源均已处于 DRAFT：

- Acquire.com
- FE International
- Flippa
- Microns
- Investors Club
- Motion Invest

统一申请范围：

- AUTOMATED_API_OR_FEED
- HISTORICAL_SNAPSHOT_STORAGE
- DERIVED_ANALYTICS
- PUBLIC_SUMMARY_DISPLAY
- COMMERCIAL_PRODUCT_USE

## Gmail 草稿

已创建但未发送：

- Acquire.com → support@acquire.com
- FE International → support@feinternational.com，cc fecapitalinfo@feinternational.com
- Flippa → support@flippa.com
- Microns → support@microns.io

所有草稿均明确：
- 不绕过平台限制
- 不需要 NDA/私密 deal-room 数据
- 先申请官方 API/feed/授权
- 接受字段级、速率、缓存、归因和下架要求

## 安全审查

0043 新增 `commercial_market_source_tiers` 采用 RLS + 无 anon/authenticated policy 的 service-role-only fail-closed 模式。
Supabase Security Advisor 新增的是对应的 `rls_enabled_no_policy` INFO，符合内部表设计；未产生新的高严重级别安全错误。

## 冻结规则

- 禁止直接抓 Acquire / FE / Flippa / Microns
- 禁止用聚合 API 绕过上游授权
- 未收到书面许可前，不改变 source_status 到 GREEN
- 收到许可后仍必须：Policy Review → Registry → Staging → Quality Gate → Publication Gate → Production
