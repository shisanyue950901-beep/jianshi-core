# P3.4 商业平台合作意向申请计划

日期：2026-10-07
状态：READY_FOR_REVIEW
前置条件：P3.3 产品框架已冻结

## 1. 合作目标

见势不是申请“抓取权”，而是申请成为面向中文创业者的机会发现入口。

标准合作价值链：

平台提供允许使用的有限公开字段
→ 见势做中文筛选、评分、结构化分析与用户教育
→ 用户在见势发现值得深入了解的项目
→ 点击回原平台查看原始 listing、联系卖家或继续交易

见势不承接交易，不镜像完整 listing，不替代原平台。

## 2. 第一波目标

### Acquire.com
优先级：P1

原因：
- 与见势“在线业务/Startup 机会发现”最接近
- 公开 listing 已有 asking price、行业、tech stack、匿名财务等适合机会发现的字段
- 有正式 Partner Program，说明其组织上存在合作入口
- 对见势长期品牌价值最高

目标：
先争取有限公开字段引用 + 聚合趋势 + attribution + deep link。
如果对方有官方 feed/API/partner arrangement，优先采用官方方式。

### Microns
优先级：P1

原因：
- Micro-SaaS / 小型在线业务与中国个人创业者高度匹配
- 官方明确区分 public details 与 private details
- 小团队、产品定位相近，合作沟通路径可能更灵活
- 已存在 partner/affiliate 思路，说明其对导流合作并不陌生

目标：
有限 public details + 项目类别/价格区间/公开经营信息 + attribution + 原站导流。
不要求 private details。

### Flippa
优先级：P1

原因：
- 样本量大
- 有 verified / vetted 等质量信号
- 有成熟 partner/broker 体系
- 可补充 Acquire / Microns 覆盖不足

目标：
先争取 selected public fields 和聚合统计，不要求镜像数据库。

## 3. 第二波目标

- Quiet Light
- StartupMKT
- FE International

进入条件：
第一波至少完成发送与首轮反馈分类，或第一波 7–10 个工作日无实质回复。

FE International 暂不放第一波，是因为其更偏成熟 M&A，和当前“个人创业者找项目”主用户的契合度略低。

## 4. 第一封邮件的最小请求

第一次沟通只问四件事：

1. 是否允许见势引用少量 public listing fields。
2. 是否允许把这些字段做 aggregate / trend analysis。
3. 是否允许清晰 attribution + link back 到原始 listing。
4. 如果允许，平台希望我们通过 API、feed、partner program 还是其他方式实现。

第一次邮件不主动要求：
- 完整数据库
- 私密财务
- NDA 后内容
- 卖家身份
- 联系方式
- 客户数据
- 数据室
- 批量导出
- 私有 API
- 独家授权

## 5. 希望获准的字段范围

优先级最高：
- category / business type
- public asking price 或 price range
- public revenue/profit figures 或 ranges
- public business model
- public tech stack
- public listing status
- public verification/vetting indicator
- source URL / listing URL

可选：
- public traffic / growth metrics
- public age / founded date
- public location
- public operational workload

永远不主动申请：
- seller identity hidden by platform
- private P&L / CIM
- buyer/seller contact data
- customer-level data
- NDA-only information
- private chat/messages
- verification documents

## 6. 我们向平台提供的价值

每封邮件都必须明确：

- 见势面向中文创业者和内容创作者
- 见势负责 discovery / education，不负责 transaction
- 不复制完整 listing
- 清晰展示来源
- 提供原始 listing deep link
- 目标是新增中文市场的高意向流量
- 愿意遵守字段限制、速率、缓存、归因和下架要求
- 现在处于验证阶段，所以希望从一开始就在平台允许的边界内建设

禁止夸大：
- 不虚构用户数
- 不虚构流量
- 不声称已有中国买家资源
- 不声称“官方合作”
- 不承诺交易量

## 7. 邮件语气

必须像真实产品创始人在询问合作，而不是工程师提交 API 权限表。

推荐开场：
- I’m building JianShi...
- We help Chinese individual entrepreneurs discover and evaluate online business opportunities...
- We’re currently validating the product and want to make sure we build within your preferred data boundaries from the start.

避免：
- V1/V2
- production gate
- source registry
- evidence class
- scope matrix
- scraping pipeline
- database mirror
- automated collector

这些只留在内部。

## 8. 产品说明标准版

英文短版：

JianShi (见势) is a Chinese-language opportunity discovery and decision platform for individual entrepreneurs and business content creators. We analyze public and licensed commercial, product and technical signals to help users discover business opportunities, compare them, and understand which ones are worth deeper research.

We are not an acquisition marketplace and we do not broker transactions. When we reference a marketplace case, our preferred model is a limited summary with clear attribution and a direct link back to the original platform.

## 9. 回复分类

收到回复后必须归入：

### APPROVED
明确批准所需使用范围。

### PARTIAL_APPROVAL
只批准部分字段、部分用途、聚合分析或导流。

### NEED_MORE_INFO
对方要求网站、字段清单、技术方案、流量、公司信息等。

### PARTNER_PROGRAM_ROUTE
对方要求走现有 partner/affiliate/business development 路径。

### PAID_LICENSE
对方提供付费数据许可。
不得直接购买，先评估价值并让用户确认。

### REJECTED
明确拒绝。

### NO_RESPONSE
无回复。

## 10. 收到同意后的内部流程

任何口头或邮件同意都不能直接开采集。

必须继续：

Written Reply
→ Policy Review
→ 明确批准字段与用途
→ Source Registry
→ Staging
→ Quality Gate
→ Publication Gate
→ Production

如果对方只允许 referral，不允许数据再利用，则只做 referral，不采数据。

## 11. 跟进节奏

建议：
- Day 0：首次邮件
- Day 5–7 个工作日：第一次简短 follow-up
- 再过 7 个工作日：最后一次 follow-up
- 之后停止主动追问，标记 NO_RESPONSE

Microns 这类小团队可稍微更自然，但不高频催促。

## 12. 成功标准

第一阶段不是“四家全同意”。

以下任一即可算 P3.4 有效进展：
- 1 家 PARTIAL_APPROVAL 以上
- 1 家进入正式 partner/data discussion
- 1 家明确告诉我们可接受的数据边界
- 1 家给出官方 feed/API/partner route

最理想结果：
Empire Flippers + 第二个合法商业来源
→ 开始真正的 Commercial-to-Commercial Cross Validation。

## 13. 第一波发送状态

当前先保持：
- Acquire.com = DRAFT_READY
- Microns = DRAFT_READY
- Flippa = DRAFT_READY
- FE International = HOLD_SECOND_WAVE

未经最终人工确认，不执行 Send。
