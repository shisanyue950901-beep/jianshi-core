# 见势 R7.7｜已售状态观察与退出基准

## 为什么做
Acquire 类交易市场最有价值的不只是“现在挂多少钱”，还包括：
- 哪些商业模式真的从 For Sale 进入 Sold
- 卖出前最后一次公开挂牌价
- 卖出前最后一次公开挂牌倍数
- 在市场停留了多久

Empire Flippers 官方 Marketplace API 是当前 GREEN 商业源，并允许在自有网站/邮件中 syndicate listings。

## 严格定义
Empire Flippers 当前公开 Sold 响应实测没有返回可直接使用的真实成交价字段。

因此见势严禁把：
- listing_price
- last asking price
- annual_listing_multiple
称为“成交价”或“成交倍数”。

R7.7 使用术语：
- 首次观察到 Sold
- 卖出前最后挂牌价
- 卖出前最后挂牌倍数
- 观察到的 For Sale → Sold 状态迁移

## 数据模型
marketplace_listing_status_events：
记录每次观察到的 listing_status 变化。

当系统真实观察到：
For Sale → Sold

冻结旧状态：
- prior_listing_price
- prior_annual_listing_multiple
- prior_average_monthly_net_profit
- prior_average_annual_net_profit

marketplace_observed_exits_v01：
仅包含见势真实连续观察到的 For Sale → Sold，不把“第一次见到时就已经 Sold”的历史挂牌误当成完整迁移。

marketplace_exit_benchmarks_v01：
按 monetization 汇总观察退出样本，包括：
- observed_exit_count
- median_last_asking_price_before_sold
- median_last_asking_annual_multiple_before_sold
- median_days_on_marketplace

## Collector
每 6 小时继续采集当前 For Sale。
同时采集最近 120 天的 Sold 结果，用官方 sold_at_from 查询过滤。

默认：
- API page size = 100
- active max pages = 5
- sold max pages = 5
- 官方 API <= 1 request/second

若 Sold 查询临时失败：
- 当前 For Sale 采集仍可 PASS
- quality gate = PASS_WITH_WARNINGS
- 不阻断主公开站当前数据
- 记录 sold_warning

## 产品用途
R7.7 初期先作为底层证据，不立即把小样本中位数包装成“市场估值”。

只有观察退出样本达到足够数量后，才在详情页展示类似：
“过去 N 个见势真实观察到的同类退出中，卖出前最后挂牌倍数中位数为 X。”

并持续标注：
“最后挂牌倍数 ≠ 实际成交倍数。”
