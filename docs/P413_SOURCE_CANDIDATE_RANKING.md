# P4.1.3 高价值项目源候选筛选与排名

日期：2026-10-07
状态：FROZEN_AUDIT
范围：只做来源审计与排序，不接数据库、不部署 Collector、不改 Production。

## 1. 筛选目标

当前目标不是“接更多网站”，而是找到真正能帮助见势把 Opportunity 从个位数扩展到 30–50 个、并保持质量的来源。

本轮五项评分：

- 新 Opportunity 发现能力：30%
- 近期信号密度：25%
- 商业相关性：20%
- 官方 API / 数据许可清晰度：20%
- 免费/低成本接入：5%

任何来源即使总分较高，只要商业重用或聚合条款与见势用途明显冲突，仍可被 Policy Veto 直接 HOLD。

## 2. 第一梯队

### 1. PyPI — NEXT_STAGING_TARGET

综合判断：8.3 / 10

为什么优先：
- 官方提供 JSON API、Index API、RSS Newest Packages / Latest Updates。
- PyPI Terms 明确存在 API Terms，限制主要集中在滥用、过量请求、垃圾营销等。
- 官方 BigQuery Public Dataset 同时提供 package download statistics 与 distribution metadata，并明确这些表的数据采用 Creative Commons 许可。
- Google BigQuery Public Dataset 每月前 1 TiB 查询免费；Sandbox 可以不绑定信用卡使用。
- 能补 npm 偏 JavaScript 的语言偏差，覆盖 Python AI、自动化、数据、开发工具、后端 SaaS 基础设施。

限制：
- PyPI JSON API 自身的 downloads 字段已废弃，不能把它当采用量。
- Newest Packages RSS 噪音高，需要 Candidate Cluster，不可直接“一包一个 Opportunity”。
- BigQuery 下载统计若使用，必须有成本上限与查询预算；验证期先使用 Sandbox / Free Tier。

建议 Evidence：
- PYPI_PACKAGE → TECHNICAL_SUPPLY，shadow-only
- PYPI_DOWNLOAD_TREND → TECHNICAL_ADOPTION，初期 shadow-only

下一步：
只把 PyPI 做成下一条 Staging 实验源，不立即推 Production。

官方依据：
- https://docs.pypi.org/api/
- https://docs.pypi.org/api/json/
- https://docs.pypi.org/api/feeds/
- https://docs.pypi.org/api/bigquery/
- https://policies.python.org/pypi.org/Terms-of-Service/
- https://docs.cloud.google.com/bigquery/docs/sandbox

### 2. Hugging Face Hub — HIGH_PRIORITY_AI_SOURCE

综合判断：8.5 / 10

价值：
- 官方 Hub API 有开放 endpoints。
- 可以按 models / datasets / Spaces 搜索、筛选、排序。
- 官方客户端可按 downloads 等字段排序。
- 信号密度高，尤其适合 AI 应用、模型能力、AI 垂直工具、Agent/Workflow 的候选发现。
- Free/anonymous API 有明确速率配额。

限制：
- 会进一步强化见势当前已经偏 AI 的供给结构，因此不作为“扩宽行业”的第一名。
- Hub 内实际 Model/Dataset/Space 内容许可证各不相同。
- 见势若接入，只应先存官方公开 metadata、tags、downloads/likes/更新时间等；不得把某个 repo 的内容许可证自动解释为允许见势复制内容。
- 需要单独写 Content License Boundary。

建议 Evidence：
- HF_MODEL / HF_SPACE → TECHNICAL_SUPPLY / PRODUCT_SIGNAL，shadow-only

官方依据：
- https://huggingface.co/docs/hub/api
- https://huggingface.co/docs/huggingface_hub/main/guides/search
- https://huggingface.co/docs/hub/main/rate-limits
- https://huggingface.co/terms-of-service

### 3. WordPress.org Plugin Directory — HIGHEST_BUSINESS_VALUE_PENDING_POLICY

产品价值判断：8.4 / 10
接入状态：YELLOW_POLICY_REVIEW

为什么很重要：
- Plugin API 是 WordPress.org 官方生态 API。
- Plugin 数据可包含 active_installs、last_updated、rating 等高价值采用信号。
- WordPress Plugin Directory 明确允许 SaaS/serviceware 类型插件，因此大量插件背后是真实商业产品或服务。
- 对中国个人创业者尤其有价值，因为 WordPress 插件属于典型“小团队可以构建、全球分发、订阅变现”的产品形态。
- 能显著拓宽见势当前偏 AI/GitHub 的 Opportunity 分类。

为什么现在不直接 GREEN：
- 本轮确认了官方 Plugin API 与公开统计字段，但没有找到足够明确、专门面向“第三方商业分析平台长期聚合和再展示 Plugin Directory metadata”的授权条款。
- GPL 覆盖插件代码/目录内容，不应自动扩张解释为 Marketplace 元数据的商业聚合许可。

下一步：
- 做第二轮 policy review。
- 如果仍不明确，给 WordPress.org/Plugin Directory 发一封窄范围使用确认，不抓取替代。
- 在权限明确前不自动采集。

官方依据：
- https://developer.wordpress.org/reference/functions/plugins_api/
- https://developer.wordpress.org/plugins/wordpress-org/
- https://developer.wordpress.org/reference/functions/install_plugin_information/
- https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/

## 3. 第二梯队

### Atlassian Marketplace — YELLOW_API_TRANSITION

综合判断：7.5 / 10

价值：
- B2B 商业相关性非常高。
- 旧 V2 public app listing 数据包含 downloads、reviews 等商业/采用指标。
- Marketplace 是企业软件插件生态，适合发现“企业愿意为什么功能付费”。

问题：
- V2 API 已被弃用并正在关闭。
- 最新 V3 API 更偏 developer/vendor 管理，很多 app listing/software endpoint 示例要求 Atlassian Account + API token。
- 当前不适合基于即将退出的 V2 新建生产 collector。
- 外部商业聚合的授权边界还需进一步确认。

结论：
HOLD_API_TRANSITION。等 V3 稳定的 discovery/read contract 明确后再审。

官方依据：
- https://developer.atlassian.com/platform/marketplace/rest/v3/
- https://developer.atlassian.com/platform/marketplace/rest/v4/api-group-app-listing
- https://developer.atlassian.com/platform/marketplace/searching-for-apps-using-json/

### Envato Market — YELLOW_COMMERCIAL_TERMS_FRICTION

综合产品价值：7.6 / 10

价值：
- 数字商品、模板、插件等非常接近个人创业者可构建/销售的项目。
- API 能形成 price / sales / rating / category 等真实商业需求代理。

主要问题：
- API Terms 对商业 Application 有额外条件。
- Terms 还要求 API 信息不能比 Envato Market 的现状落后超过 6 小时。
- 对见势未来商业化的“分析平台”模式适配不够干净。

结论：
不作为近期接入目标。未来如果产品价值足够高，优先谈官方合作/书面许可，而不是依赖一般 API Terms。

官方依据：
- https://build.envato.com/terms/
- https://help.market.envato.com/hc/en-us/articles/42875085863705-Envato-Market-API-Terms

### Docker Hub — GREEN_LOW_OPPORTUNITY_BREADTH

产品价值：约 7.0 / 10

优点：
- 官方 Hub/Registry API。
- 数据规模大、更新频率高。
- 对基础设施、数据库、AI serving、developer tooling 有采用信号价值。

缺点：
- 主要是技术部署/基础设施，不直接代表可创业商业项目。
- 和 GitHub/npm 的 TECHNICAL_SUPPLY 重叠较高。

结论：
合法性/技术接入问题不大，但机会发现边际价值低。暂不优先。

官方依据：
- https://docs.docker.com/docker-hub/
- https://docs.docker.com/docker-hub/repos/
- https://www.docker.com/legal/docker-terms-use/

## 4. 暂停/不适合当前模式

### JetBrains Marketplace — YELLOW_WRITTEN_PERMISSION

价值：
- 插件市场中同时存在 Free / Paid / Externally Paid Plugin，商业相关性不错。

问题：
- Marketplace Agreement 明确限制未经书面许可分发/提供 Marketplace 或其部分。
- 本轮没有找到适合见势做商业聚合分析的开放 discovery API 授权合同。

结论：
没有书面许可前不自动采集。

官方依据：
- https://www.jetbrains.com/legal/docs/plugins_site/plugin_marketplace/
- https://plugins.jetbrains.com/docs/marketplace/legal-agreements.html

### YouTube Data API — HOLD_POLICY_MISMATCH

数据密度非常高，但当前用途不匹配。

原因：
- YouTube Developer Policies 对 API Data aggregation 有严格限制。
- Non-Authorized API Data 一般不能无限保存，超过 30 天需删除或刷新。
- 2026 年政策进一步要求部分 derived metric / statistical storage 场景需要显式申请/审计批准。
- 见势希望跨大量公开视频聚合并生成趋势/机会分数，这正好触碰高合规复杂度区域。

结论：
当前不作为 DISTRIBUTION_SIGNAL 自动聚合来源。
未来若确有必要，应先申请 YouTube API Compliance Audit / derived metrics permission。

官方依据：
- https://developers.google.com/youtube/terms/developer-policies
- https://developers.google.com/youtube/terms/developer-policies-guide
- https://developers.google.com/youtube/terms/api-services-terms-of-service

## 5. 已有来源保持原判

- npm = GREEN / Production shadow
- Stack Exchange = GREEN legal + HOLD_LOW_SIGNAL product value
- Product Hunt = YELLOW / commercial permission required
- Hacker News = YELLOW / commercial reuse scope not sufficiently explicit
- Reddit = RED / commercial contract required
- Google Trends = YELLOW / official API limited alpha
- Empire Flippers = GREEN commercial proof
- Acquire / Microns / Flippa = commercial partnership outreach candidates

## 6. 冻结排序

按“下一步可以真正推进”的顺序：

1. PYPI = NEXT_STAGING_TARGET
2. HUGGING_FACE = HIGH_PRIORITY_AFTER_PYPI
3. WORDPRESS_PLUGINS = POLICY_REVIEW_NOW / INTEGRATE_AFTER_PERMISSION_CLEAR
4. ATLASSIAN_MARKETPLACE = HOLD_API_TRANSITION
5. ENVATO = HOLD_COMMERCIAL_TERMS
6. DOCKER_HUB = DEFER_LOW_INCREMENTAL_VALUE
7. JETBRAINS = HOLD_WRITTEN_PERMISSION
8. YOUTUBE = HOLD_POLICY_MISMATCH

## 7. 为什么下一条选 PyPI，而不是 Hugging Face

Hugging Face 的信号密度更高，但会继续把 Opportunity 供给集中在 AI。

PyPI：
- 同样是高质量官方源；
- 法务/数据许可路径更清晰；
- 可以补 Python、自动化、数据、后端服务、开发工具等多个类别；
- RSS 可以发现新项目；
- BigQuery public dataset 可以在免费范围内进一步验证真实下载采用；
- 更适合当前“先把 Opportunity 宽度做出来”的目标。

因此：

P4.1.4 下一小步只做 PyPI Staging 设计和验证，不立即 Production。

## 8. 冻结

```
P413_SOURCE_COUNT_KPI = FORBIDDEN
P413_NEXT_STAGING_SOURCE = PYPI
P413_SECOND_SOURCE = HUGGING_FACE
P413_HIGHEST_BUSINESS_UPSIDE_PENDING_POLICY = WORDPRESS_PLUGINS
P413_YOUTUBE = HOLD_POLICY_MISMATCH
P413_NO_PRODUCTION_CHANGE = TRUE
P413_NO_NEW_COLLECTOR_DEPLOYED = TRUE
```
