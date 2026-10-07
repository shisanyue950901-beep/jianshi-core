# P4.8D｜首轮真实用户复盘门禁

日期：2026-10-07  
状态：FROZEN_FOR_FIRST_REAL_USER_REVIEW

## 为什么需要这一层

现在见势已经具备：

- 6 个具体海外已验证项目；
- 首页 / 机会库 / 详情页真实路径；
- 第一方匿名行为分析；
- P4.8B 只读漏斗报告；
- 标准 UTM；
- 内部 QA session 隔离。

接下来最容易发生的错误，不是“没有数据”，而是**数据太少时就开始改产品**。

因此 P4.8D 不新增功能，而是冻结第一次真实用户复盘的门禁和改动纪律。

## 第一复盘门禁

唯一量化门槛：

```text
target_detail_sessions < 30
=> ACCUMULATING

target_detail_sessions >= 30
=> ENOUGH_FOR_FIRST_REVIEW
```

这里的 30 只表示“允许做第一次产品复盘”，**不是统计显著性声明，也不是成功阈值**。

在真实基线形成前，不人为规定“点击率必须 20%”“30 秒阅读必须 50%”之类的漂亮数字。

## 30 个详情 session 前允许立即修什么

只有以下类型可以不等样本门槛：

1. 功能 bug；
2. 事实错误；
3. 严重误导文案；
4. 行为分析故障；
5. 阻断用户使用的可访问性问题。

这些属于质量缺陷，不属于“基于转化率优化”。

## 30 个详情 session 前禁止因数据波动修改什么

不得因为少数用户行为就修改：

- 推荐档位；
- OPP_V0.2；
- 项目排名；
- 数据源路线；
- 6 个详情页 noindex 边界；
- Auth 上线状态。

特别禁止：

> 某个项目暂时点击最多 → 就认定它最好 → 提高推荐档位。

点击兴趣与商业判断是两回事。

## 第一次复盘只看四层漏斗

### 1. 入口选择

指标：`entry_click_rate_pct`

它回答：

> 进入首页 / 机会库的人，是否愿意点进至少一个具体项目？

如果这一层相对最弱，优先检查：

- 首页是否一眼能看懂；
- 项目卡标题是否具体；
- 一句话项目说明是否让中文用户理解；
- 具体项目是否被旧趋势内容抢走注意力。

### 2. 详情参与

指标：`engaged_30s_rate_pct`

它回答：

> 点进项目的人，是否愿意至少花 30 秒继续看？

如果这一层相对最弱，优先检查：

- 卡片承诺和详情内容是否一致；
- 详情首屏结论是否太抽象；
- “项目是什么”是否足够具体；
- 证据解释是否过早、过重。

### 3. 深度阅读

指标：`scroll_90_rate_pct`

它回答：

> 用户是否愿意读到详情页接近底部？

如果这一层相对最弱，优先检查：

- 六问结构是否清楚；
- 是否有重复信息；
- 页面是否过长；
- 风险与未知是否放得太后；
- 手机阅读是否累。

### 4. 跨项目比较

指标：`second_target_project_rate_pct`

它回答：

> 用户是否把见势当成“比较项目”的工具，而不是只看完一页就走？

如果这一层相对最弱，优先检查：

- “继续比较”是否有吸引力；
- 不同项目之间的差异是否足够清楚；
- 是否缺少统一可比字段；
- 返回首批项目的路径是否明显。

## 如何决定第一刀改哪里

第一次复盘不追求同时提高所有数字。

按以下顺序：

1. 先确认数据采集健康；
2. 结合 5 问定性访谈，找出用户真实困惑；
3. 找到四层漏斗里最明显的摩擦；
4. 只选择一个产品层做最小改动；
5. 不碰证据事实和推荐档位，除非发现事实本身错误；
6. 改动发布后开启新的测试 Epoch；
7. 新旧 Epoch 分开比较。

## 不要把不同问题混在一起

例如：

- 首页点击低：不代表项目本身不好；
- 30 秒阅读低：不代表商业模型没价值；
- 第二项目浏览低：不代表详情页一定差；
- FBA 点击高：不代表 FBA 应该从“值得研究”改成“优先研究”。

用户行为用于验证**产品表达与使用价值**，不能替代商业证据判断。

## 第一次复盘输出模板

复盘时只产出：

```text
SAMPLE_GATE = PASS / ACCUMULATING
DATA_HEALTH = PASS / FAIL
ENTRY = OBSERVATION
DETAIL_30S = OBSERVATION
SCROLL_90 = OBSERVATION
SECOND_PROJECT = OBSERVATION
QUALITATIVE_TOP_CONFUSION = ...
PRIMARY_FRICTION_LAYER = ...
ONE_CHANGE_FOR_NEXT_EPOCH = ...
BUSINESS_EVIDENCE_CHANGE = FALSE unless factual error
RECOMMENDATION_CHANGE = FALSE unless evidence changed
```

## 冻结

```text
P48D_FIXED_SUCCESS_THRESHOLDS = FALSE
P48D_MIN_DETAIL_SESSIONS = 30
P48D_PRE_GATE_PRODUCT_OPTIMIZATION = BLOCKED
P48D_QUALITY_FIXES = ALLOWED
P48D_ONE_LAYER_PER_EPOCH = TRUE
P48D_OUTREACH_SENT = FALSE
```
