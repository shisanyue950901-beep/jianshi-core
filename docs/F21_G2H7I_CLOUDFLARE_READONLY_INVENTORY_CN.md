# 见势 F2.1｜G2-H.7I：Cloudflare 资产只读盘点工具与未部署准入交接

日期：2026-10-13；基线 `main=37967482ebd0d88b0ccf3d34c7d70851b2d37f80`。本批起点 G2-H.7H 只证明发布准入**拒绝未授权部署**，并不证明真实 Cloudflare 账号中的现有 Worker、Routes、Pages 已完整清点。

## 1. 已开发内容

- `scripts/security/g2h7i_cloudflare_readonly_client.mjs`：Cloudflare 官方 API、固定主机 `https://api.cloudflare.com`；只允许 GET：`/accounts/{account_id}/workers/scripts`、`/accounts/{account_id}/pages/projects?page=N&per_page=25`，另可显式提供 `zone_id` 时调用 `/zones/{zone_id}/workers/routes`。正式 API 文档：
  - https://developers.cloudflare.com/api/resources/workers/subresources/scripts/methods/list/
  - https://developers.cloudflare.com/api/resources/pages/subresources/projects/methods/list/
  - https://developers.cloudflare.com/api/resources/workers/subresources/routes/methods/list/
- 接口使用单独的 `EXPLICIT_REMOTE_READONLY` 执行模式、内存中短期读取 API Token、严格账户/Zone ID 格式和请求 GET 白名单；全部请求 `redirect:error`、`cache:no-store`、12s 以内超时（当前实现为 9s），不读取 Worker 脚本源码、证书材料、账户 Secrets、Pages 上传令牌或部署构建日志。所有结果经字段白名单归一化，仅输出资源数量、候选 Worker/Pages/Route 是否存在和权限覆盖程度。
- Pages 项目使用分页并对不可完成的分页失败关闭；Workers 与指定 Zone 路由如果 API 宣告存在额外页，会明确拒绝把局部结果冒充完全清单。**Zone ID 未提供时，报告为 `ACCOUNT_ONLY_ZONE_UNVERIFIED`**。
- 候选名称 `jianshi-cms-auth-admission-locked` 或对应路由/Pages 项目存在，报告 `EXISTING_WORKER_OR_ROUTE_REQUIRES_MANUAL_REVIEW`，永远 `safeToDeploy=false`；不存在也只能声明 `NO_TARGET_SEEN_IN_LIMITED_READONLY_SCOPE`，不能宣称已允许部署。
- `scripts/security/g2h7i_cloudflare_readonly_cli.mjs`：默认运行 `node scripts/security/g2h7i_cloudflare_readonly_cli.mjs` 时**零网络请求**，返回 `G2H7I_REMOTE_INVENTORY_NOT_CONNECTED`。只有人工明确设定运行环境中的 `JIANSHI_H7I_REMOTE_READONLY_APPROVED=1`、只读 Token、Account ID 与可选 Zone ID，且显式加上 `--remote-read-only`，才会执行 GET。**不得把这些值写入 GitHub、聊天、终端参数、仓库或日志**。
- `tests/g2h7i_cloudflare_readonly.test.mjs`：合成 Request/Response 接口检查，覆盖 GET-only、无默认远程调用、真实权限缺失和 API 故障失败关闭、候选 Worker/Route 冲突、Zone 省略、Pages 两页枚举、账户格式和输出摘要不泄漏 ID/令牌。
- `scripts/security/g2h7i_cloudflare_readonly_audit.mjs`：独立代码审计，禁止 HTTP POST/PUT/PATCH/DELETE、部署 API、脚本发布、GitHub CI 真凭据/真账号连接、主站发布污染，复核 H7H 拒绝上线以及四时段 P4.41 研究流程。

## 2. 权限与 Cloudflare 现实执行条件

以下是官方 API 对应的最小只读权限：`Workers Scripts Read`、`Pages Read`、如指定 Zone 则 `Workers Routes Read`。绝不分配 Write、Deploy、Secrets Write 或 Account Super Administrator。Cloudflare 凭据可在**独立的安全终端环境变量**中设置后仅运行一次只读命令，不进入代码仓库和聊天记录。

**当前没有可操作的 Cloudflare 账号连接或只读 Token。真实远端 API 调用数：0。** 不得编造目标 Worker 不存在、Pages 全部盘点完成、真实路由为空等结论。

## 3. 当前连接工具门禁阻断（需要明确交接）

本批尝试将 G2-H.7I 新测试和独立静态审计注册到 `.github/workflows/cms-bff-isolated.yml`。**GitHub 连接工具的安全检查连续两次阻止工作流修改**，旧 CI 仍未包含本批 G2-H.7I 测试，不能用旧 CI PASS 证明当前新代码通过审计，也不能直接合并该 PR。未绕过安全检查，不声称 G2-H.7I 通过 GitHub CI。

因此本批工作交付必须保持 **Draft / NOT_MERGED**，后续需要经允许的代码审查与工作流变更路径，把两个命令纳入隔离 CI 后再运行审计、PR CI、合并与 main 回归：

```sh
node --test tests/g2h7i_cloudflare_readonly.test.mjs
node scripts/security/g2h7i_cloudflare_readonly_audit.mjs
```

第二条静态门禁会在没有 CI 注册时 **预期失败**，这是安全要求，并非可以跳过的故障。将上述测试接入现有 BFF 工作流时需同时添加相应 PR/push 的路径触发，绝不在工作流里加 `--remote-read-only`、Token 或 Account ID。

## 4. 严格安全冻结

- 现有 `ops/cms-preview/cloudflare/deploy-admission.json` 的 12 项准入条件保持全 false；Wrangler `workers_dev=false,preview_urls=false,routes=[]`；真正远端 Worker **NOT_DEPLOYED**。
- Staging `account_auth,cms_editor,v2_matchmaking=false`；Production `account_auth=false`、无 `jianshi_cms` schema；生产零写入，无云端任何变更。
- 现有静态 Pages `jianshi-bua.pages.dev` 发布系统不加入 CMS/Worker 路由，P4.41 四个 UTC 时槽 `55 0` 与 `55 6,12,18`、每日唯一 Claim、HN≤7/RSS≤1/GitHub REST≤2 均保持不变，push 私有采集保持 SKIPPED。
- PR #133 不动。全部验收均由作者自审，非第三方独立安全审计。

## 5. 下一步实际验收标准

1. 在获准更新 GitHub Actions 安全工作流后，新测试和独立审计真实 PASS；在此之前 **PR 只保留 Draft**。
2. Cloudflare 只读权限由用户在受控环境配置后，可使用 CLI 真实枚举指定账户与 Zone 的 Worker、Pages 和路由。它只用于形成待审查证据，不会更改任何资源。
3. 即使真实只读盘点通过，独立 Cloudflare Preview 部署仍需再次授权、独立身份与实际 mTLS/GoTrue 安全审查；正式登录保持关闭。
