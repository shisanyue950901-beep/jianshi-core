# T08b｜20 条存量项目多源与牵引力证据补全审计

核对日期：2026-10-16（T08b）｜收入快照截止：2026-10-15（T08，未修改）｜用途：仅以公开网页补充佐证，不调用 TrustMRR API，不读取 private/。

## 本轮实际完成范围

- 20/20：保留原有至少一条 A/A- 支付来源公开详情 URL、历史 checked_at、T 级来源及 traction URL；全部填写 4.1.1 的同源交叉验证和未知客户集中度风险标记。
- 15/20：新增一条可指向公开页面的 T 级指标。其中 **8 条**第三方平台、**7 条**官网自述/转引。**第三方平台 T 不等于独立 A 级收入**。
- **5/20**：尚缺可充分复核的独立外部 T 数值，明确维持缺口并保留历史 last_verified_at，不做假补齐：search1api、advanced-gsc-mcp、adscriptly、saashunt、5-day-sprint。
- 仅对实际核对了新增公开 T 页面且写入该值的项目更新 last_verified_at=2026-10-16；其余 5 条继续保留已记录的 2026-10-15 历史核对日。**这不意味着 10 月 16 日完成财务复核。**
- 收入金额、source_last_synced、公司成立时间、scores、total_score、verdict、原 flags、public_ready/发布状态和首页推荐排序保持不变。

## 公开 T 级证据工作底稿

| 项目 ID | 新增 T 级公开线索 | 可核查网页 | 类型/限制 |
| --- | --- | --- | --- |
| datafast | Product Hunt 3 条评价 | https://www.producthunt.com/products/datafast | 第三方平台 |
| shipfast | Product Hunt 52 条评价 | https://www.producthunt.com/products/shipfast/reviews | 第三方平台 |
| turbostarter | 团队关联开源仓库 Loading UI：470 stars | https://github.com/turbostarter/loading-ui | 第三方平台；**仅团队开源作品，不代表商业 SaaS 用户** |
| sonar-aso-tool | 官网称 227 indie developers | https://trysonar.app/ | 第一方营销自述 |
| agentskit | 官网称 35 builders | https://agentskit.co/ | 第一方营销自述 |
| opentweet | 官网客户案例声称个别客户月发 400–1000 篇 | https://opentweet.io/ | 第一方案例；非平台总量 |
| getebook-ai | 官网称 12,000+ creators | https://getebook.ai/ | 第一方营销自述 |
| mastros | 官网博客称 2026-09-02 扩展有 71 条评价 | https://www.mastros.online/blog/is-mastros-safe | 第一方转引；**未直接核对商店** |
| readlens | Google Play 显示 500+ 下载档位 | https://play.google.com/store/apps/details?id=com.snapvoiceai.app | 第三方平台；下限而非精确数量 |
| 1devtool | GitHub 发布仓库 11 stars | https://github.com/stoicsoft/1devtool-releases | 第三方平台；动态值 |
| 1clickwebsite-ai | 官网称累计生成 5,000+ 网站 | https://www.1clickwebsite.ai/ | 第一方营销自述；非真实付费用户数 |
| 3dplotter | Trustpilot 4 条评价 | https://www.trustpilot.com/review/3dplotter.xyz | 第三方平台 |
| aeo-checker | 官网称 56,500+ 网站完成分析 | https://www.aeochecker.ai/ | 第一方自述；检测次数不等于付费用户 |
| ai-designer | Product Hunt 116 位 followers | https://www.producthunt.com/products/aidesigner | 第三方平台；关注人数不等于付费 |
| 3d-agent | Trustpilot 12 条评价 | https://www.trustpilot.com/review/3d-agent.com | 第三方平台 |
| search1api | 未获本次可信站外计数 | — | 缺口已在 flags 留痕 |
| advanced-gsc-mcp | 未获本次可信站外计数 | — | 缺口已在 flags 留痕 |
| adscriptly | 未获本次可信站外计数 | — | 缺口已在 flags 留痕 |
| saashunt | 未获本次可信站外计数 | — | 缺口已在 flags 留痕 |
| 5-day-sprint | 未获本次可信站外计数 | — | 缺口已在 flags 留痕 |

以上公开数值是核对时刻的网页观测或可明确归因的官网主张。**Product Hunt、GitHub stars、Google Play 下载和 Trustpilot 评价均为动态指标**；审核者应以实际打开页面复核为准，若页面已变化，记录新时间而不是偷偷改写历史值。未访问 TrustMRR API，也没有独立重新审计历史收入快照。

## Hark 五条抽查优先样本

1. DataFast：收入来源 https://trustmrr.com/startup/datafast ；第三方 T：https://www.producthunt.com/products/datafast （3 条评论）。
2. ShipFast：收入来源 https://trustmrr.com/startup/shipfast ；第三方 T：https://www.producthunt.com/products/shipfast/reviews （52 条评论）。
3. ReadLens：收入来源 https://trustmrr.com/startup/readlens ；第三方 T：https://play.google.com/store/apps/details?id=com.snapvoiceai.app （500+ 下载）。
4. 3DPlotter：收入来源 https://trustmrr.com/startup/3dplotter ；第三方 T：https://www.trustpilot.com/review/3dplotter.xyz （4 条评论）。
5. 3D-Agent：收入来源 https://trustmrr.com/startup/3d-agent ；第三方 T：https://www.trustpilot.com/review/3d-agent.com （12 条评论）。

核对内容：页面可打开、产品主体确为该项目、数值及类别一致；A 级收入仍需区分支付提供方、更新时间和上游独立性。若五条中任意一条数字已变化，保留时间信息并按真实页面修订后再通过 Hark 验收。

## P4.1.1 交叉核验风险结论

- 所有 20 条都含 TrustMRR 主链接和对应的 `.md`：**同一平台的双 URL 不是两个独立 A 来源**。平台称与支付 API 连接，并不意味着见势独立审计；2026-10-16 未刷新真实收入。
- 独立 2 个 A 来源发生 **>20%** 数值差异才用较近同步记录、标「来源不一致」。本轮多数没有合格的双 A 同期证据，因此不可错误触发此规则，也不可标为双来源完成。
- 原有 `revenue.source_last_synced` 均为 2026-10-15；本轮不改动，随时间超过 30 日应标「待更新」，超过 90 日不得上首页。
- 数据未能排除单一大客户、仅 1–2 位付费客户、同一 Stripe 账号分摊多产品的可能；统一在 flags 显示 **风险待核实**，未把它们描述成已发生的事实。
- 历史收入和牵引力的合理关系仍需人工判断。第一方官网数值不视作付款证明；流量/星标/评价/安装数不能代替净营收。
- **不调用 TrustMRR API、不采集私有用户资料、不生成复制或推荐数据源**。未更新任何 private/ 文件。

## 回归验收合同

- 20 条唯一 id，原有支付来源 checked_at、T sources / traction 均保留；新数据增补不修改历史口径。
- 首页前三严格为 `1clickwebsite-ai`、`sonar-aso-tool`、`3dplotter`。
- 由 `tests/test_t08b_sources.py` 执行离线结构/来源检查；由原有 T08/T07 全套、`publish-static.yml` `build-static` 与 GitHub CI 校验。
- 此 PR **仅供审核，未经「Hark 已批准，请 squash 合并 #编号」不得合并**。
