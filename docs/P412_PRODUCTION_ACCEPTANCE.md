# P4.1.2 Stack Exchange 需求信号 — Production Acceptance

日期：2026-10-07

## 结论

```
P412_PR = PASS_MERGED_47
P412_CI = PASS_RUN_137
P412_STAGING_REAL_API_TEST = PASS
P412_SIGNAL_DENSITY = LOW
P412_SOURCE_POLICY = GREEN
P412_PRODUCT_VALUE = HOLD_LOW_SIGNAL
P412_AUTO_COLLECT = FALSE
P412_PRODUCTION_CRON = OFF
P412_PRODUCTION_EDGE_DEPLOY = NOT_DEPLOYED
P412_QUERY_DEFINITIONS = RETAINED_DISABLED
P412_OPP_V02 = UNCHANGED
P412_PUBLIC_READY = UNCHANGED
P412_FINAL = PASS_FROZEN_HOLD
```

## 为什么 HOLD

Stack Exchange 官方 API 在合规层面可用，Staging Collector 也真实跑通。

但对当前见势 Opportunity 相关标签做 7/30 天窗口采样后，近期问题量多数只有 0–1 条。

进一步检查历史累计量较高的 openai-api、langchain、shopify、stripe-payments、youtube-api 等标签，近期 30 天密度仍然过低。

因此问题不是“接不了”，而是“接了也没有足够产品价值”。

## Production 最终状态

`data_sources.stack_exchange`：

- source_status = GREEN
- auto_collect = false
- redisplay_allowed = true
- rate_limit_note = HOLD_LOW_SIGNAL

6 个 Stack Exchange query definition 均：

- enabled = false

Production：

- `jianshi-stackexchange-signals-6h` Cron = 不存在
- `collect-stackexchange-signals` Edge Function = 未部署

因此没有后台自动请求 Stack Exchange。

## 评分验收

0051/0052 上线前后，6 个 Opportunity 的：

- HEAT
- CONTENT
- BUILD
- BUSINESS
- public_ready

逐项完全一致。

Stack Exchange 不参与当前 OPP_V0.2，也不满足 public_ready Evidence Gate。

## 决策原则

```
LEGAL_TO_USE != WORTH_COLLECTING
SOURCE_COUNT_IS_NOT_KPI
QUALITY_FIRST = TRUE
```

只有近期标签密度恢复、出现更有价值的官方指标，或新的 Opportunity taxonomy 与活跃标签高度匹配时，才重新评估 Stack Exchange。
