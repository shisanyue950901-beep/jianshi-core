# P4.8A 真实用户测试入口

日期：2026-10-07  
状态：IMPLEMENTING

## 目标

把已经发布但没有自然入口的 6 个“海外已验证项目中文研究页”真正接入公开产品路径，让中国用户可以：

1. 从首页直接发现具体项目；
2. 在机会库先看具体项目，再看宽泛趋势；
3. 在一个详情页底部继续比较其他项目；
4. 用现有第一方匿名行为分析观察真实阅读与继续探索行为。

本阶段不扩数据源、不改 OPP_V0.2、不改 Production 数据库结构、不开放 Auth、不合并 PR #52。

## 发布前真实问题

PR #53 合并后，6 个详情页已经可以直接访问，但：

- 首页没有任何一个新项目入口；
- /opportunities/ 仍只有旧的 6 个宽泛趋势方向；
- 新详情页没有“继续比较其他项目”的自然路径；
- 因此现有行为数据无法回答真实用户是否会主动选择这些具体项目。

这属于产品导航断层，不是数据缺失。

## P4.8A 产品调整

### 首页

首页第一层改成：

> 海外已验证项目 → 商业证据 → 中国适配 → 低成本验证

首屏之后直接展示首批 6 个具体项目。

旧四维评分与趋势榜单保留，但明确降级为“趋势观察 / 辅助信号”，不再与具体创业项目混为一层。

### 机会库

/opportunities/ 分成两层：

1. 首批项目研究
2. 趋势方向 · 辅助观察

首批项目卡直接展示：
- 推荐档位
- 一句话项目说明
- 直接商业样本数量
- 商业来源种类
- 一人公司适配判断

### 详情页

每个首批项目详情页底部增加“继续比较”，优先展示另外 3 个项目，降低看完单页后直接离开的概率。

## 搜索与公开边界

6 个详情页继续保持：

- robots = noindex,nofollow
- 不写入 sitemap
- 不写入 search-index.json

它们可以通过站内正常链接被真实测试用户访问，但当前不主动进入搜索引擎公开索引。

## 行为分析

复用 P4.3 已上线的第一方匿名事件，不新增表：

- PAGE_VIEW
- OPPORTUNITY_CARD_CLICK
- OPPORTUNITY_DETAIL_VIEW
- SECOND_OPPORTUNITY_VIEW
- ENGAGED_30S
- SCROLL_50
- SCROLL_90

新项目 slug 已天然满足现有 currentSlug() 合同，因此不需要新增 Edge Function 事件类型。

## 首轮观察指标

只观察新 6 个项目：

1. 项目入口点击率  
   首页 / 机会库中进入新详情页的 session 占比。

2. 30 秒阅读率  
   新详情页 ENGAGED_30S / OPPORTUNITY_DETAIL_VIEW。

3. 深读率  
   新详情页 SCROLL_90 / OPPORTUNITY_DETAIL_VIEW。

4. 第二项目浏览率  
   看过至少一个新项目后继续查看第二个不同项目的 session 占比。

第一轮先积累真实基线，不预设“漂亮数字”。在至少 30 个新项目详情 session 前，不根据小样本重做产品；目标测试池仍是 P4.3 冻结的第一批 100–500 个精准真实访客。

## 测量 Epoch

正式发布 P4.8A 后才开启新的 USER_TEST_EPOCH。

Epoch 之前的行为事件包括开发、验收和内部访问，不作为真实用户结论依据。

## 不改变

- OPP_V0.2
- Source Policy
- SAMPLE_COUNT != SOURCE_DIVERSITY
- ASKING_PRICE != SOLD_PRICE
- ONE_PERSON_FIT = EDITORIAL_SCREENING
- Production Auth Gates
- PR #52
- 6 个详情页 noindex 边界
