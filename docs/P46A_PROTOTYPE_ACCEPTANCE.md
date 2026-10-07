# P4.6A 具体创业机会详情样板 — Prototype Acceptance

日期：2026-10-07

## 结论

```
P46A_PR = OPEN_53
P46A_CI_INITIAL = FAIL_RUN_171_PATH_COLLISION
P46A_CI_FINAL = PASS_RUN_174

P46A_PROTOTYPE_COUNT = 2
P46A_VERTICAL_SAAS = PASS
P46A_AMAZON_FBA = PASS

P46A_CHINESE_USER_VIEW = PASS
P46A_DOMESTIC_OUTBOUND_SPLIT = PASS
P46A_DOUYIN = INCLUDED
P46A_XIAOHONGSHU = INCLUDED
P46A_BILIBILI = INCLUDED
P46A_WECHAT = INCLUDED
P46A_YOUTUBE = INCLUDED
P46A_TIKTOK = INCLUDED
P46A_SEO = INCLUDED

P46A_FACT_EDITORIAL_SEPARATION = PASS
P46A_ROBOTS = NOINDEX_NOFOLLOW
P46A_SEARCH_INDEX = NOT_INCLUDED
P46A_SITEMAP = NOT_INCLUDED

P46A_PRODUCTION_CHANGE = FALSE
P46A_FINAL = PASS_PROTOTYPE
```

## 首批两个样板

### 1. 垂直行业 SaaS

页面不再使用“Micro SaaS”作为用户标题。

结构包括：

- 当前判断
- 项目是什么
- 谁付费 / 怎么赚钱
- 当前真实商业证据
- 中国创业者适配
- 国内 / 出海路线
- 抖音 / 小红书 / B站 / 知乎 / 公众号
- YouTube / TikTok / SEO / LinkedIn
- 第一轮验证动作
- 风险和当前未知

关键产品语义：

`国内内容热度 != 海外购买需求`

`CONTENT_ATTENTION != PURCHASE_INTENT`

### 2. Amazon FBA 细分品牌

结构强调：

- 中国创业者可以研究供应链优势，但不能把供应链接近度直接等同于竞争优势；
- 抖音 / 小红书 / B站主要承担中国侧研究、内容和供应链表达；
- 海外真实需求需要结合 Amazon 站内搜索、评价、竞争和实际转化；
- YouTube / TikTok 可以作为海外内容与达人测试渠道，但播放量不等于购买转化；
- FBA 明确作为有库存、现金流、平台规则和合规风险的业务，而不是轻资产机会。

## 事实与编辑建议分层

样板页面使用两个不同层级：

### 事实证据

来自当前公开商业数据快照，例如：

- 直接商业样本数量
- 样本识别规则
- 公开 niche
- 商业来源多样性
- 快照日期

### 编辑建议

包括：

- 国内 / 出海路线
- 渠道建议
- 第一轮验证动作
- 当前适配判断

页面不会把编辑建议伪装成来源已经证明的事实。

## CI 首次失败说明

CI #171 并非页面功能失败。

根因：

仓库根目录 `content/` 是静态构建生成目录；已有测试运行 build 时会清空并重新生成该目录，导致放在其中的原始 prototype JSON 在后续测试执行前被删除。

修复：

原始编辑数据迁移到：

`config/p46a_concrete_opportunity_prototypes.json`

CI #174 最终 PASS。

该修复也冻结了新的工程规则：

> 生成目录不得存放构建输入源文件。

## 当前发布边界

P4.6A 不上线。

两个页面：

- robots = noindex,nofollow
- 不加入 sitemap
- 不加入站内 search index
- PR #53 保持 OPEN
- Production 无修改

因此可以继续编辑和验收页面内容，而不会让半成品直接进入真实用户环境。

## 下一小步

建议 P4.6B 只增加下一批 3 个：

1. 联盟营销 / 内容站
2. YouTube 垂直媒体资产
3. 数字产品业务

继续沿用 P4.6A 模板，尤其强化：

- 中文用户视角；
- 抖音 / 小红书 / B站 / 微信；
- YouTube / TikTok / SEO；
- “内容平台”与“真实商业渠道”的区别；
- 事实与编辑判断分离。

不建议一次做完剩余 6 个。
