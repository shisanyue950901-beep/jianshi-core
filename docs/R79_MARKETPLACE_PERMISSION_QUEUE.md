# 见势 R7.9｜交易市场合作授权队列

## 新增候选
### FE International — RED
官方 2026 Marketplace Terms 明确禁止：
- benchmarking / competitive intelligence
- automated/manual scraping
- crawl / harvest / extract Marketplace 数据
除非书面许可。

因此只保留合作目标，不进入自动采集。

### Investors Club — YELLOW
优点：
- 公开挂牌覆盖 SaaS、电商、内容、服务等
- 有 Asking Price、Annual Net Profit、Profit Multiple 等字段
- 自身维护 price/listing history

风险：
- Terms 将平台 Content 视为专有内容
- 没找到允许第三方商业聚合、历史存储和再发布的公开授权

因此必须拿书面许可。

### Motion Invest — YELLOW
优点：
- 小型网站、内容站、YouTube 资产很适合“一人公司/内容资产”研究
- 公开展示月收入、流量、售价、变现方式

风险：
- 未发现公开 API
- Terms 保留平台内容/IP 权利
- 未发现商业再利用授权

因此必须拿书面许可。

## 统一申请内容
我们不会申请“完整复制 Marketplace”。

我们申请五项最小许可：
1. AUTOMATED_API_OR_FEED
2. HISTORICAL_SNAPSHOT_STORAGE
3. DERIVED_ANALYTICS
4. PUBLIC_SUMMARY_DISPLAY
5. COMMERCIAL_PRODUCT_USE

推荐字段最小化：
- source listing id
- category / monetization
- asking price
- revenue / profit where permitted
- multiple where permitted
- status
- first listed / updated / sold status where permitted
- source URL

默认不需要：
- seller identity
- private buyer/seller messages
- NDA data
- confidential URLs
- uploaded deal-room documents

## 英文合作邮件模板

Subject: Data/API partnership request from JianShi — Chinese business opportunity intelligence platform

Hello {{Partner}} team,

We are building JianShi (见势), a Chinese-language business opportunity and trend intelligence platform.

Our product does not aim to clone or replace your marketplace. We help Chinese founders, creators, and small teams understand market patterns through source-attributed summaries, historical changes, and derived analytics, while sending qualified users back to the original marketplace.

We would like to ask whether you can provide an official API, feed, affiliate data feed, or written permission for a limited set of public listing fields.

The permissions we would like to clarify are:

1. Automated API/feed access
2. Historical snapshot storage of permitted fields
3. Derived and aggregated analytics
4. Limited public display of summary fields with source attribution and outbound links
5. Use inside a commercial subscription intelligence product

We do not need seller identities, private messages, NDA-protected information, confidential URLs, or deal-room documents.

If helpful, we can also:
- respect a custom rate limit,
- cache rather than repeatedly request data,
- display your marketplace as the original source,
- link every relevant record back to your marketplace,
- remove fields you do not want redistributed,
- follow an approved attribution format.

Could you let us know whether an existing API/feed/partner program fits this use case, or what permissions you would require?

Best regards,
JianShi / 见势
看见正在发生的生意机会

## 转 GREEN 流程
书面回复/合同
→ 记录 approved_scopes
→ Policy Review
→ source_registry 改 GREEN
→ Staging Collector
→ 数据质量 Gate
→ 公开展示 Gate
→ Production

任何一步未完成，都保持 fail-closed。
