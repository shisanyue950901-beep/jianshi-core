# P4.8C｜第一批精准真实用户测试包

日期：2026-10-07  
状态：READY_FOR_CI

## 目标

P4.8A 已经把首批 6 个项目接入产品路径，P4.8B 已经冻结只读报告。

P4.8C 解决最后一个测试执行问题：

> 如何把第一批真实用户带进来，同时保证内部 QA、普通邀请、定性访谈能够被正确区分。

本阶段不主动发送任何邀请，也不选择具体平台渠道。

## 1. 主测试入口

第一批正常受测用户优先统一使用：

```text
https://jianshi-bua.pages.dev/?utm_source=manual_invite&utm_medium=private_share&utm_campaign=p48_first100
```

原因：

- 从首页开始才能真实测试“用户是否理解见势是什么”；
- 可以测首页 / 机会库 → 项目详情转化；
- UTM 会由现有第一方分析在 session 内持续保留；
- 不依赖具体社交平台。

不要为了提高详情访问量而默认直接给用户某个项目详情页，否则会人为绕过首页漏斗。

## 2. 定性访谈入口

只有在明确做“某个项目详情页是否看得懂”的访谈时，才使用直接项目链接。

统一：

```text
utm_source=manual_interview
utm_medium=guided_test
utm_campaign=p48_project_interview
```

这些 session 可以进入详情页阅读质量分析，但不应解释成首页入口转化结果。

所有标准链接由：

`python scripts/p48c_test_links.py`

生成，避免手写 UTM 漂移。

## 3. 内部 QA 不得污染 Epoch

从 P4.8A USER_TEST_EPOCH 开始，后续内部验收必须优先使用：

```text
https://jianshi-bua.pages.dev/?qa=1
```

规则：

- `qa=1`：当前标签页 session 标记为内部 QA，不发送行为事件；
- 站内继续跳转仍保持 QA 抑制；
- `qa=0`：清除当前标签页 QA 标记；
- 关闭标签页后 sessionStorage 自然失效；
- QA 参数不会修改用户的长期匿名分析偏好。

用户自己的 Global Privacy Control、Do Not Track 或“关闭匿名使用分析”仍然有效，不会被 `qa=0` 绕过。

## 4. 什么人算“精准真实用户”

至少满足：

- 中文用户；
- 当前确实在寻找创业项目、副业方向或可复制商业模式，或正在判断一个具体创业方向；
- 愿意自己浏览页面，而不是只听我们讲解；
- 不是为了帮忙“刷数据”而点击。

不要求：

- 必须懂技术；
- 必须是创业者；
- 必须来自某个平台；
- 必须认同见势当前判断。

反对意见和“看不懂”都属于有效数据。

## 5. 首轮定性问题

受测者自由浏览后，只问以下 5 个问题，不先解释标准答案：

1. 你觉得“见势”这个网站主要帮你做什么？
2. 这 6 个项目里，你最想继续研究哪一个？为什么？
3. 哪一段信息最让你觉得可信？哪一段最让你怀疑？
4. 如果你真的想尝试这个方向，页面有没有告诉你第一步该做什么？
5. 你看完后还缺什么信息，才愿意继续花时间研究？

不要把访谈回答写进匿名行为事件表。定性笔记另行人工整理，不采集姓名、联系方式等非必要信息。

## 6. 样本纪律

量化主门槛继续使用：

```text
TARGET_DETAIL_SESSIONS < 30  => ACCUMULATING
TARGET_DETAIL_SESSIONS >= 30 => ENOUGH_FOR_FIRST_REVIEW
```

在 30 个首批项目详情 session 前：

- 不因为单个用户跳出就改首页；
- 不因为某一个项目暂时点击高就改推荐档位；
- 不改 OPP_V0.2；
- 不增加新数据源来“解释”流量；
- 功能 bug、事实错误、严重误导文案可以立即修。

达到 30 个详情 session 后，用 P4.8B 报告做第一次量化复盘，再结合定性访谈决定下一轮改动。

## 7. 第一轮需要回答的产品问题

最终不是追求更多 PV，而是回答：

1. 用户能不能在不解释的情况下理解见势的用途？
2. 用户是否愿意从首页进入至少一个具体项目？
3. 详情页是否值得阅读 30 秒以上、甚至读到 90%？
4. 用户会不会主动比较第二个项目？
5. 哪种具体项目最能触发“我想继续验证”的行为？
6. 用户不继续的原因，是项目不适合，还是产品表达不清？

## 8. 不做

P4.8C 不做：

- 群发邀请；
- 自动私信；
- 买流量；
- 广告投放；
- 平台刷量；
- 朋友帮忙机械点击；
- 提前把 6 个 noindex 详情页改成 SEO 公开奖励流量；
- 根据少量数据做排名优化。

## 冻结状态

```text
P48C_PRIMARY_ENTRY = HOMEPAGE_WITH_STANDARD_UTM
P48C_INTERVIEW_ENTRY = DIRECT_PROJECT_WITH_INTERVIEW_UTM
P48C_INTERNAL_QA = SESSION_SUPPRESSED_WITH_QA_1
P48C_PLATFORM_MATRIX = NOT_REQUIRED
P48C_OUTREACH_SENT = FALSE
```
