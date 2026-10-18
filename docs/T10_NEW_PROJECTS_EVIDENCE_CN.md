# T10｜新增10条项目证据台账及Hark条件复核修正（2026-10-18）

> PR [#189](https://github.com/shisanyue950901-beep/jianshi-core/pull/189)，源分支 `feat/t10-new-projects`；基线main `1557438df2016752ef9359562032aaa6a1e8e656`。Hark已作有条件数据复核。本次仅修正T10记录与测试，尚未授权合并main。支付连接标识为来源平台的声明，不是见势独立财务审计。

## 新增10条证据清单（USD）

| ID | 项目 | 类别 | 成立（月精度） | 近30天收入 | MRR | 累计收入 | 月环比 | A来源 | 独立T平台指标 | 评分 |
|---|---|---|---|---:|---:|---:|---:|---|---|---|
| `myfeedin` | MyFeedIn | 浏览器插件 | 2024-06-01 | $2,586 | $1,350 | $30,843 | +55% | [公开A页](https://trustmrr.com/startup/myfeedin) | [chrome_users=2000](https://chromewebstore.google.com/detail/myfeedin-linkedin-analyti/enliacdgianieomegijopbecafnapnha) | 16/25 可做 |
| `superx` | SuperX | 浏览器插件 | 2025-08-01 | $21,824 | $22,420 | $254,578 | +25% | [公开A页](https://trustmrr.com/startup/superx) | [chrome_users=10000](https://chromewebstore.google.com/detail/superx-twitter-analytics/bjobgelaoehgbnklgcaaehdpckmhkplk) | 14/25 不推荐 |
| `compresto` | Compresto | 小App | 2023-12-01 | $1,935 | $215 | $62,497 | +46% | [公开A页](https://trustmrr.com/startup/compresto) | [product_hunt_review_count=10](https://www.producthunt.com/products/compressx) | 17/25 可做 |
| `ai-toolbox` | AI Toolbox | 浏览器插件 | 2024-09-01 | $21,001 | $1,334 | $113,519 | 未公开 | [公开A页](https://trustmrr.com/startup/ai-toolbox) | [chrome_users_lower_bound=40000](https://chromewebstore.google.com/detail/ai-toolbox-folders-prompt/jlalnhjkfiogoeonamcnngdndjbneina) | 15/25 可做 |
| `truesearch` | TrueSearch | 小App | 2025-12-01 | $2,934 | $3,107 | $23,318 | 未公开 | [公开A页](https://trustmrr.com/startup/truesearch) | [app_store_rating_count=134](https://apps.apple.com/us/app/truesearch-ai-people-search/id6756086598?platform=iphone&see-all=reviews) | 13/25 不推荐 |
| `rapidnative` | RapidNative | 开发者工具 | 2025-03-01 | $6,074 | $5,301 | $74,805 | 未公开 | [公开A页](https://trustmrr.com/startup/shaper-studio-inc) | [product_hunt_followers=222](https://www.producthunt.com/products/rapidnative) | 13/25 不推荐 |
| `rooftops-ai` | Rooftops AI | SaaS | 2024-01-01 | $2,379 | $1,124 | $25,851 | +389% | [公开A页](https://trustmrr.com/startup/rooftops-ai) | [product_hunt_followers=79](https://www.producthunt.com/products/rooftops-ai) | 12/25 不推荐 |
| `blipix` | Blipix | AI工具 | 2025-02-01 | $1,722 | $1,517 | $38,277 | +29% | [公开A页](https://trustmrr.com/startup/blipix) | [trustpilot_review_count=5](https://uk.trustpilot.com/review/blipix.pro) | 16/25 可做 |
| `rezi` | Rezi | AI工具 | 2015-05-01 | $214,250 | $246,345 | $10,365,680 | 未公开 | [公开A页](https://trustmrr.com/startup/rezi) | [product_hunt_review_count=5](https://www.producthunt.com/products/rezi) | 13/25 不推荐 |
| `practiceme` | Practiceme | 教育工具 | 2025-09-01 | $3,922 | $2,956 | 未公开 | 未公开 | [公开A页](https://trustmrr.com/startup/practiceme) | [app_store_rating_count=1](https://apps.apple.com/us/app/ai-speak-english-practice-me/id6751178289) | 17/25 可做 |

## Hark修正核对
- 累计收入已补：MyFeedIn $30,843；SuperX $254,578；AI Toolbox $113,519；RapidNative $74,805；Rooftops AI $25,851；Rezi $10,365,680。Compresto、TrueSearch、Blipix仍保留已确认的历史累计收入；Practiceme未公开，保留`null`，不等于0。
- 月环比：MyFeedIn +55%；SuperX +25%；Compresto +46%；Rooftops AI +389%（小基数、大波动）；Blipix +29%。无来源的其余5条为`null`，不是零增长。
- 独立T：Rooftops AI Product Hunt关注者更新79；Blipix Trustpilot更新5条评价、4.0/5分。Chrome 3条、App Store 2条及Product Hunt中Hark实际复核的3条按其当天原页记录；避免将下载/关注/评分误标为付费客户数。
- 收入结构：Compresto MRR $215远低于近30天$1,935；AI Toolbox MRR $1,334远低于$21,001。一次性买断与订阅不得混计。
- 在售披露：AI Toolbox $800,000、TrueSearch $85,000、Rooftops AI $48,000、Blipix $100,000，为卖方要价而非收入；`for_sale`及`flags`保持一致。
- 更正过期文案：TrueSearch旧108条评分删除，Rezi旧$217,419改为$214,250；不再出现已知累计收入“均留空”的矛盾说明。
- 30条唯一ID、原有20条历史JSON、五维评分和verdict均保持不变；新增类别：浏览器插件3、小App2、开发者工具1、SaaS1、AI工具2、教育工具1。首页动态前三仍是 `1clickwebsite-ai`、`sonar-aso-tool`、`3dplotter`。

## 发布技术状态与来源说明
- Hark已对T10数据作有条件复核，因此这10条改为`reviewed_by_hark=true`且`publication_status=PUBLIC`，供GitHub PR环境及模拟main构建验证。**PR审核完成不等于合并授权，未获Hark下一次明确指示前不得合并main。**
- 用户决定本阶段仅引用公开页面可独立观察的有限事实，逐条列明来源，并标注财务未受见势独立审计。不调用TrustMRR API、不保存密钥、不批量转载受保护的描述正文，也不将项目数据伪装为独立审计成果。
- 公开可访问并不当然等于获得平台的再使用授权；`config/source_registry.json`中的采集权限仍适用于自动采集器。本T10任务不将“必须提交书面许可申请”设为额外技术发布闸门，但应持续审查网站使用方式与来源条款，避免侵权或违反平台规则。
- 按Hark复核，原先的静态页面、浏览器、移动端和CI检查均已满足此前HEAD。**本修正提交的CI及模拟main构建结果必须以新HEAD实际GitHub Actions为准**，不能沿用旧HEAD结果。

## Hark最终PR复查
1. 对照本页及JSON核验累计收入、月环比、Rooftops AI及Blipix的站外数据；任何动态更新不得覆盖本次留存的有日期快照。
2. 核查模拟main构建在`review_preview()=false`下生成30条项目和31个页面；继续保留任意一条撤销审核即阻止发布的负向测试。
3. GitHub四项必需检查全绿，确认PR HEAD SHA后再作合并决定；不得启用自动合并。
