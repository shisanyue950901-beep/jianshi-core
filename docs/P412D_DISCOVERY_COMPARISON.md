# P4.12D｜发现、查找与商业模式对比

状态：CODE_REVIEW / CI_PENDING / NOT_PUBLISHED

## 用户目标

一个第一次来到见势的中文用户，应该可以：

1. 用自己的话搜索“模板、小说、软件、广告、服务”等相关业务；
2. 区分**六种商业模式**与**两份具名具体项目**；
3. 按业务类型和内容类型缩小范围；
4. 在 2–3 种商业模式之间比较销售内容、客户、收费、日常经营、成本和待核实问题；
5. 从具名项目档案一键进入相关的商业模式指南；
6. 使用手机或键盘完成以上动作。

本阶段**没有**增加未经核实的新项目、收入数字或商业数据来源。

## 上线预览中的实质变化

- **页面先展示两份可核对的具名项目，再展示六种商业模式**；不把项目大类冒充完整公司档案；
- 六类商业模式和两份具名案例共用一个关键词入口，但结果数明确区分两个身份；
- 内容类型「全部内容／商业模式／具体项目」和已有行业筛选配合使用；
- 没有结果时给出清楚的恢复方法，不显示虚假的推荐；
- 默认选定数字产品和亚马逊数字出版作对比，支持 2–3 项，不允许超过 3 项堆叠；
- 对比表始终比较 **商业模式**，禁止把具名项目的经营结果臆测为可比较的事实；
- 桌面保留现有暗/浅主题；手机端对比表允许横向滚动；低动态偏好继续生效；
- 页面内 hash 导航到详情后聚焦标题，返回列表时恢复到对应区域；
- 兼容已有 `#project-*` / `#case-*` 路由。

## 为什么不做“推荐哪个最赚钱”

目前只有商业模式知识与两份产品存在可核验的具名案例资料，没有两家企业可比较的完整收入与净利。

因此：

```text
RECOMMEND_BY_EARNINGS = FALSE
CASE_FINANCIAL_COMPARISON = FALSE
CATEGORY_EXISTS != VERIFIED_COMPANY
PRODUCT_EXISTS != VERIFIED_PROFIT
```

后续只有拿到**单个案例可展示且可核实的经营数据**，才考虑增加其对应比较字段。空字段不应靠页面文字猜测填充。

## 工程限制

- 仅修改 **未发布的** `web/prototypes/p412a/index.html`；
- 新增 `config/p412d_discovery_contract.json`、本说明和测试；
- 不修改 `web/build.py` 或生产网站文件；
- 不动 Production / Staging 数据库或 Auth；
- 不合并历史开放的 PR #52；
- 不公开受保护采集渠道、原始挂牌编号、英文标题或内部证据源键。

## 验收项目

```text
P412D_SEARCH_6_MODES_2_CASES = REQUIRED
P412D_CONTENT_TYPE_FILTER = REQUIRED
P412D_BUSINESS_TYPE_FILTER = REQUIRED
P412D_RESULT_COUNT_AND_EMPTY_STATE = REQUIRED
P412D_COMPARISON_ONLY_OF_BUSINESS_MODELS = REQUIRED
P412D_COMPARE_LIMIT_2_TO_3 = REQUIRED
P412D_CASES_KEEP_FINANCIALS_UNKNOWN = REQUIRED
P412D_KEYBOARD_AND_MOBILE_QA = STATIC_AND_SYNTAX_PASS / REAL_BROWSER_PENDING
P412D_SOURCE_PRIVACY = REQUIRED
P412D_CI = PASS_RUN_239
P412D_PRODUCTION_RELEASE = FALSE
```

## 接下来的发布门槛

P4.12E 应先做真实浏览器桌面、手机与键盘验收；测试体验要覆盖深色、浅色、搜索、无结果、双类型筛选、对比最小/最大选择、返回路径、直接打开案例 Hash。

只有新版用户任务测试通过且 Cloudflare Pages 发布目录安全问题被处理，才开始讨论在受控预览环境发布，而不是直接替换 Production 首页。
