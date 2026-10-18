# T10｜新增10条项目公开证据与Hark待审清单

> 执行日期：2026-10-18。基线main：`1557438df2016752ef9359562032aaa6a1e8e656`；分支：`feat/t10-new-projects`。仅公开网页读取，不调用TrustMRR API或私有脚本；Hark未批准，生产不可发布。

## 新增10条证据映射
| ID | 名称 | 类别 | 成立 | 近30日USD | A支付声明公开来源 | 第三方平台T原页及数值 | 评分 |
|---|---|---|---|---:|---|---|---|
| `myfeedin` | MyFeedIn | 浏览器插件 | 2024-06-01（仅月精度） | $2,733 | [Stripe源](https://trustmrr.com/startup/myfeedin) | [chrome_users = 2000](https://chromewebstore.google.com/detail/myfeedin-linkedin-analyti/enliacdgianieomegijopbecafnapnha) | 16/25 可做 |
| `superx` | SuperX | 浏览器插件 | 2025-08-01（仅月精度） | $20,632 | [Stripe源](https://trustmrr.com/startup/superx) | [chrome_users = 10000](https://chromewebstore.google.com/detail/superx-twitter-analytics/bjobgelaoehgbnklgcaaehdpckmhkplk) | 14/25 不推荐 |
| `compresto` | Compresto | 小App | 2023-12-01（仅月精度） | $1,880 | [Polar源](https://trustmrr.com/startup/compresto) | [product_hunt_review_count = 10](https://www.producthunt.com/products/compressx) | 17/25 可做 |
| `extrabar` | ExtraBar | 小App | 2025-12-01（仅月精度） | $1,538 | [Stripe源](https://trustmrr.com/startup/extrabar) | [product_hunt_followers = 203](https://www.producthunt.com/products/extrabar) | 19/25 可做 |
| `truesearch` | TrueSearch | 小App | 2025-12-01（仅月精度） | $2,956 | [RevenueCat源](https://trustmrr.com/startup/truesearch) | [app_store_rating_count = 108](https://apps.apple.com/us/app/truesearch-ai-people-search/id6756086598?platform=iphone&see-all=reviews) | 13/25 不推荐 |
| `rapidnative` | RapidNative | 开发者工具 | 2025-03-01（仅月精度） | $6,014 | [Stripe源](https://trustmrr.com/startup/shaper-studio-inc) | [product_hunt_followers = 222](https://www.producthunt.com/products/rapidnative) | 13/25 不推荐 |
| `rooftops-ai` | Rooftops AI | SaaS | 2024-01-01（仅月精度） | $1,940 | [Stripe源](https://trustmrr.com/startup/rooftops-ai) | [product_hunt_review_count = 1](https://www.producthunt.com/products/rooftops-ai) | 12/25 不推荐 |
| `blipix` | Blipix | AI工具 | 2025-02-01（仅月精度） | $1,739 | [Stripe源](https://trustmrr.com/startup/blipix) | [trustpilot_review_count = 7](https://uk.trustpilot.com/review/blipix.pro) | 16/25 可做 |
| `rezi` | Rezi | AI工具 | 2015-05-01（仅月精度） | $217,419 | [Stripe源](https://trustmrr.com/startup/rezi) | [product_hunt_review_count = 5](https://www.producthunt.com/products/rezi) | 13/25 不推荐 |
| `practiceme` | Practiceme | 教育工具 | 2025-09-01（仅月精度） | $4,165 | [RevenueCat源](https://trustmrr.com/startup/practiceme) | [app_store_rating_count = 1](https://apps.apple.com/us/app/ai-speak-english-practice-me/id6751178289) | 17/25 可做 |

检查日均为2026-10-18。收入as_of采用**上游公开同步日**，以区别于本次检查日期；源页面标题与30天图表矛盾时选择30天图表并在flags记录。同步逾30天的ExtraBar显示「待更新」。Product Hunt等数字会波动，需要Hark再次打开链接核验；T的评价、关注数、应用安装档位不表示付费客户数。

## 逐条重点风险
- **myfeedin**：收入页面标题$2,793与30日图表$2,733不一致；保留图表口径待Hark裁定。
- **superx**：收入页标题$21,053与图表$20,632不一致；采用图表值，须Hark复核。
- **compresto**：Product Hunt原slug为CompressX，但该页面现标题Compresto且域名同为compresto.app。
- **extrabar**：近30天财务同步于2026-09-05，超过30天，待更新。；MRR原页显示横线且无活跃订阅，不将未知值擅写成0。
- **truesearch**：TrustMRR同期转引App评分124条，App Store独立原页显示108条，不同日期/地区口径需核查。；App Store出现订阅取消困难投诉，属于用户评论未经裁定。
- **rapidnative**：收入页slug是shaper-studio-inc，公开页面显示名称RapidNative且链接rapidnative.com。；收入页标题$6,054与30日图表$6,014存在小幅不一致，使用图表值。
- **rooftops-ai**：Product Hunt仅1条评价，证据虽独立但不能说明大量活跃客户。
- **blipix**：Trustpilot评价是使用线索，存在样本偏差，不等于7个付费用户。
- **rezi**：近30天$217,419超过历史T04初筛$50k上限，但当前T10任务卡只规定下限，保留作低复刻性参考。；已披露VC-backed、用户和收入量级巨大，不代表个人可复制。
- **practiceme**：公开来源未显示可精确摘录的历史累计收入，置null。；App Store仅1条评价，属于弱但真实独立牵引力。

## 入库与分发边界
- T10硬条件：至少1个支付直连A/A-；成立已满90日；last_30d≥$1,000；至少1个独立站外T原页数值；不入电商、金融、医疗、成人、代理服务。
- 20条既有项目冻结未修改；10条新项目`reviewed_by_hark=false`且`publication_status=PRIVATE_REVIEW_ONLY`。Hark审核或书面许可问题未解决前，不得进入正式main/线上。
- TrustMRR公开页面的财务真伪只达到「平台声明付款已连接」，不等于由见势独立审计。TrustMRR Terms更新时间为2026-10-09；来源注册表仍标识TrustMRR的公开再展示需取得书面许可。**PR审核前务必确认该许可；本次PR不代表授权。**
- 近30日口径≠MRR≠历史总收入。无数据用null，不估算。日期因公开来源只提供月份而以每月1日存，成立90日也从该月份最末日重新保守核验。
- 第三方T独立于收入平台，但其数字并不证明收入真实；Product Hunt仅1或几条评价的牵引力极弱，需要Hark单独决定是否足够。
- 任务卡不设收入上限，故Rezi虽规模远超小型个人产品仍作为低可复制性参考；若Hark要求严格小体量库，应退回更换，禁止擅改历史门槛。

## 首页JSON真实前三
`1clickwebsite-ai → sonar-aso-tool → 3dplotter`。新增最高评分`19`，未进入首页前三；原有评分/收入不改。首页仍从JSON排序，无硬编码项。

## 已淘汰的候选
- PostNitro：支付API key连接过期，不能以陈旧快照声称即时收入。
- FriendFilter + GroupFilter：Stripe连接过期；历史数值不得充当近期已验证收入。
- Preuve AI / Prompt Builder：支付连接过期，故不入库。
- Unsection等：最近30天收入低于$1,000，不满足硬门槛。
- Did I Do?：主体功能与ADHD/OCD健康相关，避免触碰T10医疗排除范围。

## Hark验收须审阅
1. 逐条打开公开A页与T原页核对时点数值、产品域名对应关系；留意缓存/时区与金额标题/图表矛盾。
2. 核查成立月份与至少90日、分类配比、10条新增不重名；重点确认`ExtraBar`源同步超过30日、`TrueSearch`的个人数据及按周收费投诉、`Rooftops AI`仅1条评价。
3. 核查页面重新展示权限和数据来源条款（尤其TrustMRR Terms）；未确认书面许可不得批准生产发布。
4. 核查五维评分与新榜单。尚无Hark审批，不能勾选reviewed状态。
5. GitHub工作流状态以当前PR同一HEAD的JianShi CI、T07、JianShi Static Snapshot实际运行结果为准；不得将静态模拟通过当作真实用户或生产部署成功。
