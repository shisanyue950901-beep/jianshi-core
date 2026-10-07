# P4.7C 中文优先命名与两个新增项目详情页 — 验收

日期：2026-10-07

## 结论

```
P47C_NEW_PROTOTYPES = 2
P47C_TOTAL_PROTOTYPES = 6

P47C_AMAZON_KDP = PASS
P47C_VERTICAL_SERVICE = PASS

P47C_CHINESE_FIRST_NAMING = PASS
P47C_CANDIDATE_POOL_CHINESE_FIRST = PASS

P47C_PROTOTYPE_CI = PASS_RUN_190
P47C_NAMING_CI = PASS_RUN_191

P47C_PUBLIC_INDEXING = FALSE
P47C_PRODUCTION_DATA_CHANGE = FALSE

P47C_FINAL = PASS_PROTOTYPE
```

## 中文优先规则

用户可见内容默认：

> **能自然中文表达的概念全部中文化。**

只有两类英文保留：

1. 官方品牌名；
2. 确有识别或检索价值的行业缩写。

例如：

- 软件订阅服务（SaaS）
- 亚马逊物流（FBA）
- 应用程序（App）
- 亚马逊按需印刷（Amazon Merch）
- 无货源代发（Dropshipping）
- 邮件订阅媒体（Newsletter）

内部：

- slug
- 数据库字段
- API 字段
- 工程状态

可以继续使用英文，不对普通用户展示。

## 本阶段新增两个详情页

### 亚马逊 KDP 数字出版

严格证据：

- active listing
- 主标题明确为 Amazon KDP Business
- 按 listing 去重
- 直接商业样本 = 8
- 商业来源多样性 = 1

当前推荐：

`优先研究`

### 垂直服务型业务

严格证据：

- active listing
- 主标题明确为 Agency Business
- 按 listing 去重
- 直接商业样本 = 4
- 商业来源多样性 = 1

页面不向中文用户展示“Agency Business”作为主标题。

当前推荐：

`优先研究`

## 当前六个详情样板

1. 垂直行业软件订阅服务（SaaS）
2. 亚马逊物流（FBA）细分品牌
3. 数字产品业务
4. 联盟营销 / 内容站
5. 亚马逊 KDP 数字出版
6. 垂直服务型业务

全部继续使用统一六问模板：

1. 项目是什么
2. 海外有没有真实验证
3. 为什么值得中国用户看
4. 适合什么样的中国个人创业者
5. 第一轮怎么验证
6. 风险和未知

## 发布边界

仍然：

- noindex,nofollow
- 不进入 sitemap
- 不进入站内搜索索引
- 不修改正式机会评分
- 不修改 Production 商业数据
- 不接新数据源
