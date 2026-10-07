# P4.3 第一方匿名用户行为分析 — Production Acceptance

日期：2026-10-07

## 结论

```
P43_PR = PASS_MERGED_46
P43_CI = PASS_RUN_132
P43_MAIN_CI = PASS_RUN_133
P43_STAGING_MIGRATION = PASS
P43_STAGING_EDGE = PASS
P43_STAGING_WRITE_TEST = PASS
P43_PRODUCTION_MIGRATION = PASS
P43_PRODUCTION_EDGE = PASS
P43_PRODUCTION_WRITE_TEST = PASS
P43_STATIC_SNAPSHOT = PASS_RUN_49
P43_STATIC_SNAPSHOT_COMMIT = 3ca68162c80da265b1ecbb7e29055227df17c1f2
P43_PUBLIC_ANALYTICS_JS = PASS
P43_PUBLIC_PRIVACY_NOTICE = PASS
P43_REAL_USER_DATA = NOT_YET_CLAIMED
P43_FINAL = PASS_PRODUCTION
```

## 数据链

```
Browser
→ /analytics.js
→ behavior-track Edge Function
→ record_behavior_event_v01
→ private behavior_events
→ internal aggregate views
```

浏览器没有 behavior_events 表权限。

## 隐私最小化

Production 合同：

- 不持久化 IP
- 不持久化 User-Agent
- 不持久化 Email / Name
- 不持久化完整搜索词
- 搜索只记录 query_length / results_count
- 外链只记录 target host
- visitor UUID 为第一方随机 ID，90 天轮换
- session UUID 使用 sessionStorage
- GPC / DNT 自动停止发送
- 隐私页提供主动关闭与重新开启
- 原始事件默认保留 90 天

## Production 测试

Production Edge 使用随机 synthetic UUID 测试：
- endpoint 返回 RECORDED
- behavior_events 正确写入白名单字段
- synthetic event 验证后已删除，不作为真实用户统计

## 指标

内部视图：

- analytics_daily_funnel_v01
- analytics_opportunity_daily_v01
- analytics_visitor_lifecycle_v01

可计算：
- Unique visitors
- Sessions / page views
- Opportunity detail visitors
- 第二个 Opportunity 浏览
- Catalog search/filter
- Source outbound
- 30 秒参与
- 90% scroll
- 1d / 7d return

## Retention

Cron：

`jianshi-behavior-retention-daily`

Schedule：

`25 3 * * *`

Raw event retention：

90 days.

## Public deployment

Static Snapshot run #49 PASS。

公开隐私页已经说明匿名使用分析、90 天轮换/保留、GPC/DNT 与关闭机制。

公开 `analytics.js` 已可访问。

Snapshot root HTML 中：

```json
{"enabled":true,"endpoint":"https://dalfvgehosxfyxkptxwx.supabase.co/functions/v1/behavior-track"}
```

## 安全

Security Advisor 没有新增高严重级别问题。

`behavior_events` 的 RLS-no-policy INFO 是 deliberate fail-closed：
- anon = no table grants
- authenticated = no table grants
- service_role = internal access

Performance Advisor 仅出现新表索引尚未被真实流量使用的 unused-index INFO，符合当前刚上线状态。

## 不改变

- OPP_V0.2 = UNCHANGED
- public_ready = UNCHANGED
- account_auth = FALSE
- Source Policy = FAIL_CLOSED
- Newsletter launch = CLOSED
- Marketplace = DEFERRED

## 下一步

开始积累真实匿名用户数据。
在正式引流前继续检查 Auth Launch Gate，并扩第二条 GREEN 需求信号源。
