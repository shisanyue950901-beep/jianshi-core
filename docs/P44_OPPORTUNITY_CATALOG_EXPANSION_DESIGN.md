# P4.4 机会目录扩容设计

日期：2026-10-07  
状态：DESIGN_FROZEN_NO_PRODUCTION_CHANGE

## 1. 主线校正

当前产品主线不是继续增加技术数据源，而是把“用户真正能看懂并做决策的创业机会”做出来。

现有 6 个 Opportunity：

- 一人公司 SaaS
- AI Agent 工具与自动化
- LLM 应用与工具
- 轻量电商品牌与 Amazon 资产
- 创作者媒体资产
- 联盟营销与内容资产

不删除。

它们从现在开始更准确地定义为：

> **母赛道 / Evidence Aggregation Track**

作用：
- 聚合 GitHub / Marketplace 等证据；
- 提供宏观四维评分；
- 作为子机会的证据背景。

真正面向用户的产品单元逐步变成：

> **Concrete Opportunity / 具体创业机会**

例如：

`创作者媒体资产 → YouTube 垂直媒体 / Newsletter 订阅媒体 / 数字产品业务`

## 2. 最重要的证据规则

母赛道有商业证据，不代表所有子机会自动获得商业验证。

冻结：

```
PARENT_EVIDENCE = CONTEXT
CHILD_VALIDATION = CHILD_SPECIFIC_EVIDENCE_REQUIRED
PARENT_PUBLIC_READY != CHILD_PUBLIC_READY
```

例如：

“solo-saas” 当前有 Marketplace SaaS 样本，并不能直接证明“邮件营销 SaaS”一定已经获得商业验证。

子机会在进入“已验证”状态前，必须建立更精确的证据映射。

这条规则用于防止为了扩充项目数量而产生伪精确。

## 3. Production 当前真实基础

现有 6 个母赛道 Evidence：

- affiliate-content：GitHub 34 + Marketplace 16
- ai-agent-tools：GitHub 50
- creator-media：GitHub 100 + Marketplace 33
- ecommerce-brands：GitHub 50 + Marketplace 107
- llm-tools：GitHub 50
- solo-saas：GitHub 50 + Marketplace 6

当前 Empire 活跃 Marketplace monetization 中：

- Amazon FBA：77
- eCommerce：52
- YouTube：16
- Digital Product：15
- Subscription：14
- Display Advertising：12
- Amazon KDP：11
- Affiliate：10
- Amazon Associates：8
- Service：8
- DropShipping：7
- Agency：6
- SaaS：6
- Newsletter：2
- Lead Gen：1

当前 GitHub 证据还明确出现：

- Referral / Affiliate Platform
- AI 电商视频生成
- AI 求职/职位匹配
- Firecrawl / AI Web Data
- Listmonk / BillionMail
- Medusa / Saleor / Spree / Bagisto
- Open SaaS / OSS SaaS alternatives

因此已有数据足够先做第一轮“具体机会编辑”，不需要继续接新 API 才能开始。

## 4. 第一批 16 个具体机会候选

### A 组：优先进入编辑审查

1. **垂直行业 Micro SaaS**
   - 母赛道：solo-saas
   - 当前基础：Marketplace SaaS + GitHub SaaS
   - 注意：需要进一步细化具体行业，不允许直接继承母赛道全部商业样本。

2. **联盟营销 / SEO 内容站**
   - 母赛道：affiliate-content
   - Marketplace：Affiliate / Display Ads / Amazon Associates
   - GitHub：affiliate-marketing
   - 当前证据较强。

3. **Amazon FBA 细分品牌**
   - 母赛道：ecommerce-brands
   - Marketplace 当前有大量直接 Amazon FBA 样本。
   - 当前商业证据最明确的具体项目之一。

4. **YouTube 垂直媒体资产**
   - 母赛道：creator-media
   - Marketplace YouTube + GitHub YouTube。
   - 适合创业者与创作者双视图。

5. **数字产品业务**
   - 母赛道：creator-media
   - Marketplace Digital Product 有直接商业样本。

6. **Newsletter 订阅媒体**
   - 母赛道：creator-media
   - Marketplace Newsletter / Subscription + GitHub Newsletter。
   - 直接 Newsletter 样本数量较少，编辑时必须展示这一限制。

7. **Amazon KDP 数字出版**
   - 母赛道：affiliate-content
   - Marketplace 有直接 KDP 商业样本。

8. **跨境 DTC / 独立站品牌**
   - 母赛道：ecommerce-brands
   - Marketplace eCommerce 样本丰富。
   - 后续需要排除纯 Amazon FBA，避免重复计数。

### B 组：研究候选，暂不称“已验证”

9. **推荐 / 联盟营销 SaaS**
   - GitHub 有 RefRef 等技术供给。
   - 需要子类商业证明。

10. **邮件营销 / Newsletter SaaS**
    - GitHub 有 Listmonk / BillionMail。
    - Marketplace 有 SaaS 母类，但尚未证明就是邮件营销 SaaS。

11. **AI 电商短视频生成工具**
    - GitHub 出现 TikTok ecommerce video generation 工具。
    - 当前只有技术信号。

12. **AI 求职 / 简历 / 职位匹配助手**
    - GitHub 出现较强 AI job-search agent。
    - 当前只有技术信号。

13. **AI 网页研究 / 数据采集工具**
    - Firecrawl / Agent-Reach 等技术证据较强。
    - 当前没有对应商业证明。

14. **中小企业 Agent 工作流自动化**
    - AI Agent 母赛道技术供给很强。
    - 仍过宽，进入编辑前需拆出具体业务任务。

15. **开源 SaaS 替代 / 私有部署工具**
    - GitHub 有 OSS SaaS alternatives / Open SaaS 生态。
    - 商业需求需进一步验证。

16. **无头电商 / 电商基础设施工具**
    - Medusa / Saleor / Spree / Bagisto 等供给明显。
    - 更偏开发者/B2B，需要验证中国个人创业者是否适合。

## 5. 第一批真正做内容的项目

下一阶段不一次做 16 个。

只做第一批 8 个：

1. 垂直行业 Micro SaaS
2. 联盟营销 / SEO 内容站
3. Amazon FBA 细分品牌
4. YouTube 垂直媒体资产
5. 数字产品业务
6. Newsletter 订阅媒体
7. Amazon KDP 数字出版
8. 跨境 DTC / 独立站品牌

理由：

- 当前数据里有较直接的商业证据；
- 对普通创业者比 Agent Framework / Python package 更容易理解；
- 能覆盖软件、内容、媒体、电商、数字产品，而不是继续 AI 单一化；
- 更适合测试真实用户到底对哪种创业方式感兴趣。

## 6. 用户详情页结构

具体 Opportunity 的用户内容固定回答：

1. 这是什么项目
2. 谁会买单
3. 怎么赚钱
4. 为什么现在值得看
5. 当前有什么真实商业证据
6. 一个人是否适合
7. 中国创业者怎么做
8. 国内做还是出海
9. 最小验证动作
10. 获客从哪里开始
11. 最大风险
12. 当前不知道什么
13. 最终判断：值得做 / 值得研究 / 继续观察

禁止为了内容完整而虚构：
- 开发成本
- 开发周期
- 收入
- 用户量
- 转化率

## 7. 当前阶段冻结

```
CURRENT_STAGE = REAL_USER_VALIDATION
EXISTING_6_OPPORTUNITIES = PARENT_TRACKS
USER_FACING_DIRECTION = CONCRETE_OPPORTUNITIES

CANDIDATE_COUNT = 16
FIRST_EDITORIAL_BATCH = 8

NEW_SOURCE_EXPANSION = PAUSED
PYPI_PRODUCTION = PAUSED
HUGGING_FACE = PAUSED
BIGQUERY = PAUSED

PARENT_EVIDENCE_INHERITANCE = CONTEXT_ONLY
CHILD_VALIDATION_REQUIRES_CHILD_EVIDENCE = TRUE

PRODUCTION_CHANGE = FALSE
PUBLIC_SITE_CHANGE = FALSE
```

## 8. 下一小步

下一阶段只做 **第一批 8 个机会的“证据映射审计”**。

目的不是写漂亮文案，而是逐一确认：

- 哪些 Marketplace listing 真正属于这个具体机会；
- 哪些 GitHub repo 真正属于这个具体机会；
- 哪些只有母赛道证据；
- 哪些足够进入“值得做/值得研究”；
- 哪些必须保持“继续观察”。

证据映射通过后，再开始真正写用户能看到的详情页。
