# P4.34｜低频真实 RSS 采集 + GitHub 私有产物跨天去重

**2026-10-09 实施说明**。P4.33 完成确定性清洗，但尚未由任何新版本真实 scheduled 任务验收；本变更新增受控的官方 RSS 实时尝试、可恢复的跨日指纹并标记冷启动。**不能以 PR/CI 成功替代外部 API 成功。**

## 新的采集范围（不突破网站原有研究和发布边界）

- HN Algolia：沿用 P4.26 现有每日最多 6 家 + 1 话题，即 7 次 HTTPS 尝试，不重试、不访问搜索命中网页正文。
- Fathom Analytics **官方明确提供的 RSS**：原 `p432_publisher_rss_probe.py` 从按需改为**现有每日研究槽内最多 1 次请求**，官方 RSS 链接 `https://usefathom.com/blog/feed.xml`；固定域名、禁止重定向、6 秒超时、最多 256 KiB 响应/10 篇元数据。只取标题、日期和官方链接，不缓存文章全文。若请求失败，写健康状态 `P434_RSS_ACCESS_FAILED_NO_RETRY`，不会退化为搜索引擎抓取。
- SEC EDGAR：继续冻结在 P4.31 按需模式。SEC 公共 API 的 User-Agent 要求真实有效联系邮箱；目前未获授权自动运行身份，**不提交虚构邮箱、不自动调用 SEC**。
- 其他编辑性网页：Buffer、Plausible 等仍人工核对，未获自动批量采集许可。
- Acquire、Flippa、Microns、Indie Hackers：维持禁止未经许可的自动内容提取，不借用 HN 索引间接下载挂牌。

## 端到端流水线及运维

**复用已有** `.github/workflows/publish-static.yml` 的 `cron: '55 */6 * * *'`，并且仅在 UTC 00—01 时段内触发日采集。没有新增 cron、额外 GitHub job、外部数据库、收费 API、TinyFish 或昂贵的重试。

```text
原每日研究时段（运行在隔离 GitHub Runner）
   │
   ├── HN Search（7 次以内）
   │     └─ p426_research_leads.json  / HTTP 真实成功失败计数
   │
   ├── Fathom 官方 RSS（1 次以内）
   │     ├─ 成功 → p432_rss_leads.json（仅元数据）
   │     └─ 失败 → p434_rss_health.txt（失败、零重试）
   │
   ├── P4.30：具名公司身份疑点内部审核队列
   ├── P4.33：统一字段清洗/HTTPS 来源核验/链接去重与隔离
   │     └─ p433_clean_review.json
   │
   ├── 读取同仓库上一份还未过期的 research-leads-<run-id>
   │     ├─ GitHub 自带 GITHUB_TOKEN（只读 actions:read；不需 PAT）
   │     ├─ prior/p434_hash_index.json（仅指纹与首末见日期）
   │     ├─ 失效、权限不可达、第一次运行 → 明示冷启动
   │     └─ 拒绝其他分支、当前 run、非法名称、过期的产物
   │
   ├── P4.34 纯离线历史指纹合并
   │     ├─ p434_daily_delta.json（统计新见/重复）
   │     └─ p434_hash_index.json（最多1,200条SHA-256、45天时窗）
   │
   └── 上传到 **原同一个** 私有 artifact（48小时保留）
         不写入 web/dist，不写 Supabase 生产，不自动晋级公开案例
```

### 跨天去重的准确含义

- **只有读取到之前有效的 `p434_hash_index.json` 才有跨次可比性。** 否则 `status=FIRST_INDEX_BASELINE_NO_TREND`，不会将初次看到的数据假称“今天新增”。
- `new_since_available_index` 只表示 URL 的 SHA-256 在上一份可用指纹库里缺失，并不等于新公司、新创收、某站真实交易或法定新增商业机会。
- 状态保存在已有的 48 小时私有 artifact 内。若调度持续中断超过保留期限，历史会丢失并回到首轮模式；**不是永久备份**。指纹逻辑窗口 45 天，并不意味着 GitHub 会保存 45 天的原始档案。
- `p434_hash_index.json` 只保留 `hash`、`first_seen`、`last_seen`，没有原始 URL、公司、文章标题、交易数据。原始最少量元数据仍在短期审核 artifact；后续若需长期追踪要另外设计经过预算审核的私有存储。
- `source_http_status` 明确区别 `AT_LEAST_ONE_LIVE_HTTP_SUCCESS` 和 `NO_LIVE_HTTP_CONFIRMED`；HTTP 成功并不代表财务指标真实。

## 与权限/费用相关的改变

- 工作流现有 `permissions: contents: write`，为同仓库历史 artifacts **增补 `actions: read`**，没有 Production 数据库密钥和第三方授权 token，`GH_TOKEN` 不进入数据文件或日志。
- GitHub 官方 `gh run download` 可用来读取之前的工作流 artifact；无须添加独立缓存服务，也不新增 cron，但旧版 run 或权限故障导致冷启动。
- 每日最大公开 HTTP 请求预算由 **7（仅 HN）提高到 8（HN 7 + Fathom RSS 1）**；只有现有每日时段发起。实际 GitHub 私有 Actions 分钟/执行帐单仍无法直接核实；即使无新增 workflow，其既有工作流也可能产生平台执行费用。
- 不用 App 浏览器、抓取受限市场、Cloudflare 数据库、Supabase 表修改、额外免费套餐假设。
- 对公开站的验收：只有原 Carrd/Plausible/NerdWallet 可进入 `web/dist/projects`，严禁发布任何上述 RSS/API 清洗数据。

## 首次运行验收清单

在**合并后的第一次真正 `event=schedule`** 执行完毕后：
1. 核对运行 job 的 `Daily private business-evidence leads` 实际不是 `skipped`，查看 `P434_RSS_HTTP_OK` 或 `P434_RSS_ACCESS_FAILED_NO_RETRY`。
2. 查看 `research-leads-<run-id>` 私有产物是否包含 `p426_research_leads.json`、`p430_review_queue.json`、`p433_clean_review.json`、`p434_daily_delta.json`、`p434_hash_index.json`。
3. 审核 `network_requests_successful` / `failed`、RSS HTTP 成功状态、被隔离违规来源、拒收和相同URL合并情况。不能只看 GitHub 运行绿灯。
4. 如果此前没有本版 hash index，应得到 `FIRST_INDEX_BASELINE_NO_TREND`，第二个有效日扫描才能得到 `COMPARED_WITH_PRIOR_INDEX`。
5. 不保存用户联系方式到产物；不对外公开研究线索或放宽 L3/L4 准入。

**当前阶段记录**：本轮开发前，容器 `hn.algolia.com`、`usefathom.com`、`data.sec.gov` 均无法 DNS 解析；本 PR 仅将可复现实时采集尝试交给 GitHub scheduled runner，不能预测其网络是否成功。首次真实数据仍以 scheduled artifact 为准。

## 后续建设

- P4.35：只有首次真实 GitHub 扫描产物验收后，才扩大合法官方 API/RSS 的来源与长期存储；根据动作频率和账单预算调整。
- 原始财务 L4 SEC/审计财报和 L3 有归属创始人收入陈述需要主体、周期、货币、审计/自报性质的双重核验；发掘研究线索不等于正式证明可复制创业机会。
