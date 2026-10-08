# P4.12C｜首批两份具名海外项目档案——内部证据审核

状态：TWO_PROFILES_DRAFTED / PUBLICATION_BLOCKED  
核查日：2026-10-08

## 目的与禁区

这是从六种商业模式指南走向具体项目信息产品的第一步，**不是继续扩充匿名挂牌样本数**。

现有业务分类和匿名挂牌样本并没有可可靠直接关联的企业名，因此不得将匿名样本（含财务中位数）拼接成具名项目档案。具名项目只能使用独立核对的第一方产品、本人官方资料及可靠平台事实。财务真实性需要更高门槛，不能从标价、宣称或商品存在推导净利。

正式上线前仍须处理 Cloudflare Pages 只发布构建产物、历史部署与缓存的遗留安全事项。样板只位于 P4.12 设计分支，绝不合并 Production main。

## 案例一：Easlo｜数字效率模板

用户可读的确定事实：

- Easlo 有独立模板商品目录，提供不同用途的工作和生活模板，包括免费与付费选项；
- Notion 官方模板市场存在 Easlo 具名创作者页面及模板清单；
- 其业务形式属于“数字产品 / 模板商品”。

内部核对资料：

- **EASLO_OWN_SITE_01**：项目自营商品目录 `https://www.easlo.co/templates`：列表中有 Second Brain、Freelance OS 等产品与价格信息；可确认商品展示与价格标签，但不能证明实际成交；
- **EASLO_NOTION_02**：Notion 官方创作者页 `https://www.notion.com/templates/creators/easlo`：可确认创作者与模板关联，可看到公开市场上的免费与付费模板；
- 可选背景（**未纳入经营数字口径**）：本人早期在 Indie Hackers 的自述，属于历史自报业绩，没有完整审计证据，不作为当前收入基线。

本轮不得对外断言：

- 目前每月收入、利润、销量、转化率、退款率；
- 仍由一个人运营或者确定员工人数；
- 模板标价就是作者最终实收；
- 所有销售都来自 Notion 官方市场。

审核结论：

```
PRODUCT_EXISTENCE = VERIFIED
PAID_OFFER = OBSERVED
CREATOR_LINK = VERIFIED_PLATFORM
TRANSACTIONS = NOT_VERIFIED
FINANCIALS = NOT_VERIFIED
TEAM_SIZE = UNKNOWN
```

## 案例二：Louise Lennox｜爱情小说出版

用户可读的确定事实：

- 作者的自有官网介绍了作品和图书系列；
- 亚马逊官方 2022 年作者故事文章明确提及她选择使用 Kindle 直接出版；
- 作者官网有纸质书商品陈列，不代表全部为 Kindle 直接出版。

内部核对资料：

- **LENNOX_AUTHOR_01**：作者作品目录 `https://www.authorlouiselennox.com/books`；
- **LENNOX_AMAZON_02**：亚马逊作者专题 `https://www.aboutamazon.com/news/books-and-authors/how-these-authors-found-success-with-amazon-kindle-direct-publishing`；
- **LENNOX_SHOP_03**：作者自有商店 `https://www.authorlouiselennox.com/shop`。

本轮不得对外断言：

- 现有全部书籍均通过 KDP 发行；
- 2022 年作者采访中的历史描述等于 2026 年经营状况；
- 具体 KDP 版税、利润、销量、团队和投入；
- 小说主题、上架方式可复制出相同商业结果。

审核结论：

```
AUTHOR_IDENTITY = VERIFIED_BY_AUTHOR_SITE
BOOK_CATALOG = VERIFIED
KDP_EXPERIENCE = ATTESTED_BY_PLATFORM
SELLING_OFFER = OBSERVED
ROYALTIES = NOT_VERIFIED
NET_PROFIT = NOT_VERIFIED
```

## 出版权限边界

### 可以进入样板界面

- 项目品牌/创作者名，用户需要知道具体是谁；
- 其公开产品、客户群、基本收费模式；
- 用平实中文表示的确认事实及未知信息；
- 名称与业务类型关系的解释。

### 不进入样板的内容

- 任何受保护的商业挂牌供应商、原始挂牌标题、挂牌编号、采集渠道、内部 source_ref；
- 内部第三方数据映射规则、数据库接口、审计代码或编辑记录；
- 独立来源 URL；确需公开的链接后续必须通过产品层脱敏/权利审核，且仅允许项目自身官网，不允许暴露受保护的项目发现和采集渠道；
- 无独立证据的收入/利润/团队/预计 ROI。

## 下阶段扩展依据

现在有 2 个具名案例，不代表所有 6 种类别都已有真实公司档案。下一步是对其余四类按同标准寻找并核对真实企业；当信息不足时保持商业模式指南，不用虚构项目补齐卡片数量。

## 验收

```
P412C_NAMED_PROFILES = 2
P412C_NAMED_CASE_CLASSIFIED_AS_MARKETPLACE_RECORD = FALSE
P412C_BUSINESS_OFFER_VERIFIED = TRUE
P412C_ACTUAL_SALES_VERIFIED = FALSE
P412C_FINANCIALS_VERIFIED = FALSE
P412C_PUBLIC_SOURCE_PROVIDER_LEAK = FALSE
P412C_PRODUCTION_PUBLICATION = FALSE
P412C_CLOUDFLARE_ROOT_FIX = PENDING
```
