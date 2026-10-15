# T08｜新增项目准入与淘汰审计

> 检查日期：2026-10-15。新项目仅用 TrustMRR `.md` 中支付API连接收入、成立日期及DR快照；DR为Ahrefs估算牵引信号，独立客户数不推定。
> **Hark审核前状态：PRIVATE_REVIEW_ONLY，未视为公开审核通过；合并main前须由Hark确认并将新10条审核/发布标记正式批准。**

## 新增十条的统一核查口径

- 准入：至少一个TrustMRR `A`支付提供方API来源、成立至少90天、近30日滚动收入不低于$1,000。
- 每条都附A级支付记录来源及T级Ahrefs DR，标为estimated:true；DR是SEO估算信号，**不等于活跃用户、客户或收入确认**。
- 对2026-10-15来源页面MRR、30日收入与累计收入分别赋值，增长率读取公开md，客户数无唯一付费客户证明时为null。
- 评分渠道理由注明已公开的DR或X关注规模与推测渠道，不伪称已验证实际流量结构。
- 一次性买断产品显示MRR未公开；与2026-10-15的滚动收入分别列出，不混算。

## 排除候选（不少于五条）

| 候选 | 主来源 | 硬规则 / 编辑排除原因 |
|---|---|---|
| RankResume | [TrustMRR](https://trustmrr.com/startup/rankresume-778-verified-revenue) | 公开页累计收入仅$778，近30日为$0，低于$1,000门槛 |
| Taillens | [TrustMRR](https://trustmrr.com/startup/taillens-tool-for-frontend-developers) | 虽有浏览器插件与LemonSqueezy验证，近30日收入显示$0 |
| Rosewell | [TrustMRR](https://trustmrr.com/startup/rosewell) | 近30日约$812，未达$1,000硬门槛 |
| BlackStack | [TrustMRR](https://trustmrr.com/startup/blackstack) | Polar API key已过期，停留在2026-05-01旧同步，无法取得本轮有效收入快照 |
| Homy | [TrustMRR](https://trustmrr.com/startup/homy) | 2026-10-10才成立，明显不足90天；T04已剔除 |
| TechScreen | [TrustMRR](https://trustmrr.com/startup/techscreen) | 业务营销含面试期间实时协助内容，已有编辑伦理排除决定 |
| 9x12tools.com | [TrustMRR](https://trustmrr.com/startup/9x12tools-com) | 官方.md路径本轮返回404，缺少可逐字段复核的当日成立日、滚动收入快照，不凭旧目录合计代填 |
| TopExtension.lol | [TrustMRR](https://trustmrr.com/startup/topextensionlol) | 2026年8月成立，未满90天且最近收入$0 |
| PromptDC | [TrustMRR](https://trustmrr.com/startup/promptdc) | 公开近30日约$173，未达准入收入门槛 |
| API Plugin | [TrustMRR](https://trustmrr.com/startup/api-plugin) | 近30日$0，虽有Stripe验证和DR20但不合收入规则 |

## 待Hark复核重点

- 1clickwebsite.ai和3dplotter评分≥20是研究判断，并非确认创业成功率。
- 1DevTool、AEO Checker收入处于$1,000–$1,500，已加临界标记。
- 1DevTool公开1人团队字段缺失，其他多条同样未披露团队人数；统一`team_size=null`，网页显示“未公开”，不可推断为一人创业。
- 新10条`reviewed_by_hark=false`、`publication_status=PRIVATE_REVIEW_ONLY`。仅允许`feat/t08`预览路由构建，主分支生产输出遇到未审核数据应FAIL_CLOSED。
- 首页与/discover同一算法以`total_score`降序、`last_30d`降序、`id`升序排序，前三由构建时JSON计算，页面不硬编码名称或收入。
- 本审计是公开来源核查摘要而非付款流水、团队身份或第三方牵引独立鉴证。

**审核结论：提交 Hark 逐字段复核；执行层不得自行合并。**
