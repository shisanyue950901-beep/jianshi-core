# P4.5A 第一批 8 个具体机会 — 真实证据审计

日期：2026-10-07  
状态：EVIDENCE_AUDIT_FROZEN_NO_PRODUCTION_CHANGE

## 1. 本阶段只回答一个问题

现有 Production 数据里，哪些证据可以**直接**支持第一批 8 个具体创业机会？

本阶段不做：
- 自动映射规则上线；
- 创建子 Opportunity；
- 改评分；
- 改 public_ready；
- 改前台；
- 新增数据源。

## 2. 审计原则

### 样本数不等于来源数

当前活跃 Marketplace 数据全部来自：

`empire_flippers`

因此：

- 77 条 Amazon FBA 样本 = 77 个直接商业样本；
- 但商业来源多样性仍然 = 1。

冻结：

```
DIRECT_SAMPLE_COUNT != SOURCE_DIVERSITY
SINGLE_SOURCE_DIRECT_PROOF != MULTI_SOURCE_VALIDATION
```

当前任何一个子机会都不能因为 Empire 样本多，就直接标成“高置信度多源验证”。

### 父级证据不能自动继承

母赛道的 Evidence 只能做 Context。

例如：
- ecommerce GitHub query ≠ Amazon FBA 技术证据；
- newsletter GitHub topic ≠ Newsletter 媒体商业收入证据；
- SaaS 母赛道商业样本 ≠ 某个具体 Micro SaaS 模式已经被验证。

### 不同创业类型不能强制使用同一验证模型

软件机会与内容/电商机会的证据结构不同。

**SOFTWARE**
需要：
- child-specific commercial proof
- child-specific technical supply

**CONTENT_ASSET**
重点需要：
- direct commercial proof
- 第二独立来源或等价交叉证据

不强制 GitHub。

**COMMERCE_ASSET**
重点需要：
- direct commercial proof
- 第二独立来源或等价交叉证据

不强制 GitHub。

因此未来子机会不能机械复制母赛道的 `TECHNICAL_SUPPLY + COMMERCIAL_PROOF` 模型。

## 3. Production 真实直接样本

独立规则计数，允许一条 listing 同时支持多个不同机会；这不是来源多样性。

| 具体机会 | Empire 直接样本 | GitHub 现有相关 Query | 审计结论 |
|---|---:|---:|---|
| 垂直行业 Micro SaaS | 6 SaaS | 50 SaaS repos | 中等直接证据，但“Micro”不受支持 |
| 联盟营销 / SEO 内容站 | 11 内容站 | 34 Affiliate repos | 商业证据较强，但“SEO”不适用于全部样本 |
| Amazon FBA 细分品牌 | 77 | 无 child-specific query | 商业直接证据很强 |
| YouTube 垂直媒体资产 | 16 | 50 YouTube repos | 商业直接证据较强 |
| 数字产品业务 | 15 | 无 | 商业直接证据较强 |
| Newsletter 订阅媒体 | 2 | 50 Newsletter repos | 有直接证据，但商业样本偏少 |
| Amazon KDP 数字出版 | 11 | 无 | 商业直接证据较强 |
| 跨境 DTC / 独立站品牌 | 24 非 Amazon eCommerce | 50 eCommerce repos | 有商业样本，但“跨境/DTC/独立站”无法从现有字段确认 |

## 4. 逐项审计

### 4.1 垂直行业 Micro SaaS

直接商业证据：
- 6 条 active SaaS listing；
- 样本存在 Business、SEO、Legal、News & Education / Travel 等不同 niche。

技术背景：
- GitHub `saas` query 当前 50 repos。

问题：
- 现有数据能证明“不同垂直 niche 存在 SaaS 商业资产”；
- 不能证明这些业务是通常意义上的“Micro SaaS”；
- 50 个 GitHub SaaS repo 也没有按垂直行业做 child-specific 分类。

因此发布前建议名称改为：

> **垂直行业 SaaS**

状态：

`RENAME_AND_WORTH_RESEARCH`

不能标记高置信度已验证。

### 4.2 联盟营销 / SEO 内容站

直接商业证据：
- 11 条 listing 同时满足：
  - title 中明确为 Site；
  - monetization 至少包含 Affiliate / Amazon Associates / Display Advertising 之一。

技术背景：
- affiliate_marketing GitHub query = 34 repos。

问题：
- 直接商业样本可以支持“联盟营销 / 内容站”；
- 不能证明全部样本主要依靠 SEO 获客；
- GitHub affiliate repo 更多是技术/营销工具背景，不能作为内容站收入证明。

建议名称改为：

> **联盟营销 / 内容站**

状态：

`RENAME_AND_WORTH_RESEARCH`

### 4.3 Amazon FBA 细分品牌

直接商业证据：
- Amazon FBA active listing = 77；
- 覆盖 Home、Beauty、Sports、Automotive、Pet Care、Supplements 等多个 niche。

这是第一批中直接商业样本最丰富的具体机会。

但：
- 77 个样本仍全部来自 Empire；
- 不能说“77 个独立来源验证”；
- 当前没有第二个合法商业平台证据。

状态：

`WORTH_RESEARCH`

不是 `WORTH_DOING`。

### 4.4 YouTube 垂直媒体资产

直接商业证据：
- YouTube listing = 16；
- niche 包括 Automotive、Sports、Entertainment、Travel、News & Education 等。

技术/生态背景：
- YouTube GitHub query = 50 repos。

GitHub 只能说明工具/生态供给，不直接证明频道商业表现。

状态：

`WORTH_RESEARCH`

### 4.5 数字产品业务

直接商业证据：
- Digital Product listing = 15；
- 覆盖 Business、Medical、Art、Design、Music 等 niche。

这类创业机会不需要为了“技术证据”强行找 GitHub repo。

状态：

`WORTH_RESEARCH`

### 4.6 Newsletter 订阅媒体

直接商业证据：
- Newsletter monetization listing = 2。

技术/生态背景：
- Newsletter GitHub query = 50 repos。

问题：
- 商业样本是直接的；
- 但当前样本数明显少于 YouTube / Digital Product / FBA；
- GitHub Newsletter 项目不能补足商业样本不足。

状态：

`WORTH_RESEARCH_LOW_CONFIDENCE`

页面以后必须明确显示“当前直接商业样本较少”。

### 4.7 Amazon KDP 数字出版

直接商业证据：
- Amazon KDP listing = 11。

这是明确的业务模式字段，不需要借 Affiliate 母赛道的其他商业样本来凑证据。

状态：

`WORTH_RESEARCH`

### 4.8 跨境 DTC / 独立站品牌

当前可直接识别：
- eCommerce；
- 排除 Amazon FBA / FBM 后 = 24 条 active listing。

这些样本能支持：

> **非 Amazon 电商品牌**

但现有字段不能确认：
- 是否跨境；
- 是否 DTC；
- 是否一定是独立站；
- 主要销售国家/渠道结构是否符合“跨境 DTC”定义。

因此原名称过度推断。

建议发布前改为：

> **非 Amazon 电商品牌**

状态：

`RENAME_AND_WORTH_RESEARCH`

## 5. 第一批最终判断

当前 8 个都可以继续进入“详情内容编辑候选”，但**没有一个应该直接标成“值得做”**。

原因不是它们没有商业证据，而是目前：
- 商业来源多样性仍只有 1；
- 中国创业者适配与执行难度尚未完成 child-specific 审查；
- 三个候选名称还存在证据语义过度扩张。

冻结：

```
WORTH_RESEARCH = 8
WORTH_DOING = 0
HIGH_CONFIDENCE_VALIDATED = 0
```

需要发布前改名：

1. 垂直行业 Micro SaaS → 垂直行业 SaaS
2. 联盟营销 / SEO 内容站 → 联盟营销 / 内容站
3. 跨境 DTC / 独立站品牌 → 非 Amazon 电商品牌

## 6. 自动化方向

P4.5A 是一次人工规则审计，不代表以后每次人工维护。

下一阶段 P4.5B 才把这些判断转为可执行规则：

```
Marketplace listing
→ structured rule
→ AUTO_MATCH
→ confidence
→ child evidence
→ exception review queue
```

例如：

`monetizations contains Amazon FBA → amazon-fba-niche-brand`

这种高确定规则以后可以全自动执行。

但 P4.5A 不上线自动规则。

## 7. 当前冻结

```
P45A_DIRECT_COMMERCIAL_SOURCE = EMPIRE_FLIPPERS_ONLY
P45A_COMMERCIAL_SOURCE_DIVERSITY = 1

P45A_CHILDREN_AUDITED = 8
P45A_WORTH_RESEARCH = 8
P45A_WORTH_DOING = 0
P45A_HIGH_CONFIDENCE_VALIDATED = 0

P45A_RENAME_REQUIRED = 3

P45A_AUTO_MAPPING = NOT_ENABLED
P45A_PRODUCTION_CHANGE = FALSE
P45A_PUBLIC_SITE_CHANGE = FALSE
```

下一小步：
**P4.5B：只设计并 Staging 验证自动 Evidence Mapping Rule，不改前台、不自动发布。**
