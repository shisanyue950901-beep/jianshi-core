# 见势 R7.8｜退出活跃度辅助商业证据

## 评分版本
OPP_V0.2

## 目标
把 Empire Flippers 官方 API 中可确认的 Sold 状态作为 BUSINESS_SCORE 的弱辅助证据，同时避免把同一来源重复计算成新的独立数据源。

## 规则
- Sold 状态来源仍是 Empire Flippers，同一数据源。
- 不增加 source_count。
- 不增加多源 Gate 的来源数量。
- 不把 Sold 数量解释为成交率。
- 不把最后挂牌价解释为真实成交价。
- 不把最后挂牌倍数解释为真实成交倍数。

## 样本 Gate
- sold_status_count < 5：sold_activity_score = 0，不参与 BUSINESS_SCORE。
- sold_status_count >= 5：计算退出活跃度。
- 对 BUSINESS_SCORE 的最大加分 = 5.00。
- HEAT / CONTENT / BUILD 不获得 Sold 加分。

## Staging 实测
- 轻量电商品牌与 Amazon 资产：Sold 25，bonus +5.00
- 创作者媒体资产：Sold 8，bonus +3.37
- 联盟营销与内容资产：Sold 5，bonus +2.75
- 一人公司 SaaS：Sold 1，bonus +0.00
- AI Agent 工具与自动化：Sold 0，bonus +0.00
- LLM 应用与工具：Sold 0，bonus +0.00

## 对外展示
机会详情页显示：
- 已捕获 Sold 状态样本数
- 在市天数中位数
- 样本年利润中位数
- 是否达到 5 个样本的评分门槛

固定披露：
“Sold 只表示该挂牌在官方市场中的已售状态。见势没有把最后挂牌价当作真实成交价，也不会把 Sold 样本数解释为成交率。”

## 版本审计
OPP_V0.1 历史分数保留。
OPP_V0.2 写入新的 score_snapshots，不覆盖旧版本。


## Production 验收｜2026-10-07
- OPP_V0.2 = ACTIVE
- active_evidence = 496
- validated opportunities = 4
- AI Agent / LLM 仍保持单源观察
- 轻量电商品牌：Sold 25，样本达标
- 创作者媒体资产：Sold 8，样本达标
- 联盟营销与内容资产：Sold 5，样本达标
- 一人公司 SaaS：Sold 1，样本不足，不加分
- OPP_V0.1 历史保留
- OPP_V0.2 已写入独立 score_snapshots
- source_count 未因 Sold 状态增加
