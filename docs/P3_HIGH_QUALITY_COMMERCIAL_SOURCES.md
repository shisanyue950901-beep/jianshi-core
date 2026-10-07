# P3 高质量商业数据源层（Acquire 标杆）

日期：2026-10-07

## 冻结目标

P3 不追求“数据源数量最多”，而追求**高质量真实商业市场**。

核心判断：

> GitHub 解释“大家正在造什么”；高质量交易市场解释“哪些方向已经变成真实生意”。

质量分层只决定授权投入优先级，**不决定是否允许采集**。任何来源只有在 Source Policy 明确允许后才能进入自动采集和公开展示。

## 当前优先级

| 优先级 | Tier | 来源 | 当前生产权限 | 角色 |
|---:|:---:|---|---|---|
| 1 | S | Empire Flippers | GREEN / 已接入 | 现有商业证据基线 |
| 2 | S | Acquire.com | RED / 需书面许可 | 首要新增目标 |
| 3 | S | FE International | RED / 需书面许可 | 专业 M&A 高质量样本 |
| 4 | A | Flippa | RED / 需书面许可 | 大样本 + Data Verified/Vetted |
| 5 | A | Microns | RED / 需书面许可 | Micro-SaaS / 一人公司高匹配 |
| 6 | A | Investors Club | YELLOW / 权利未明确 | 盈利在线业务补充 |
| 7 | B | Motion Invest | YELLOW / 权利未明确 | 内容站 / YouTube 补充 |

FoundersPrime、AcquireBase、SideProjectors 等仍保留在 Source Registry，但不进入本轮高质量首批授权队列；聚合器也不能绕过上游来源限制。

## 2026-10-07 官方条款实时复核

### Acquire.com

Buyer & Seller Terms 明确禁止未经书面许可的数据抓取/提取、自动查询、跨域重新展示，以及用于构建竞争产品。Acquire 官方同时存在 Partner Program，因此本轮首选路径是**直接询问授权数据 feed / API / partner licensing**，而不是爬网页。

联系人：support@acquire.com / Partner Program。

### FE International

2026 Platform Terms 明确禁止未经 express written permission 的 benchmarking / competitive intelligence 以及 scraping / crawling / harvesting / extraction。

联系人：support@feinternational.com / fecapitalinfo@feinternational.com。

### Flippa

Terms of Service 明确规定：未经 express written consent，不可使用 data mining、robots 或类似工具提取 substantial parts，也不可建立/发布包含 substantial parts 的自有数据库。

联系人：support@flippa.com；另有官方 partnership contact。

### Microns

官方 Policy 明确写明：未经 express permission，不可 crawl / scrape / spider Services 页面。

联系人：support@microns.io。

### Investors Club

官方 Terms 保留网站技术和数据权利，并限制自动化复制；未找到清晰的第三方商业聚合/再发布许可，因此保持 YELLOW。

### Motion Invest

官方 Terms 说明平台及内容为其专有资产，但未找到公开 API、自动采集、历史存储或商业再发布许可，因此保持 YELLOW。

## 五项统一授权范围

所有外部申请都请求同一组 scope：

1. AUTOMATED_API_OR_FEED
2. HISTORICAL_SNAPSHOT_STORAGE
3. DERIVED_ANALYTICS
4. PUBLIC_SUMMARY_DISPLAY
5. COMMERCIAL_PRODUCT_USE

任何“可以浏览/可以注册/可以买家会员”都不等于以上五项授权。

## Production Gate

即使收到回复，也必须继续走：

Written Reply → Policy Review → Source Registry → Staging → Quality Gate → Publication Gate → Production

禁止：

- 直接抓 Acquire / FE / Flippa / Microns
- 绕 CAPTCHA / 登录墙 / NDA
- 把 FoundersPrime 等聚合 API 当成上游授权替代品
- 把 listing asking price 当作成交价
- 把 Sold 状态当作真实成交价格或转化率

## P3 当前执行状态

- 高质量来源分层：已建模
- 最新条款审计：已更新
- Acquire / FE 既有 DRAFT：保留并升级优先级
- Flippa / Microns：补建授权 DRAFT
- Production 自动采集：保持关闭
- 下一动作：审核并发送首批授权邮件
