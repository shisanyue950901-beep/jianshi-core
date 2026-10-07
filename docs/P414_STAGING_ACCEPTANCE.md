# P4.1.4 PyPI Staging Acceptance

日期：2026-10-07

## 结论

```
P414_PR = OPEN_49
P414_CI = PASS_RUN_143
P414_STAGING_MIGRATION = PASS
P414_STAGING_COLLECTOR = PASS
P414_TECHNICAL_GATE = PASS
P414_SIGNAL_DENSITY = PASS
P414_METADATA_QUALITY = PASS
P414_INCREMENTAL_DISCOVERY = MEDIUM
P414_GITHUB_OVERLAP = HIGH
P414_COMMERCIAL_PROOF = NONE
P414_PRODUCTION_PROMOTION = HOLD_FOR_REFINEMENT
P414_PRODUCTION_CHANGE = FALSE
```

## 首次真实 Staging 运行

- RSS items: 80
- unique discovered packages: 76
- accepted package metadata: 60
- metadata success rate: 100%
- parser errors: 0
- new snapshots: 60
- candidate count: 26
- candidate match rate: 43.33%
- BigQuery used: false
- package content stored: false
- deprecated JSON downloads used: false
- scoring changed: false

候选类别：

- DEVTOOLS: 18
- AI_AGENT: 8
- DATA_ANALYTICS: 4
- SAAS_INFRA: 3
- CREATOR_MEDIA: 2
- AUTOMATION: 1
- ECOMMERCE: 0
- MARKETING_GROWTH: 0

## 增量价值

26 个 candidate 中：

- 19 个带 GitHub URL
- 8 个带非 GitHub URL
- 1 个只有非 GitHub URL
- 0 个完全没有 project URL

因此 PyPI 的主要价值是：

1. 补充 Python 技术生态；
2. 发现新包/新 release；
3. 给 GitHub 技术项目增加“进入 Python 包生态”的独立分发信号。

它不能替代商业证明，也不适合直接把 package 转成 Opportunity。

## Production

Production 已确认：

- pypi data_sources = 0
- pypi external queries = 0
- pypi cron = false
- PyPI Collector 未部署

因此 P4.1.4 没有修改 Production。

## 下一次若继续 PyPI

必须先处理：

1. candidate quality filter；
2. GitHub/PyPI 去重与互证；
3. 降低 AI / DevTools 偏置；
4. 决定是否引入 PyPI BigQuery download trend 作为 adoption signal。

PR #49 在这些问题解决前保持未合并。
