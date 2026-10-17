# P4.5C Collector → Evidence Mapping 自动触发链

日期：2026-10-07
状态：IMPLEMENTING_STAGING_ONLY

## 目标

P4.5B 已证明“怎么自动匹配”。

P4.5C 只解决：

> 什么时候自动匹配，以及下游映射故障是否会污染上游 Collector。

目标链：

```
Empire Collector
→ quality gate PASS
→ pipeline run SUCCESS
→ data source last_success
→ run_child_evidence_mapping_hook_v01(run_id)
→ refresh_child_marketplace_evidence_v01()
→ child_evidence_mapping_runs audit
```

## 失败隔离

Evidence Mapping 属于 downstream enrichment。

冻结：

```
MAPPING_FAILURE != COLLECTOR_FAILURE
```

如果映射失败：

- Empire pipeline run 仍保持 SUCCESS；
- Empire Collector HTTP 成功状态不被改写；
- mapping audit 写 FAILED；
- hook 返回失败状态作为数据，不抛出到 Collector；
- public_ready / OPP_V0.2 / 发布状态不改变。

## Trigger Gate

只有同时满足：

- run_type = EMPIRE_FLIPPERS_COLLECTOR
- pipeline run status = SUCCESS
- source = empire_flippers

才允许执行映射。

其他 run 调用 hook：
- SKIPPED
- 不执行 refresh

## Audit

`child_evidence_mapping_runs`

记录：

- trigger_run_id
- source
- trigger type
- RUNNING / SUCCESS / FAILED / SKIPPED
- rule version
- mapping result
- error
- duration

同一个 trigger_run_id 唯一，重复调用会重跑同一 audit record，不制造重复 run。

## P4.5C 非目标

- 不增加独立 Cron；
- 不自动发布子机会；
- 不把 AUTO_APPROVED Evidence Match 等同于 WORTH_DOING；
- 不推 Production；
- 不改前台。
