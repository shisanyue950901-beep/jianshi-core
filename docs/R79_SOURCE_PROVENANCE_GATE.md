# 见势 R7.9｜上游许可继承 Gate

## 为什么需要
第三方聚合器提供公开 API，不代表它能自动把上游市场的受限数据变成可商业再发布数据。

原则：

> 访问权 ≠ 再许可权；聚合器许可不能默认覆盖上游许可。

## FoundersPrime 实测
2026-10-07 Staging 调用：
`GET https://www.foundersprime.com/api/v1/startups?limit=100`

实际返回数组长度：1,150。

上游来源：
- Acquire.com：618
- TrustMRR：532

没有发现第三类来源。

FoundersPrime 自身公开说明支持 API 阅读、索引、引用和带 attribution 的有限展示；但见势当前没有证据证明 FoundersPrime 拥有把 Acquire.com / TrustMRR 收购挂牌再次许可给第三方商业产品的权利。

因此：
- FoundersPrime marketplace/startups = YELLOW
- production auto collect = FALSE
- public redisplay = FALSE
- 仅做许可与数据来源审计

## 数据结构
### source_provenance_rules
记录：
- 聚合器
- 上游 label
- 映射后的上游 source
- INHERIT / EXPLICIT_ALLOW / BLOCK
- 书面许可证据

### source_provenance_audits
记录：
- API 路径
- 样本量
- 上游来源分布
- 审计结果
- evidence hash

## 继承规则
对于聚合条目：

1. 聚合器本身必须通过公开发布 Gate。
2. 必须能识别 upstream provenance。
3. 默认 `INHERIT` 上游 source policy。
4. 上游 RED / YELLOW 不可发布。
5. 未知上游直接 fail-closed。
6. 只有 `EXPLICIT_ALLOW + written_permission_reference` 才能覆盖继承限制。

## FoundersPrime 当前映射
- FoundersPrime / Acquire.com → inherit Acquire.com → BLOCK
- FoundersPrime / TrustMRR → inherit TrustMRR → BLOCK

## 许可申请
向 FoundersPrime 一次问清：
- 是否拥有对 Acquire.com 来源字段的第三方商业再许可权
- 是否拥有对 TrustMRR 来源字段的第三方商业再许可权
- 是否允许历史快照
- 是否允许衍生分析
- 是否允许有限公开展示
- 是否允许商业产品使用
- 如果没有全量权利，能否提供“direct/licensed origin only”的 API filter

即使得到口头答复也不自动解锁。
必须有可存档的书面证据，再进入 Policy Review。
