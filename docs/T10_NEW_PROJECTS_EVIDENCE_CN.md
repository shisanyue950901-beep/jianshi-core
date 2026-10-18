# T10｜新增10条项目证据复查与Hark审核底稿（2026-10-18）

> 分支：`feat/t10-new-projects`；PR #189；基线main：`1557438df2016752ef9359562032aaa6a1e8e656`。本底稿是待审数据和来源映射，不构成TrustMRR授权再发布或见势独立财务审计。

## 最新公开网页复核清单
| ID | 产品 | 新增类别 | 成立日期（月份精度） | 30天收入USD | MRR USD | 支付连接A/A-公开原页 | 独立站外T原页、类别及值 | 五维评分 |
|---|---|---|---|---:|---:|---|---|---|
| `myfeedin` | MyFeedIn | 浏览器插件 | 2024-06-01 | $2,586 | $1,350 | [公开A页](https://trustmrr.com/startup/myfeedin) | [chrome_users=2000](https://chromewebstore.google.com/detail/myfeedin-linkedin-analyti/enliacdgianieomegijopbecafnapnha) | 16/25 可做 |
| `superx` | SuperX | 浏览器插件 | 2025-08-01 | $21,824 | $22,420 | [公开A页](https://trustmrr.com/startup/superx) | [chrome_users=10000](https://chromewebstore.google.com/detail/superx-twitter-analytics/bjobgelaoehgbnklgcaaehdpckmhkplk) | 14/25 不推荐 |
| `compresto` | Compresto | 小App | 2023-12-01 | $1,935 | $215 | [公开A页](https://trustmrr.com/startup/compresto) | [product_hunt_review_count=10](https://www.producthunt.com/products/compressx) | 17/25 可做 |
| `ai-toolbox` | AI Toolbox | 浏览器插件 | 2024-09-01 | $21,001 | $1,334 | [公开A页](https://trustmrr.com/startup/ai-toolbox) | [chrome_users_lower_bound=40000](https://chromewebstore.google.com/detail/ai-toolbox-folders-prompt/jlalnhjkfiogoeonamcnngdndjbneina) | 15/25 可做 |
| `truesearch` | TrueSearch | 小App | 2025-12-01 | $2,934 | $3,107 | [公开A页](https://trustmrr.com/startup/truesearch) | [app_store_rating_count=134](https://apps.apple.com/us/app/truesearch-ai-people-search/id6756086598?platform=iphone&see-all=reviews) | 13/25 不推荐 |
| `rapidnative` | RapidNative | 开发者工具 | 2025-03-01 | $6,074 | $5,301 | [公开A页](https://trustmrr.com/startup/shaper-studio-inc) | [product_hunt_followers=222](https://www.producthunt.com/products/rapidnative) | 13/25 不推荐 |
| `rooftops-ai` | Rooftops AI | SaaS | 2024-01-01 | $2,379 | $1,124 | [公开A页](https://trustmrr.com/startup/rooftops-ai) | [product_hunt_followers=74](https://www.producthunt.com/products/rooftops-ai) | 12/25 不推荐 |
| `blipix` | Blipix | AI工具 | 2025-02-01 | $1,722 | $1,517 | [公开A页](https://trustmrr.com/startup/blipix) | [trustpilot_review_count=7](https://uk.trustpilot.com/review/blipix.pro) | 16/25 可做 |
| `rezi` | Rezi | AI工具 | 2015-05-01 | $214,250 | $246,345 | [公开A页](https://trustmrr.com/startup/rezi) | [product_hunt_review_count=5](https://www.producthunt.com/products/rezi) | 13/25 不推荐 |
| `practiceme` | Practiceme | 教育工具 | 2025-09-01 | $3,922 | $2,956 | [公开A页](https://trustmrr.com/startup/practiceme) | [app_store_rating_count=1](https://apps.apple.com/us/app/ai-speak-english-practice-me/id6751178289) | 17/25 可做 |

- A级收入：2026-10-18重新只读核验上述10个产品的**公开HTML原页**，最近30天金额取产品页`<title>`实际展示，MRR从该产品页面元数据读取。来源平台声称Stripe、Polar、RevenueCat或LemonSqueezy付款API已连接，非本团队独立审计；不调用TrustMRR API。原页`Last updated`时间戳未指定时区，`source_last_synced`仅存日期，避免伪造精确UTC秒。
- MRR、last_30d及all_time彼此区分。累计收入若本次可读HTML未完整显示可直接复核数值，则设`null`并加flags；不沿用旧快照数字充作当天事实。
- `founded_date`为来源公开月份，规范化存当月1日，并标精度；上述产品即使按当月最后一日计算均超过90天。AI Toolbox成立2024年9月的月度信息来自开发者公司About页，标第一方自述，不充当T。
- Chrome Web Store / App Store原站核对：MyFeedIn 2,000用户档位、SuperX 10,000用户档位、AI Toolbox 40,000用户档位、TrueSearch美国App Store 134条评分、PracticeMe美国App Store 1条评分。档位是**下限不是精确计数**，不代表实际付费用户。TrueSearch独立App Store 134 vs TrustMRR转引124，保留差异。
- 其他5个T平台：Product Hunt（Compresto、RapidNative、Rooftops AI、Rezi）及Trustpilot（Blipix）本次动态访问被封锁或403；现有T指标记录来自此前审稿/历史缓存，**不能声明已在2026-10-18再次通过实时原页复核**。Hark必须在审稿时打开原页并确认数值。CI的链接格式测试不证明远端数字。
- 分布：浏览器插件3、小App2、开发者工具1、SaaS1、AI工具2、教育工具1；每类至多3，新项目全部收入≥$1,000。原有20条不修改。

## 淘汰、替换与审计重点
- **ExtraBar**：2026-10-18公开支付验证HTML标题显示近30天**$893**，不达$1,000硬门槛，从T10删除；改用`ai-toolbox`，其公开来源显示**$21,001**近30天、MRR**$1,334**、LemonSqueezy连接状态正常，Chrome商店有40,000用户档位。其原始数据单独审核。
- **PostNitro、FriendFilter/GroupFilter、Preuve AI**：支付连接或数据同步已过期，不以陈旧数据显示满足当前门槛。
- **HeyNews**：公开财务约$3,165，但业务包含代运营邮件内容的人工服务，存在T10「代理服务」排除风险，未选。
- **Cooldock**：第三方牵引力官方原页未完成核实，未选。
- **Rooftops AI**：仅74个Product Hunt关注者，1条创始人自评不作为独立客户评价；仍不能证明有付费客户。近期收入约$2,379且已挂牌$48,000，标风险。
- **TrueSearch**：人名/联系方式搜索有明显个人信息与App Store规范风险，开发商原文亦披露Apple guideline 5.1.1风险；Hark应审查是否实际触碰项目禁入合规边界。已挂牌$85,000。
- **Rezi**：规模$214,250/30天，不违反当前T10仅收入下限的明文规则，但远非普通个人早期产品，不适于不加区别的复刻建议。
- **AI Toolbox**：此类浏览器插件需高度重视AI聊天内容权限、隐私、安全、与平台条款。Chrome用户下限不等于真实活跃或订阅人数。

## 发布与权限闸门
- 新增10条严格`reviewed_by_hark=false`/`publication_status=PRIVATE_REVIEW_ONLY`；未获Hark批准和来源数据再展示许可前不得变为PUBLIC，不得合并main。生产模拟环境必须对10条fail-closed。
- `config/source_registry.json`仍将TrustMRR标为`YELLOW`、`redisplay_allowed=false`、`written_permission_required=true`。即使使用公开HTML而非API，也**不能将资料可公开浏览误读为批量再展示的许可**。法务/平台许可未解锁时不发布此批页面。
- JSON动态评分首页前三：`1clickwebsite-ai → sonar-aso-tool → 3dplotter`；无新增项目进入前三；旧20评分冻结。五维理由请逐条按JSON核对。
- GitHub Actions仅确认结构、网页生成、Chromium响应式及Lighthouse；Cloudflare Pages预览成功不等于Worker生产构建成功。真正平台使用许可、收入真实性、T日期必须另行人工审查。

## Hark剩余复核
1. 人工核对5条受限T原页当日显示值及归属，出现不一致则修改或淘汰，不可静默通过。
2. 核对TrustMRR公开页使用与再展示权利是否取得书面许可；无许可时禁止上生产。
3. 审核TrueSearch隐私和上架政策、Rooftops AI单薄T、Rezi项目规模适配性。
4. 审核10条`source_last_synced`时区日期、近30日来源标题数值与金额口径；Hark复核结束后才可能另行明确授权squash。
