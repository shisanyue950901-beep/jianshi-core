# P4.1 项目源扩容审计 V1

日期：2026-10-07
状态：IMPLEMENTING_SHADOW

## 目标

见势当前的瓶颈不是数据库容量，而是可消费 Opportunity 太少、证据类型过窄。

P4.1 的目标不是接入最多网站，而是补齐：
- 技术采用信号
- 需求信号
- 产品发布/分发信号
- 搜索需求信号
- 第二个高质量商业证明源

同时保持：
- OPP_V0.2 不变
- public_ready Gate 不变
- 非 GREEN 来源 fail-closed
- 未授权商业数据不采集、不存储、不重展示

## 第一轮来源结论

### npm Public Registry — GREEN / 第一批落地

价值：
- 大量公开 JavaScript/TypeScript package
- weekly/monthly downloads
- dependents
- package metadata
- 可观察某类技术/工具是否从“有人做”发展到“有人采用”

政策依据：
- 官方 Public Registry API
- npm Open Source Terms 允许通过公开 API 使用 registry
- Terms 明确允许商业项目/business purposes

使用边界：
- 只取公开 package metadata 与聚合下载/搜索指标
- 不镜像 README/fulltext
- 不采集用户 PII
- 不把 npm 下载量解释为收入或商业证明
- P4.1 仅作为 TECHNICAL_SUPPLY shadow signal

### Stack Exchange / Stack Overflow API — GREEN / 第二批

价值：
- 开发者真实提问量
- tag 总量与增量
- 可作为技术需求/实施摩擦的 Demand Proxy

政策依据：
- 官方 API
- API Terms 要求 attribution
- P4.1 仅计划聚合 tag/question metadata，不存储正文

使用边界：
- 遵守 throttle
- 明确 attribution
- 不存储完整问题正文
- 不把开发者问答量解释为付费需求
- 进入 DEMAND_SIGNAL shadow，不能满足 public_ready

### Hacker News — YELLOW

官方 API 可访问 public HN data，且文档当前写明 no rate limit。

但 P4.1 没有确认足够明确的商业重展示许可范围。

处理：
- 可以人工研究
- 暂不自动采集
- 暂不公开重展示
- 后续继续政策审查

### Product Hunt — YELLOW / 需要商务许可

官方 API 文档明确：
默认不得用于 commercial purposes；如用于 business 需联系 Product Hunt。

处理：
- 不自动接入
- 后续可单独发商业授权/合作申请
- 即使获批，也只能作为 PRODUCT/DISTRIBUTION signal，不能直接当商业证明

### Reddit — RED

官方 Developer Terms / Data API Terms：
- 商业用途需要 permission / separate agreement
- 未经授权抓取属于违规
- 数据保留与删除还有额外义务

处理：
- 不抓取
- 不使用第三方“Reddit API”绕过
- 若未来价值足够高，再走正式商业合同路线

### Google Trends API — YELLOW

Google 已推出官方 Trends API，但仍处于 limited alpha，需申请 early access。

处理：
- 不抓网页作为替代
- 可考虑申请官方 alpha
- 获得权限后再审 Terms / quota / redisplay

## P4.1 数据架构

新增通用 Shadow Signal Layer：

- external_signal_queries
- external_signal_entities
- external_signal_discoveries
- external_signal_snapshots
- opportunity_external_query_map
- opportunity_external_signal_shadow_v01

优点：
- 新来源不必每次造一套完全不同的数据表
- 先在 shadow 中观察历史
- 不会因为增加一个来源就改变评分
- 未来 HN / Product Hunt / Google Trends 获得合法权限后可复用

## Evidence Class

新增但全部 counts_for_public_validation=false：

- NPM_PACKAGE → TECHNICAL_SUPPLY
- STACKEXCHANGE_TAG → DEMAND_SIGNAL
- HN_STORY → DEMAND_SIGNAL
- PRODUCTHUNT_POST → DISTRIBUTION_SIGNAL
- REDDIT_POST → DEMAND_SIGNAL
- GOOGLE_TRENDS_TERM → DEMAND_SIGNAL

P4.1 不改变：
TECHNICAL_SUPPLY + COMMERCIAL_PROOF + >=5 evidence 的现有 public_ready 合同。

## 当前实施顺序

1. npm：真实接入、跑 Shadow、形成连续快照
2. Stack Exchange：再接入 tag/question aggregate
3. 扩 GitHub query taxonomy
4. 观察一周后，从真实信号中扩 Opportunity Candidate
5. Product Hunt：等新版前台上线后再考虑授权邮件
6. Reddit：无合同不接
7. Google Trends：官方 alpha 申请后再评估

## Opportunity 扩容原则

不直接人工批量创建 50 个 ACTIVE Opportunity。

正确漏斗：

原始 Signal
→ Query Cluster
→ Candidate
→ 多日连续信号
→ 编辑审查
→ Opportunity
→ 商业证据验证
→ public_ready

第一阶段目标仍然是：
- 30–50 个可浏览 Opportunity
- 10–15 个较高质量已验证机会

但必须通过真实证据逐步长出来，不造“项目导航站”。

## 冻结

P41_SOURCE_COUNT_KPI = FORBIDDEN
P41_QUALITY_FIRST = TRUE
P41_NPM = GREEN_IMPLEMENT
P41_STACK_EXCHANGE = GREEN_NEXT
P41_HACKER_NEWS = YELLOW
P41_PRODUCT_HUNT = YELLOW_PERMISSION_REQUIRED
P41_REDDIT = RED_CONTRACT_REQUIRED
P41_GOOGLE_TRENDS = YELLOW_ALPHA
P41_NEW_SIGNALS_AFFECT_SCORE = FALSE
P41_PUBLIC_READY = UNCHANGED
