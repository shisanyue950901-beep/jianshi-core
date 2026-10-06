# 见势 R7.6｜Acquire 类交易市场数据源策略

## 结论
Acquire 类交易市场是见势最重要的“真实商业验证”数据层之一，但不能把“公开能看到”误认为“允许自动抓取并商业化再展示”。

生产规则继续保持：
- GREEN：允许生产自动采集 + 允许公开展示。
- YELLOW：研究价值高，但许可边界未完成；生产自动采集强制关闭。
- RED：条款明确禁止或风险不可接受；禁止生产自动采集和公开重展示。

## 2026-10-06 复核矩阵

| 数据源 | 状态 | 自动采集 | 公开展示 | 当前用途 |
|---|---|---:|---:|---|
| Empire Flippers | GREEN | 是 | 是 | 生产商业样本 |
| GitHub | GREEN | 是 | 是 | 生产技术趋势 |
| Acquire.com | RED | 否 | 否 | 人工市场研究 / 等书面授权 |
| Flippa | RED | 否 | 否 | 人工研究 / 等许可 |
| Microns | RED | 否 | 否 | 人工研究 / 等许可 |
| DealSlide | RED | 否 | 否 | 人工研究 |
| TrustMRR | YELLOW | 否 | 否 | API 许可沟通 |
| CatchBuys | YELLOW | 否 | 否 | API 条款 + 上游再许可权核验 |
| AcquireBase | YELLOW | 否 | 否 | 书面许可沟通 |
| SideProjectors | YELLOW | 否 | 否 | Terms/API 专项复核 |

## Acquire.com
2026-03-18 Buyer & Seller Terms 明确禁止：
- automated/manual scraping or data extraction
- automatic queries / spiders / robots / crawlers
- 跨域 repost / display listing information
- 使用服务构建竞争产品
除非 Acquire.com 书面明确许可。

因此见势不得通过：
- 直接爬 Acquire
- 登录后批量抓取
- 浏览器自动化绕过
- 从页面复制成自己的交易数据库

Acquire 仍可以作为：
- 产品研究参考
- 数据字段设计参考
- 许可/合作目标
- 发现某个公开商业方向后，再去独立合法来源验证该方向

## CatchBuys
优点：
- 官方提供 REST API
- 约 30 个商业交易市场聚合
- 页面明确把 data products、newsletter、deal-flow tracker、alerts 列为目标用途
- 标准字段已经覆盖售价、MRR、收入、利润、multiple、年龄等

但当前仍为 YELLOW：
1. 完整 Terms 尚未完成可核验审查。
2. 需要确认 CatchBuys 对每个上游来源是否拥有向第三方产品再许可/再展示的权利。
3. 在书面确认前不能仅凭营销页面把它当成生产 GREEN 数据源。

## TrustMRR
官方 API/MCP 很有价值，且收入验证质量高。
但 Terms 明确：
- API key 不自动授予公开展示/再发布许可
- customer-facing product、public display、bulk export/republication 需要书面许可
- AI/search/recommendation 等使用也需要事先书面许可

所以当前 YELLOW，只做许可沟通，不接生产。

## 许可申请统一范围
给数据源方申请时一次问清楚以下五项：
1. AUTOMATED_API_OR_FEED
2. HISTORICAL_SNAPSHOT_STORAGE
3. DERIVED_ANALYTICS
4. PUBLIC_SUMMARY_DISPLAY
5. COMMERCIAL_PRODUCT_USE

即使对方批准，也不会自动把数据源改成 GREEN。
必须：
书面证据 → Policy Review → Registry 改状态 → Staging → Source Gate Test → Production。

## 推荐合作说明
> 我们正在开发「见势」，一个中文互联网商业机会与趋势情报平台。我们不会复制贵平台的完整 marketplace，也不会绕过登录、付费墙或私密信息。我们希望通过官方 API / feed 或书面授权，仅使用双方明确约定的字段，用于聚合趋势、历史变化和经过加工的商业分析，并始终保留来源与跳转链接。希望确认自动访问、历史快照、衍生分析、有限公开展示和商业产品使用的许可范围。

## 当前产品策略
近期不依赖 Acquire 抓取才能继续成长：
- Empire Flippers 继续作为 GREEN 商业事实源。
- GitHub 继续作为技术供给源。
- 通过更多官方/授权 API 增加独立证据。
- Acquire/TrustMRR/CatchBuys 等走合作授权路线。
- 不因为缺少某个市场数据就降低多源 Gate。
