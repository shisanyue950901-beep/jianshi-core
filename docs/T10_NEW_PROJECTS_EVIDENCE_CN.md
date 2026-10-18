# T10｜Hark 二次精度复核：公开 Markdown 财务、增长和成立日期

> 2026-10-18。PR [#189](https://github.com/shisanyue950901-beep/jianshi-core/pull/189)，分支 `feat/t10-new-projects`。Hark确认上轮第1–8项已落实；本次依据 TrustMRR 公开 `.md` 的 **Last 30 days revenue growth / Founded / All-time revenue** 修订，不再以仅包含简略字段的HTML替代精度数据。A与同站 .md 为同源，**不是两个独立A证据**。

| ID | 产品 | 类别 | 成立精确日 | 近30天收入USD | MRR USD | All-time USD | 30天增长 | A公开原页和.md | 独立T指标 | 评分 |
|---|---|---|---|---:|---:|---:|---:|---|---|---|
| `myfeedin` | MyFeedIn | 浏览器插件 | 2024-06-11 | $2,586 | $1,350 | $30,843 | +54.5% | [A原页](https://trustmrr.com/startup/myfeedin) / [.md](https://trustmrr.com/startup/myfeedin.md) | [chrome_users=2000](https://chromewebstore.google.com/detail/myfeedin-linkedin-analyti/enliacdgianieomegijopbecafnapnha) | 16/25 可做 |
| `superx` | SuperX | 浏览器插件 | 2025-08-14 | $21,824 | $22,420 | $254,578 | +25.5% | [A原页](https://trustmrr.com/startup/superx) / [.md](https://trustmrr.com/startup/superx.md) | [chrome_users=10000](https://chromewebstore.google.com/detail/superx-twitter-analytics/bjobgelaoehgbnklgcaaehdpckmhkplk) | 14/25 不推荐 |
| `compresto` | Compresto | 小App | 2023-12-18 | $1,935 | $215 | $62,497 | +46.4% | [A原页](https://trustmrr.com/startup/compresto) / [.md](https://trustmrr.com/startup/compresto.md) | [product_hunt_review_count=10](https://www.producthunt.com/products/compressx) | 17/25 可做 |
| `ai-toolbox` | AI Toolbox | 浏览器插件 | 2024-09-08 | $21,001 | $1,334 | $113,519 | -2.7% | [A原页](https://trustmrr.com/startup/ai-toolbox) / [.md](https://trustmrr.com/startup/ai-toolbox.md) | [chrome_users_lower_bound=40000](https://chromewebstore.google.com/detail/ai-toolbox-folders-prompt/jlalnhjkfiogoeonamcnngdndjbneina) | 15/25 可做 |
| `truesearch` | TrueSearch | 小App | 2025-12-10 | $2,934 | $3,107 | $23,318 | -19.2% | [A原页](https://trustmrr.com/startup/truesearch) / [.md](https://trustmrr.com/startup/truesearch.md) | [app_store_rating_count=134](https://apps.apple.com/us/app/truesearch-ai-people-search/id6756086598?platform=iphone&see-all=reviews) | 13/25 不推荐 |
| `rapidnative` | RapidNative | 开发者工具 | 2025-03-06 | $6,074 | $5,301 | $74,805 | -7.1% | [A原页](https://trustmrr.com/startup/shaper-studio-inc) / [.md](https://trustmrr.com/startup/shaper-studio-inc.md) | [product_hunt_followers=222](https://www.producthunt.com/products/rapidnative) | 13/25 不推荐 |
| `rooftops-ai` | Rooftops AI | SaaS | 2024-01-01 | $2,379 | $1,124 | $25,851 | +388.5% | [A原页](https://trustmrr.com/startup/rooftops-ai) / [.md](https://trustmrr.com/startup/rooftops-ai.md) | [product_hunt_followers=79](https://www.producthunt.com/products/rooftops-ai) | 12/25 不推荐 |
| `blipix` | Blipix | AI工具 | 2025-02-08 | $1,722 | $1,517 | $38,277 | +28.8% | [A原页](https://trustmrr.com/startup/blipix) / [.md](https://trustmrr.com/startup/blipix.md) | [trustpilot_review_count=5](https://uk.trustpilot.com/review/blipix.pro) | 16/25 可做 |
| `rezi` | Rezi | AI工具 | 2015-05-22 | $214,250 | $246,345 | $10,365,680 | -6.0% | [A原页](https://trustmrr.com/startup/rezi) / [.md](https://trustmrr.com/startup/rezi.md) | [product_hunt_review_count=5](https://www.producthunt.com/products/rezi) | 13/25 不推荐 |
| `practiceme` | Practiceme | 教育工具 | 2025-09-03 | $3,922 | $2,956 | $24,717 | -23.8% | [A原页](https://trustmrr.com/startup/practiceme) / [.md](https://trustmrr.com/startup/practiceme.md) | [app_store_rating_count=1](https://apps.apple.com/us/app/ai-speak-english-practice-me/id6751178289) | 17/25 可做 |

## 逐项核查
- `growth_30d`十条均按公开 `.md` 保存**一位小数**，包含负增长：AI Toolbox -2.7%、TrueSearch -19.2%、RapidNative -7.1%、Rezi -6.0%、Practiceme -23.8%。TrueSearch和Practiceme添加收入下降flag；Rooftops AI增长调整为+388.5%，保留小基数波动风险。
- `founded_date`有来源的九条改为年月日精确日期；Rooftops AI仍为2024-01-01。删除旧「仅公开到月份」及AI Toolbox「按月初录入」表述。
- Practiceme `revenue.all_time`由null更新至**$24,717**，删除无累计收入的过期flag和review_notes；其余已有All-time金额不改。
- AI Toolbox源字段 `team_size=2–5 people` 为区间而非确定人数，因此规范字段置`null`，flags写「来源团队规模 2–5 人」。
- Rooftops AI Product Hunt **79** 关注者、Blipix Trustpilot **5条评价 / 4.0分**，以及Hark前次修正的财务结构、挂牌价格和独立T证据原样保留。
- Rezi暂不替换。按Hark本次指令为**待用户决定**，本提交仍保留Rezi原记录、分类和评分；若后续选择替换，须另开受控修改并重新验证T10类别和收入门槛。
- 原有20条JSON不变，新增10条继续`reviewed_by_hark=true`/`publication_status=PUBLIC`；分类分布浏览器插件3、小App2、开发者工具1、SaaS1、AI工具2、教育工具1；首页前三仍是`1clickwebsite-ai`、`sonar-aso-tool`、`3dplotter`。

## 限制与交付边界
- 支付平台API连接/收入由TrustMRR公开页面声称，**不代表见势独立财务审计**；Chrome安装档位、Product Hunt关注数、App Store评分和Trustpilot评价不等于付费人数。
- 本轮只使用已公开的有限事实并标注出处，不调用TrustMRR API、不使用密钥；保留适用平台条款风险说明，不另外把书面许可申请设为此PR的技术CI闸门。
- PR的`PUBLIC`编辑状态不是对`main`的合并授权。必须以本次修正后的**真实PR HEAD**对应GitHub CI为准，Hark复查后另行决定是否squash。未经明确「Hark 已批准，请 squash 合并 #189」不得合并main。

## Hark站外牵引力原页最终复核（2026-10-18）
- Compresto：Product Hunt 原页 10 条评价。
- RapidNative：Product Hunt 原页 222 关注者。
- Rooftops AI：Product Hunt 原页 79 关注者。
- Blipix：Trustpilot 原页 5 条评价、4.0 分。
- Rezi：Product Hunt 原页 5 条评价。

上述五项经Hark于2026-10-18人工核对，已替换项目详情页中误称“尚未完成站外原页复核”的过期flags。指标为第三方牵引力，不代表收入或付费人数。原有10条项目数据、五维评分和PUBLIC审核状态不变。
