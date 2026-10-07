# P4.1.2 Stack Exchange 需求信号 — HOLD_LOW_SIGNAL

日期：2026-10-07
状态：FROZEN_HOLD

## 结论

Stack Exchange / Stack Overflow 的官方 API 与使用边界可以满足见势的合规接入要求，因此来源政策层仍保留 GREEN。

但真实 Staging 采集与标签密度复核显示，当前与见势机会相关的近期问题量过低，不适合作为 6 小时级别的趋势/需求信号源。

因此：

- SOURCE_POLICY = GREEN
- PRODUCT_VALUE = HOLD_LOW_SIGNAL
- AUTO_COLLECT = FALSE
- PRODUCTION_CRON = OFF
- QUERY_DEFINITIONS = RETAINED_DISABLED
- COLLECTOR_CODE = RETAINED_NOT_DEPLOYED_TO_PRODUCTION
- OPP_V0.2 = UNCHANGED
- public_ready = UNCHANGED

## 实测

Staging Collector 使用官方 API，仅读取 tag count，不保存正文、标题或用户信息。

初始标签包括：

- openai-api
- langchain
- shopify
- stripe
- saas
- youtube-api

真实 7/30 天窗口中多数标签为 0–1 条近期问题。

进一步检查历史累计量较高的标签，例如 openai-api、langchain、shopify、stripe-payments、youtube-api，30 天窗口仍大多只有 0–1 条。

结论不是“API 不可用”，而是“当前信息密度不够”。

## 决策规则

见势不以接入来源数量作为 KPI。

合法可接 ≠ 值得生产采集。

未来只有满足以下任一条件才重新评估：

1. 目标标签近期问题密度明显恢复；
2. Stack Exchange 提供更适合趋势统计的高密度指标；
3. 见势出现新的 Opportunity taxonomy，与 Stack Exchange 活跃标签更匹配。

在此之前保持 HOLD。
