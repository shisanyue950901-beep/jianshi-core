# P4.1 项目源扩容 Production 验收

日期：2026-10-07

## 结论

```
P41_CODE = PASS_MAIN
P41_PR = PASS_MERGED_42
P41_CI = PASS_RUN_117
P41_STAGING_MIGRATION_0047 = PASS
P41_STAGING_NPM_COLLECTOR = PASS
P41_STAGING_CRON_0048 = PASS
P41_PRODUCTION_MIGRATION_0047 = PASS
P41_PRODUCTION_CRON_0048 = PASS
P41_PRODUCTION_NPM_COLLECTOR = PASS
P41_OPP_V02 = UNCHANGED
P41_PUBLIC_READY = UNCHANGED
P41_FINAL = PASS_PRODUCTION_SHADOW
```

## 新来源状态

- npm = GREEN / ACTIVE SHADOW COLLECTION
- Stack Exchange = GREEN / NEXT
- Hacker News = YELLOW / policy review
- Product Hunt = YELLOW / commercial permission required
- Reddit = RED / commercial contract required
- Google Trends = YELLOW / official alpha access required

非 GREEN 来源仍为 fail-closed。

## Production npm 首次真实采集

```
queries = 6
fetched = 300
unique_entities = 300
new_snapshots = 300
parser_errors = 0
scoring_changed = false
```

6 个当前 Opportunity 各获得 50 个 npm shadow entity。

这些数据只进入：

`opportunity_external_signal_shadow_v01`

不会进入 OPP_V0.2，也不会改变 public_ready。

## Public Gate 回归

Production 仍保持：

- affiliate-content = public_ready true
- creator-media = true
- ecommerce-brands = true
- solo-saas = true
- ai-agent-tools = false
- llm-tools = false

npm 证据类型 NPM_PACKAGE 虽属于 TECHNICAL_SUPPLY，但 counts_for_public_validation=false。

## Cron

```
jobname = jianshi-npm-signals-6h
schedule = 27 */6 * * *
active = true
```

## 数据架构

新增内部 Shadow Signal Layer：

- external_signal_queries
- external_signal_entities
- external_signal_discoveries
- external_signal_snapshots
- opportunity_external_query_map
- opportunity_external_signal_shadow_v01

所有底层表均不开放给 anon/authenticated。

## 冻结

```
SOURCE_COUNT_IS_KPI = FALSE
NPM_SIGNAL = PRODUCTION_SHADOW
STACK_EXCHANGE = NEXT_SOURCE
PRODUCT_HUNT = NO_COMMERCIAL_USE_WITHOUT_PERMISSION
REDDIT = NO_COLLECTION_WITHOUT_CONTRACT
GOOGLE_TRENDS = NO_WEB_SCRAPE_SUBSTITUTE
NEW_SIGNAL_AFFECTS_SCORE = FALSE
PUBLIC_READY_GATE = UNCHANGED
```
