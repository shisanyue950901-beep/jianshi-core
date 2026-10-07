# P4.5B 自动 Evidence Mapping Rule — Staging 设计

日期：2026-10-07  
状态：IMPLEMENTING_STAGING_ONLY

## 目标

把 P4.5A 的人工证据判断固化为可重复执行的数据库规则。

未来目标：

```
Collector 更新
→ Mapping Rule 自动重跑
→ Child Evidence 自动更新
→ 仅异常/低置信度进入 Review Queue
```

P4.5B 只验证规则引擎本身，不接 Production 自动调度。

## 内部结构

- child_opportunity_shadow_registry
- child_marketplace_mapping_rules
- child_marketplace_evidence_matches
- child_evidence_mapping_summary_v01
- child_evidence_review_queue_v01
- refresh_child_marketplace_evidence_v01()

全部 service-role only。

浏览器、anon、authenticated 用户没有表权限。

## 8 条首批规则

### HIGH / 自动批准 Evidence Match

- Affiliate/Content Site：
  title 包含 Site，且 monetization 命中 Affiliate / Amazon Associates / Display Advertising
- Amazon FBA：
  monetization = Amazon FBA
- YouTube：
  monetization = YouTube
- Digital Product：
  monetization = Digital Product
- Newsletter：
  monetization = Newsletter
- Amazon KDP：
  monetization = Amazon KDP
- 非 Amazon 电商品牌：
  monetization = eCommerce，排除 Amazon FBA / FBM

这些只是“证据匹配自动批准”，不是“机会自动发布”。

### MEDIUM / 人工 Review Queue

- 垂直行业 SaaS：
  monetization = SaaS
  且 niche 非空

保留人工确认的原因：
结构化 SaaS 字段能证明 SaaS 商业资产，但仅凭 niche 非空仍不足以完全证明“垂直行业 SaaS”的语义。

## 自动更新语义

每次 refresh：

1. 旧 active match 先 fail-closed 设为 inactive；
2. 用当前 active listing + active rule 全量重算；
3. 命中的旧 match 恢复 active 并更新时间；
4. 已下架或不再符合规则的 match 自动保持 inactive；
5. HIGH + auto_approve → AUTO_APPROVED；
6. 其他 → REVIEW_REQUIRED。

因此以后不需要人工逐条维护新增/下架 listing。

## 非目标

P4.5B 不做：

- 自动发布子机会；
- 自动判断值得做；
- 自动继承父级 public_ready；
- 修改 OPP_V0.2；
- 修改前台；
- 创建 Production Cron。

## 下一验收

Staging 必须验证：

- 8 个 child 都能产生正确映射；
- 直接数量与 P4.5A 人工审计一致；
- SaaS 进入 Review Queue；
- 其他高确定规则自动批准；
- source diversity 仍然是 1；
- refresh 重跑幂等；
- listing inactive 后 match 能自动失活；
- Production 保持 0 改动。
