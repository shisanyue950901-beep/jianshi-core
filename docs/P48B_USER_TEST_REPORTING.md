# P4.8B｜真实用户测试报告合同

日期：2026-10-07  
状态：READY

## 目的

P4.8A 已经把 6 个“海外已验证项目”接入真实用户路径。P4.8B 不新增采集、不改数据库，只把现有第一方匿名事件变成一套可重复执行的产品验证报告。

## 冻结 Epoch

```text
P48A_USER_TEST_EPOCH_START = 2026-10-07T15:49:06Z
P48A_PRE_EPOCH_NEW_PROJECT_EVENTS = 0
TARGET_PROJECT_COUNT = 6
MIN_DETAIL_SESSIONS_BEFORE_FIRST_REVIEW = 30
```

Epoch 起点采用 P4.8A Static Snapshot #69 完成并已确认线上生效后的时间。

## 目标项目

- vertical-industry-saas
- amazon-fba-niche-brand
- digital-product-business
- affiliate-content-site
- amazon-kdp-publishing
- agency-business

## 第一轮只看四个问题

### 1. 用户会不会点进具体项目？

`entry_click_rate_pct`

分母：Epoch 后访问过首页或机会库的 session。  
分子：从首页或机会库点击任一首批项目的 session。

### 2. 点进去后会不会认真读？

`engaged_30s_rate_pct`

分母：首批项目详情 session。  
分子：触发 ENGAGED_30S 的详情 session。

### 3. 会不会读到页面深处？

`scroll_90_rate_pct`

分母：首批项目详情 session。  
分子：触发 SCROLL_90 的详情 session。

### 4. 会不会继续比较第二个项目？

`second_target_project_rate_pct`

分母：首批项目详情 session。  
分子：同一 session 查看至少 2 个不同首批项目的 session。

这里不直接使用全站 SECOND_OPPORTUNITY_VIEW 作为分子，而是从首批 6 个项目的真实 detail view 重新计算，避免旧趋势页混入。

## 来源归因规则

UTM / referrer 不从详情页事件本身读取，而从“最终进入首批项目详情的 session 的第一个事件”读取。

原因：用户常常先访问带 UTM 的首页，再点击内部链接进入详情页。内部跳转后的详情 URL 不再携带 UTM；如果只看详情事件，会错误地把这类流量记成无来源。

冻结规则：

```text
ACQUISITION_ATTRIBUTION = FIRST_EVENT_IN_TARGET_DETAIL_SESSION
```

这样首页、机会库或直接详情落地都能按 session 的原始入口归因。

## 辅助诊断

报告同时输出：

- 每个项目的详情 session / 30 秒阅读 / 90% 深读；
- 点击入口来自首页、机会库还是详情页继续比较；
- 设备类别；
- UTM source / medium / campaign；
- referrer domain；
- 直接落地或未捕获点击的详情 session。

## 决策纪律

在 `target_detail_sessions < 30` 时：

```text
DECISION_STATE = ACCUMULATING
```

只检查数据是否健康，不因为少数点击修改产品定位、项目排序或详情结构。

达到 30 个首批项目详情 session 后：

```text
DECISION_STATE = ENOUGH_FOR_FIRST_REVIEW
```

才进入第一次产品复盘。

第一轮不冻结“成功率阈值”。先获得真实基线，再决定后续 A/B 或结构调整，避免先定一个看起来漂亮但没有依据的数字。

## 执行方式

执行：

`scripts/p48b_user_test_report.sql`

脚本只有 SELECT / CTE，不包含：

- INSERT
- UPDATE
- DELETE
- CREATE
- ALTER
- DROP
- TRUNCATE

因此不会修改 Production。

## 不改变

- OPP_V0.2
- Source Policy
- Production Schema
- Auth Gates
- PR #52
- 6 个首批详情页的 noindex,nofollow
- 现有 P4.3 行为事件合同
