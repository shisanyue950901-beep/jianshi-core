# 见势 R4｜机会引擎 v0.1

## 原则
R4 不使用付费 AI API。先用可解释规则把多源事实变成机会评分。

## 当前机会族
- AI Agent 工具与自动化
- LLM 应用与工具
- 一人公司 SaaS
- 轻量电商品牌与 Amazon 资产
- 联盟营销与内容资产
- 创作者媒体资产

## 证据源
GitHub：
- ai_agents query
- llm query
- saas query

Empire Flippers：
- SaaS
- Amazon FBA / FBM / eCommerce / DropShipping
- Affiliate / Amazon Associates / Display Advertising
- YouTube / Newsletter / Digital Product / Info Product

## 四分模型
- HEAT：技术热度 + 市场挂牌活动
- BUSINESS：利润、利润率、估值倍数、市场活跃度
- BUILD：开源供给、一人公司适配、中国化、商业验证
- CONTENT：热度、内容先验、证据广度

版本：`OPP_V0.1`

## 强约束
`public_ready=true` 当前要求：
1. 至少 2 种独立数据源
2. 至少 5 条有效证据

因此 GitHub 很热但没有商业验证的项目，不会直接进入公开“机会榜”。

## Staging 首次结果
- active evidence: 189
- score snapshots inserted: 24
- 唯一 MULTI_SOURCE：一人公司 SaaS
- AI Agent / LLM：技术热，但 BUSINESS 分受无商业证据惩罚
- eCommerce：商业证据强，但当前仍是 SINGLE_SOURCE

这不是最终模型；后续接入 Product Hunt、官网定价、创始人收入披露、搜索/社交信号后再扩展为 OPP_V0.2。
