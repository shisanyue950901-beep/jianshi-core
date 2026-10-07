# P4.3 真实用户行为验证

日期：2026-10-07
状态：IMPLEMENTING

## 目的

在正式引入第一批 100–500 个精准真实访客前，先建立可靠的用户行为漏斗。

P4.3 不追求广告画像，不建立第三方跟踪网络，只回答产品验证问题：

- 有没有真实用户进入？
- 首页是否把人带进 Opportunity？
- 用户会不会继续看第二个机会？
- 详情页是否真的被阅读？
- 用户是否使用机会库搜索/筛选？
- 是否有人点击原始证据/来源？
- 用户是否在几天后回来？

## 隐私原则

采用第一方、假名化、最小化采集：

不入库：
- IP 地址
- Email
- 姓名
- 完整 User-Agent
- 完整搜索词
- 页面完整 query string
- 第三方广告 ID

保存：
- 随机 visitor UUID
- 当前标签页 session UUID
- 事件类型
- pathname
- Opportunity slug
- referrer domain（仅域名）
- 经过长度限制的 UTM source/medium/campaign
- mobile/tablet/desktop 粗粒度设备类别
- 严格白名单 metadata

visitor UUID 每 90 天轮换。
session UUID 只保存在 sessionStorage。

浏览器如果启用 Global Privacy Control 或 Do Not Track，前端不发送行为分析事件。
隐私页提供关闭第一方匿名分析的入口。

## 事件合同

- PAGE_VIEW
- OPPORTUNITY_CARD_CLICK
- OPPORTUNITY_DETAIL_VIEW
- SECOND_OPPORTUNITY_VIEW
- CATALOG_SEARCH
- CATALOG_FILTER
- SOURCE_OUTBOUND_CLICK
- ENGAGED_30S
- SCROLL_50
- SCROLL_90

搜索事件只记录 query_length 与当前结果数量，不记录用户输入的原始文字。

## 原始数据保留

Raw event 默认 90 天。
每天自动清理超过 90 天的行为事件。

长期产品指标应使用聚合统计，不依赖无限期保存浏览明细。

## 核心验证指标

1. Unique Visitors
2. 首页/机会库 → Detail 转化
3. 第二个 Opportunity 浏览率
4. Detail 30 秒参与率
5. Detail 90% 滚动率
6. 来源 Outbound CTR
7. 7 日回访

注册转化、收藏、观察等指标在 Auth 真正开放以后接入，不提前伪造。

## 安全

浏览器不直接写数据库。
Public browser → behavior-track Edge Function → service-role RPC → private behavior_events。

behavior_events：
- RLS enabled
- anon/authenticated 无表权限
- service_role only
- event UUID 去重
- session 60 events/min fail-soft 限流
- metadata 最大 2 KB
- event/path/slug 严格校验

## 不改变

- OPP_V0.2
- public_ready
- Source Policy
- Auth Gate
- Newsletter Gate
- Marketplace roadmap
