# P4.37｜新增第10类来源：GitHub 官方公开 REST API（严格归属校验）

**2026-10-09**。本轮只接入**真实有官方接口、来源可归属、成本限额可控**的元数据来源，不把一般技术动态误写成营收证据。继承所有受限平台禁爬、研究不入公网、Production 零写入和 L3/L4 人工审核门禁。

## 本次增加的是什么

原始 `config/p432_source_access_matrix.json` 为9类来源，P4.37原地升级为 `P437_PRIVATE_SOURCE_ACCESS_V2`、**10类**。新增1类：`github-official-repos`（GitHub 官方 REST API）。其中只有两家来源渠道曾由真实联网采集验收：HN Algolia、Fathom RSS；本次作为**第三条无人值守通道**接入 GitHub API，但需要首次 scheduled Runner HTTP 产物验收后，才能从“代码已接入”改为“日常已验收”。

GitHub 官方速率限制政策：https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api 。GitHub Actions 自带 `GITHUB_TOKEN` 对应仓库一般有每小时请求上限，**不因此承诺账号运行免费**。

### 采集两个固定仓库，原始身份已核对

2026-10-09 通过 GitHub 官方接口实时检查：
- `https://api.github.com/repos/plausible/analytics`，官方 `plausible` 组织，仓库ID **160427405**，项目地址 `https://github.com/plausible/analytics`，官网 `https://plausible.io`。
- `https://api.github.com/repos/plausible/docs`，同一官方组织，仓库ID **270703311**，项目地址 `https://github.com/plausible/docs`，官网 `https://plausible.io/docs`。

两者均须是 Public、非 Fork、未归档、未禁用，ID、组织 login 和官方 homepage 逐项匹配才入私有报告。不自动把“同名仓库”或第三方 fork 当成官方证据。仅核对它们作为技术项目的官方仓库身份，**并未核实公司的法定法律实体**。

### 新脚本

`scripts/research/p437_official_github_repo_probe.py`：
- 默认无请求；必须 `--online` 才访问；只允许2个固定 GET `api.github.com/repos/...`，各6秒超时、单个响应最高128KiB；
- 接受 GitHub Action现成 `GH_TOKEN` / `GITHUB_TOKEN`，不会把token写入输出；HTTP 403/429 立即停止，不改身份/代理重试、不搜其他仓库；
- 强制校验 exact repo ID、organization、repo url、homepage、public/fork/archived/disabled 属性；
- 只保留项目创建、最近仓库更新与推送时间、stars、forks、GitHub open issues计数，原始响应不归档，仅保存SHA256供取证；不读取issues、贡献者身份、原始代码或README全文；
- 输出数据 `contract=P437_PRIVATE_GITHUB_REPO_METRICS_V1`、`financial_claims_verified=0`、`publication_allowed=false`；**GitHub issue数含PR等计数口径，不能当作销量、用户或项目热度可信商业指标**；
- 不在仓库中输出报告；只写 `$RUNNER_TEMP/p437_github_metrics.json`，与原有48小时 `research-leads-<run-id>` 私有artifact一起打包。
- 失败时写内部错误代码及 Actions warning，不虚报成功，也不影响 HN/RSS 主链的独立验证。

### 运行频率与费用

沿用之前唯一的UTC 00:55左右私有每日研究时段，原workflow数、cron数均不变：
- HN最多7个外部HTTP；
- Fathom RSS最多1个外部HTTP；
- GitHub REST最多**2个外部HTTP**；
- **合计上限10个来源请求/日**，无自动重试/升级套餐/付费插件。

**注意：**工作流还调用原有 GitHub Artifact 列表接口与可选历史产物下载，这些是内部运行所需的 GitHub API 调用，不包含在10个“数据来源 HTTP 请求”预算中。现有P4.36的健康判定针对HN+RSS这**8次来源请求**，GitHub第三来源另有单独的实际有效仓库计数和warning，不能把P4.36 PASS当成三个来源全部通过。

### 验收边界

代码单元测试采用精确模拟fixture，绝不声称fixture是GitHub的实时取证。真实GitHub API调用已通过连接的官方GitHub接口独立复核上述两仓库的身份；**计划任务首次执行新脚本仍待验收**。

不得因两个仓库更新或star增长宣称Plausible的2026年收入变化，更不得将公开开发活动当成适合普通人复制的低资金创业方案。

### 待继续扩容的来源

- SEC EDGAR：已有按需采集器，但没有真实的操作者联系邮箱授权，不自动添加日采集；
- Plausible/Buffer编辑内容：未明确证明批量抓取许可，仅保留人工核实的经营描述；
- Acquire、Flippa、Microns、Indie Hackers：未获得许可，不抓受限挂牌或全文。

下阶段再引入具名公司的经营原始证据、官方定期申报与合法数据分发接口，附法律实体、申报期间、数据币种和真实校验；默认一律保持私有待审核。
