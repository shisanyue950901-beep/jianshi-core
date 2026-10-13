# 见势 F2.1｜G2-H.7J：Cloudflare 多 Zone 只读可见性及公网暴露面审计

执行日期：2026-10-13。上阶段正式基线 `main=b7ff1406d0af443a23f9c6635e823bfff66af115`。

## 一、为什么新增本批

G2-H.7I 的 Cloudflare 只读 Worker/Pages 盘点可以接受一个可选的 Zone ID，但是**不能凭单一区域的 Route 数据推断其它 Zone 全部不存在**。此外，Cloudflare Worker 可以通过 account-wide Custom Domains、workers.dev 子域名、版本预览 URL、Pages 自定义域名暴露，这些入口不一定在指定 Zone Routes 中。

官方 API（2026-10-13 重新核验）：

- Worker Scripts 单页列表：`GET /accounts/{account_id}/workers/scripts`，需要 `Workers Scripts Read`。https://developers.cloudflare.com/api/resources/workers/subresources/scripts/methods/list/
- Pages Projects 分页列表：`GET /accounts/{account_id}/pages/projects`，需要 `Pages Read`。https://developers.cloudflare.com/api/resources/pages/subresources/projects/methods/list/
- Zone 列表：`GET /zones?account.id=...&page=...&per_page=50`，需要 `Zone Read`。https://developers.cloudflare.com/api/resources/zones/methods/list/
- 指定 Zone Routes：`GET /zones/{zone_id}/workers/routes`，需要 `Workers Routes Read`。https://developers.cloudflare.com/api/resources/workers/subresources/routes/methods/list/
- 账户 Worker Custom Domains：`GET /accounts/{account_id}/workers/domains`，需要 `Workers Scripts Read`。https://developers.cloudflare.com/api/resources/workers/subresources/domains/methods/list/
- 特定 Worker 的 workers.dev / preview 开关：`GET /accounts/{account_id}/workers/scripts/{script_name}/subdomain`，需要 `Workers Scripts Read`。https://developers.cloudflare.com/api/resources/workers/subresources/scripts/subresources/subdomain/methods/get/
- 特定 Pages 项目自定义域名：`GET /accounts/{account_id}/pages/projects/{project_name}/domains`，需要 `Pages Read`。https://developers.cloudflare.com/api/resources/pages/subresources/projects/subresources/domains/methods/list/

**所有这些 API 使用 GET，且不读取 Secret、证书私钥、用户数据、Worker 脚本正文，也不执行部署。**

## 二、交付文件与行为

`scripts/security/g2h7j_multizone_readonly.mjs` 复用 H7I Worker/Pages 只读客户端，另行按 Account ID 查询 Zone（要求 Zone 返回账号关联一致）、逐一查询所有 Token 可见 Zone 的路由，再查 account-wide Worker 自定义域名；若找到候选 Worker，额外核查 workers.dev 和版本预览 URL 是否 enabled；若存在主站或候选 Pages 项目，查询它们的自定义域名数量。

最重要的 **Fail Closed**：
- 若 API 授权不足（403）、错误账号混入 Zone、Zone 列表缺分页元数据或页码/数量矛盾，**直接失败**，不允许生成「无暴露」结论。
- 当前测试运行上限 10 个 Zone、40 个请求，遇到超过上限时失败关闭而不是悄悄跳过。由于 Cloudflare 的 Account API Token 只能看到它被授权的范围，即使这 10 个 Zone 都检查了，报告也只能标记 `TOKEN_VISIBLE_ACCOUNT_ZONES_ONLY`，**不能证明 Token 没权限看到的其它 Zone 不存在**。
- 返回字段只有是否检测到候选 Worker/Pages/Custom Domain/Route、数量、workers.dev 和 Preview 布尔状态；不会回显账号 ID、Zone ID、Token、API 原始响应、证书、域名、DNS 或 URL。
- 即使候选 Worker 未被找到，结果也是 `NO_CANDIDATE_SEEN_WITH_TOKEN_VISIBLE_SCOPE` 且 `safeToDeploy=false`，绝不当作生产上线授权。

`scripts/security/g2h7j_multizone_cli.mjs` 的默认运行 **0 个云端请求**；需要显式 `--remote-read-only`、`JIANSHI_H7J_REMOTE_READONLY_APPROVED=1` 和在受控运行环境中注入 `JIANSHI_H7J_ACCOUNT_ID` 与 `JIANSHI_H7J_READ_TOKEN` 才可能访问真实 Cloudflare API。**严禁将 Token、Account ID 或其值写入聊天、仓库、GitHub Actions CI 和终端命令参数。**

`tests/g2h7j_multizone_readonly.test.mjs`：验证有权限多 Zone、被隐藏权限的 403、跨账号 Zone 混入、Zone 计数不符、区域上限、没有完整分页、路由异常、Worker Custom Domains 分页不完整、候选 Worker 的 workers.dev/预览可用状态、API Token 和异常日志不泄露及无授权 CLI 零网络。

`scripts/security/g2h7j_multizone_audit.mjs`：与实现分离的代码静态审计，检查 GET-only、没有真实 Cloudflare API Token 进入 CI、无部署和生产路由修改、账号开关关闭、P4.41 四个 UTC 时槽保持不变，并确保 G2-H.7H 的十二项部署准入门禁仍全为关闭。

## 三、合规声明 / 未完成

本批 **没有** Cloudflare 账号连接或真实认证，也不会执行真实网络 GET。测试使用离线合成 HTTP Responses；真实 Cloudflare Worker/Pages/Zone/Custom Domain 的状态仍是 **NOT_CONNECTED / NOT_VERIFIED**。

不同的 Token 可能只看到不同的 Zone，所以即便未来运行此程序也仅是获得有限授权范围内的资产证据。要升级为正式发布准入，需要在严格分离的管理环境里独立审查全账号 Zone 权限范围与域名路由，检查真实 Workers mTLS、GoTrue 和服务角色。

本批 PR 安全门禁通过后可作为**研发工具**合并，但 **不等于同意或执行 Cloudflare Preview 部署**。Production 账号开关保持关闭，真实 Stage 的业务开关全关，绝不变更 P4.41 schedule、每天唯一采集 claim / HN≤7 / RSS≤1 / GitHub REST≤2 的限额，不触碰 #133 Draft PR。

审计是代码作者及自动 CI 自审，**不是独立第三方人工审计**。如果任何攻击测试 FAIL，必须修复、重跑并保留失败记录；不得强制合并。
