# P3.1 商业证据质量 Shadow 模型

日期：2026-10-07

## 目的

把两个概念彻底分开：

1. **来源质量（Quality）**：这个市场本身的筛选、核验、商业证据强度如何。
2. **合法可用性（Eligibility）**：见势是否得到自动采集、历史存储、派生分析和公开展示权限。

高质量不等于可以使用。

## Shadow 权重

当前仅作为内部解释层，不进入 OPP_V0.2：

- Empire Flippers = 1.00
- Acquire = 1.00（未授权，实际不进入统计）
- FE International = 1.00（未授权）
- Quiet Light = 1.00（未授权）
- Flippa = 0.85（未授权）
- Microns = 0.85（未授权）
- StartupMKT = 0.85（未授权）
- Investors Club = 0.85（未授权）
- Motion Invest = 0.65（未授权）

只有同时满足以下条件的来源才会进入 `commercial_evidence_quality_shadow_v01`：

- source_status = GREEN
- auto_collect = true
- redisplay_allowed = true
- commercial_use_allowed = true
- automated_collection_allowed = true
- redisplay_allowed(policy) = true
- derived_public_analytics_allowed = true

因此即使 Acquire 被评为 S/1.00，只要授权没通过，它对当前机会评分和 public_ready 的贡献仍然是 0。

## 新增高质量候选

### Quiet Light

公开页面强调 vetted listings，覆盖 SaaS、Amazon、eCommerce、Content，并公开 asking price / revenue / income 等字段。没有在本轮找到可验证的公开 API 或第三方商业再利用许可，因此保持 YELLOW。

### StartupMKT

公开 acquisition marketplace 显示约 1,970 个 open-to-acquisition startups，并强调 primary Stripe-verified revenue metrics。没有在本轮找到可验证的公开 API 或第三方商业再利用许可，因此保持 YELLOW。

## GREEN 扫描结论

本轮未发现第二个可以像 Empire Flippers 一样，明确公开允许第三方 syndication 的高质量在线业务交易市场。

CatchBuys 虽提供正式 REST API，但其数据来自多家上游市场，包括 Flippa、Empire Flippers、Microns 等；在没有逐一确认上游 sublicense / redistribution 权限前，继续保持 YELLOW / provenance-blocked，不能作为绕过上游限制的捷径。

## 冻结

```
QUALITY_TIER != LEGAL_PERMISSION
SHADOW_WEIGHT != SCORE_WEIGHT
UNLICENSED_SOURCE_CONTRIBUTION = 0
OPP_V0.2 = UNCHANGED
PUBLIC_READY = UNCHANGED
```
