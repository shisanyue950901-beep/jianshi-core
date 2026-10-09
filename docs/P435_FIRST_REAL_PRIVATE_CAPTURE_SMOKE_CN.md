# P4.35｜首次真实 HTTP 采集烟雾测试与自动验收

**2026-10-09**。继承 P4.34 的隐私、费用、站点发布与 SEC 身份门禁。用户目标：从“测试通过但实际联网未验收”升级到“已有可复查的真实网络诊断”。

## 本轮先查到什么

- 主分支 P4.34 commit `40f7c9d6`、其后静态快照 commit `6aeb8805`；合并后 CI/Static Snapshot PASS。
- 曾查询最后可见的旧 `schedule` run `37895607353`（在 P4.34 合并之前），**artifacts = 0**。不能将这一 run 当成新链路的成功采集。
- 2026-10-09 该会话沙箱直接访问 hn.algolia.com、usefathom.com、data.sec.gov 的 DNS 均失败；不再用相同网络冒充在线采集成功。
- Fathom 正式博客页面明确提供 RSS，链接指向 `https://usefathom.com/blog/feed.xml`，RSS 返回内容尚须 GitHub Runner 在线验证。
- GitHub `gh run download` 可以取指定 run 的内部 Artifact（需 actions:read），此前 P4.34 的恢复路径尚缺少真实 scheduled 验收。

## 一次性、无额外 Actions 作业的安全方案

沿用原有 `.github/workflows/publish-static.yml` **在每次 merge 到 main 时就会触发的 push 静态构建 job**。只有当被合并的**完整提交标题以确切的** `P435_PRIVATE_SMOKE_ONCE_20261009` 开头时：
- 原本 push 构建中不会运行的“研究采集”步骤**在该唯一合并提交里临时执行**；
- HN 检索缩为 **最多 1 家 + 1 个话题 = 2 次 HTTPS 请求**；Fathom 官方 RSS 仍最多 1 次固定来源 HTTPS 请求；没有外部源重试、不访问搜索结果正文；
- 仍执行 P4.30 / P4.33 / P4.34 离线审查、清洗、同批和跨日去重，私有 JSON 数据按原有 48 小时 Artifact 保存；
- Bot 后续自动提交 `chore: refresh live static snapshot` 不匹配此标题，因此不会再执行该 smoke；正常日计划仍沿用唯一 UTC 00–01 时段的同一采集逻辑。
- **零新增 cron、job、第三方 API 凭证、付费插件或重复计费工作流**；需要注意现有 GitHub Actions 私仓余额仍未核实，不能保证总账单为 0。

**这次 smoke 是真实一次性网络尝试，不是新增常态采集频率。** 若其失败，产物应保留真实失败统计，而不算业务数据成功。若某个前置关键脚本抛异常，整个研究 step 会失败，需定位其日志修复，不能在报告中称其完成。

## 独立机器健康报告

新增 `scripts/research/p435_private_scan_health.py`：
- HN `network_requests_attempted/successful/failed`，RSS `P434_RSS_HTTP_OK` 或 `P434_RSS_ACCESS_FAILED_NO_RETRY`，历史指纹 `P434_PRIOR_HASH_INDEX_RESTORED` 或明确的失败/冷启动原因；
- 跟 P4.34 的 `source_http_status`、`previous_index_available` 做交叉一致性校验，遇到“报告声称成功但请求统计全败”则失败；
- 输出 `p435_scan_health.json`（放在原来的 48 小时私有 research-leads Artifact 里）；
- 在 Actions 的 **Step Summary** 只展示请求成功/失败数量、清洗条数、历史指纹数量、是否冷启动。不会展示文章正文、可能的支付数据、URL、个人联系信息或原始研究数据。
- 完全离线，新增网络请求=0，对外收录=0；不允许自动判断收入真实性。

## 真实验收条件

验收者必须查看 **main 上该一次性 merge 所触发的 `JianShi Static Snapshot` run**，以及它对应的 `research-leads-<run-id>` artifact：

1. `Daily private business-evidence leads` 步骤**真实执行而不是 skipped**。
2. step summary 中有 `真实 HTTP：尝试 N，成功 M`；对 HTTP 失败明示 `NO_HTTP_SUCCESSES`，不得把运行成功等同抓取成功。
3. HN 请求上限 <=2、RSS <=1；`p435_scan_health.json` 内 `http_attempts_total <= 3`，`financial_claims_verified=0`。
4. 如果 artifact 里没有上一份指纹，跨日对比必须 `FIRST_INDEX_BASELINE_NO_TREND`。
5. `web/dist/projects` 仍只有 Carrd/NerdWallet/Plausible；源代码、研究 JSON、历史 SHA 表和原文均不得进入公网发布。
6. 后续第一次真正 `event=schedule` 的每日请求预算仍严格 HN<=7、RSS<=1，单次采集的成功不得推定另一时段也成功。

## 尚未完成

- SEC 公共官方 API 真实线上采集：必须提供有效真实操作者邮箱的 User-Agent；不能伪造，也不能从个人资料猜测。
- 48 小时以外的长时间持久化数据：不修改 Supabase 生产或额外付费存储来实现。
- R3 企业法律实体/报告期/币种/经营收入数据交叉确认，R5 一人创业可复制需求验证，仍不能自动晋级公开榜。
