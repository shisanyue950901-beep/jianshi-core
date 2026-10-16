# T09｜见势 4.1.1 交叉验证清单及 TrustMRR 条款摘要

更新：2026-10-16。依据：《见势 JIANSHI 4.1｜新对话完整工作交接》（2026-10-14，附录 A **最新计划** §4.1–§4.2）、仓库 `docs/P41_SIGNAL_SOURCE_EXPANSION_AUDIT.md` 与 `config/source_registry.json`，以及 TrustMRR 官方文档和条款。

## 4.1 证据分级与来源许可是两回事

- **A**：支付后台直接验证；TrustMRR、IndiePage Revenue Verified、Indie Hackers Stripe-verified、ShowMRR、StartuPage、Dodo Index、Baremetrics Open Startups、Prooov、OpenMRR、RevMRR。**必须逐条核实付款连接及徽章，不能因为出现在该网站就自动视为 A。**
- **A-**：交易平台验证的公开摘要；Acquire.com 公开挂牌、Flippa 公开挂牌、TrustMRR 在售。**只允许在对应授权范围内使用**，尤其 Acquire/Flippa 在仓库注册表为 RED，不得自动采集。
- **B**：带确切数字和日期的创始人自述；Indie Hackers self-report、Starter Story、创始人博客与公开 Dashboard。只能称「创始人自述」，不得称「验证」。
- **T**：非收入的牵引力；Chrome Web Store、App Store、Google Play、GitHub stars/提交、Product Hunt、Ahrefs DR、Similarweb 流量估算（必须标「估算」）。T 不能用作收入证明。
- **C**：X/Reddit 截图、二手转述、无日期数字等只作线索，**不入库**。
- GREEN/YELLOW/RED 是 **采集、再展示及授权策略状态**，不是上述 A/A-/B/T 证据强度。P4.1 的 npm、Stack Exchange、HN、Product Hunt、Reddit、Google Trends 扩容名单属于另一条 Shadow 信号链，未经审批不作为已验证收入。

## 4.1.1 交叉验证规则——按 4.1 原文逐项验收

- [ ] **收入证据**：至少一个 A/A- 级来源；如果存在两个独立 A 级来源且数字差异超过 **20%**，采用较新、同步时间较近的数值，并标注「来源不一致」。相同上游支付账户的不同平台不自动算独立证据。
- [ ] **新鲜度**：记录 TrustMRR 详情页的 **Last updated** / 源同步时间。A 级同步超过 **30 天**标「待更新」，超过 **90 天**不得上首页。无法证明同步时间的候选暂不通过该项。
- [ ] **财务口径**：MRR、最近 30 天收入、累计收入分别记录；一次性付款不计入 MRR。TrustMRR API 货币字段是**美分**，转换为 USD 时除以 100；卖方要价与利润不可冒充营收。
- [ ] **可信度风险**：对仅 **1–2 个付费客户**、单一大客户、多个产品共用 Stripe 账户等情况添加风险标记；无法验证时不能伪称无风险。
- [ ] **牵引力佐证**：每条待发布项目至少一个独立的 **T** 级信号，并判断收入是否与使用量匹配。仅有 B 或 T 级证据不能称为收入已验证。
- [ ] **审核及权限补充**：只在完成授权检查、来源链接复核和 Hark 审核后才可能单独讨论发布。T09 无权修改 `data/projects.json`、`public_ready`、网站首页前三或自动选题/评分。

## TrustMRR Terms §9 核对摘要

官方原文：<https://trustmrr.com/terms>（Last updated: 2026-07-28；本次核对 2026-10-16）。API 文档：<https://trustmrr.com/docs/api/list-startups>。

- **§9.1**：允许合法、善意、创造独立价值的用途，举例含获授权账号的**私人收购研究、内部分析**，不等于开放任意内部商业用途。
- **§9.2**：API Key 不授予公开发布、SEO 索引、再许可、销售、转售或对第三方开放数据的许可。公开展示、批量导出、再发布、面向客户的产品需要事先书面许可。
- **§9.3**：禁止克隆或重建 TrustMRR、基于其数据识别供用户复制/模仿/逆向业务、系统性抓取归档其数据库、规避限制；未经书面许可也禁止将数据用于 AI 模型、训练/评估数据集、搜索索引、推荐系统或自动内容生成。
- **§9.4–9.5**：密钥只供所属账号并应保密，不得使用代理/其他账户规避封禁；严重违规可能导致永久封禁及删除数据。

**重要冲突提示**：见势 4.1 的海外项目对标、可复刻性评分及候选自动推荐，如依赖 TrustMRR API 数据，可能触及 §9.3 的明确禁止项；即使网站当前没有用户也不自动豁免。T09 **仅交付技术实现和离线 Mock 验证**；不得将真实 API 数据导入见势项目库、对标/克隆评分、AI 数据集或推荐系统。若实际使用目标不属于许可范围，必须先取得 TrustMRR 明确书面授权，不能用更换账号、接口或代理绕过。

## 计划 4.2 候选 JSON 的对应关系

- 外层：`schema_version`、`source`、`collected_at_utc`、`pages_fetched`、`candidates` 与私有用途声明。
- 每条候选保留 `matched_queries`、`source_url`、原始计量值转换后的 `mrr_usd` 等有限元数据，并提供 **`project_draft_4_2`** 对象，具有计划 §4.2 全部字段：
  `id,name,url,category,one_liner_cn,target_user,revenue,evidence_level,sources,traction,flags,for_sale,business_model,price_point,acquisition_channels,tech_stack_guess,scores,total_score,cn_angle,risks,reviewed_by_hark,last_verified_at,updated_at`。
- `revenue` 保持 `mrr,last_30d,all_time,currency,as_of,verified_by,source_last_synced`；`for_sale` 保持 `listed,asking_price,multiple,url`；`scores` 保持计划的五项评分。金额以 USD 数字输出，未知为 null。
- **不得推测补值**：API 列表无准确源同步时间、T 牵引力、中文定位、评分或 Hark 审核，统一留空/false 并添加待验证 flags。4.2 草稿不是批准发布的项目记录。

## 使用规范

默认三个查询：`sort=growth-desc`、`sort=listed-desc`、`onSale=true`；各最多 3 页、每页最多 10 条，请求间隔至少 6.5 秒；429 按 `X-RateLimit-Reset` 重试。仅 `TRUSTMRR_API_KEY` 环境变量保存账号密钥，代码、日志、仓库、CI 均无明文密钥。

```powershell
# 仅在已确认符合 §9 的私人收购研究用途且账号获 API 授权时运行。
$env:TRUSTMRR_API_KEY = Read-Host 'TrustMRR API key'
python scripts/collect/fetch_trustmrr.py --pages 3 --limit 10
```

无密钥立即退出、不请求网络；仅写 git 忽略的 `private/trustmrr/candidates_YYYY-MM-DD.json`。不得通过 `git add -f` 将私有输出上传；不自动运行、不设定时任务。
