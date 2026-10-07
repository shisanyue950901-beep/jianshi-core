# P4.9｜Evidence-First UI / 证据优先重构

日期：2026-10-08  
状态：STAGING_API_PASS / FRONTEND_CI_PENDING

## 用户反馈对应的问题

本轮直接处理三个问题：

1. UI 视觉层级像内容站，不像研究产品；
2. 页面术语带有大量口语化、营销化和行动导向表达；
3. 没有明确来源支持的编辑判断占据主页面，削弱整体可信度。

## 公开内容原则

公开研究主界面只展示：

- 样本纳入规则
- 当前在售样本
- 有报价样本
- 独立商业来源
- 挂牌披露月营收
- 挂牌披露月净利润
- 挂牌披露利润率
- 挂牌披露周工时
- 挂牌报价
- 来源分类（保留原文）
- 最近公开挂牌记录
- 证据边界

不再在公开主界面展示：

- 优先研究 / 值得研究
- 一人公司适配
- 为什么值得中国用户看
- 适合谁 / 不适合谁
- 可以复制什么
- 为什么推荐
- 第一轮怎么验证
- 泛化风险建议
- 没有直接来源支撑的中国市场推断

这些内容即使内部研究保留，也不再包装成来源事实。

## 术语冻结

| 旧表达 | 新表达 |
|---|---|
| 海外已验证项目 | 海外商业项目研究 / 商业资产分类 |
| 直接商业样本 | 当前在售样本 / 公开挂牌样本 |
| 商业来源种类 | 独立商业来源 |
| 已验证 / 值得研究 | 不用于商业研究卡 |
| 一人公司适配 | 不在公开证据页展示 |
| 今日推荐 | 综合信号 |
| 正在起势 | 热度变化 |
| 值得做 | 可执行性指标 |
| 值得讲 | 传播指标 |
| 赚钱样本 | 商业挂牌样本 / 挂牌披露财务 |
| 估值 | 只有来源明确为估值时使用；当前统一使用“挂牌报价” |

## UI 方向

新版视觉系统：

- 中性浅灰背景 + 白色研究面板；
- 深灰蓝文字；
- 单一低饱和绿色作为交互强调；
- 取消大面积彩色状态 Badge；
- 数字使用等宽/表格数字布局；
- 首页卡片以数据矩阵为主体，而不是长解释文案；
- 详情页采用研究档案结构；
- 原始样本使用表格；
- 所有数据限制集中展示，不分散在营销式提示语中。

## 实时证据接口

新增：

`public-feed?view=research&slug=<slug>`

返回：

- active_sample_count
- priced_sample_count
- metrics.median_asking_price
- metrics.median_monthly_gross_revenue
- metrics.median_monthly_net_profit
- metrics.median_profit_margin_pct
- metrics.median_hours_worked_per_week
- niche_distribution
- samples
- evidence_source
- evidence_boundary

公开页面不再依赖 config 里的静态 direct_samples 作为 Production 真值。

config 仅作为构建失败时的回退快照：

`snapshot_role = BUILD_FALLBACK_ONLY`

## Staging 验收

Staging public-feed version 11 已部署成功。

抽查：

- vertical-industry-saas
- amazon-fba-niche-brand
- amazon-kdp-publishing

均返回：

- 官方 API 来源
- 当前在售样本
- 财务中位数
- 工时中位数
- 来源分类
- 公开挂牌记录
- 4 条证据边界

Staging 数据时间早于 Production，因此样本数量可能与 Production 当前值不同。这是正常环境数据差异，不使用 Staging 数量覆盖 Production。

## 数据边界

公开固定显示：

1. 财务、工时和报价字段来自挂牌方公开披露，见势未独立审计；
2. 挂牌报价不等于最终成交价；
3. 当前每个首批研究分类只有 1 个独立商业来源；
4. 样本不能证明团队规模、中国市场适配、可复制性或未来收益。

## 不改变

- OPP_V0.2 计算逻辑
- Source Policy
- Auth Gates
- PR #52
- 6 个首批项目详情页 noindex,nofollow
- 行为分析事件合同
- P4.8 用户测试 Epoch

## 发布 Gate

发布前必须同时满足：

```text
P49_STAGING_RESEARCH_API = PASS
P49_PUBLIC_COPY_EVIDENCE_ONLY = PASS
P49_UNSUPPORTED_EDITORIAL_COPY = ABSENT
P49_REALTIME_RESEARCH_FETCH = PASS
P49_NOINDEX_BOUNDARY = PASS
P49_CI = PASS
P49_PRODUCTION_EDGE_FUNCTION = NOT_YET
P49_PUBLIC_SITE = NOT_YET
```
