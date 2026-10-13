# 见势 F2.1｜G2-H.7H：Cloudflare 独立预览环境准入与部署前自动否决

执行日期：2026-10-13。分支起点 `main=b158816059fa43516b0d8173ac1ebb2f82834e7c`（已含 G2-H.7G 合并及当天的静态快照刷新）。

## 0. 本批交付定位

此阶段明确解决「已经做了 TLS1.3 + mTLS + PostgreSQL 隔离测试，但能否直接部署 Cloudflare Preview？」的准入问题。结论是：**不能直接把 G2-H.7D/7E/7G 认证代码发布到公开 Pages**；Cloudflare Workers 的独立项目、mTLS 绑定、可信上游和真实 GoTrue/角色验证仍必须分别取得证据。

本批提供三个可以实际运行的工件：
1. `ops/cms-preview/cloudflare/locked-worker.mjs`：独立 Worker 404 拒绝所有请求的候选入口；无用户身份逻辑、网络、Cookie、绑定、数据库、私钥或访问主站的路由。这不是正式 CMS 认证入口。
2. `ops/cms-preview/cloudflare/wrangler.json`：专属 Worker 名称 `jianshi-cms-auth-admission-locked`；设置 `workers_dev=false`、`preview_urls=false`、`routes=[]`、`mtls_certificates=[]`、账号认证开关 `0`。没有 account ID、密钥、真实 endpoint；文件处于 `ops/` 下，不是自动部署配置。
3. `ops/cms-preview/cloudflare/deploy-admission.json`：十二个硬门禁显式 `false`，包括独立 Worker 权限、证书绑定、非 Cloudflare 代理的可信 mTLS 上游、Secret 托管、真实 Staging 邮件模板、GoTrue 多角色 A/B IDOR、人类安全复核、再次授权和 Production 变更等。文件必须保持 `BLOCKED_BY_DEFAULT`；证据暂为空。

**上述文件未上传至 Cloudflare，更没有实际创建生产或预览 Worker 实例。** Wrangler 的 `workers_dev=false` 并不是所有既有部署 URL 都不可达的证明，必须实际检查 Dashboard 域名和路由；本批只证明 repo 配置候选不会主动开放这些入口。

## 1. 真实技术约束

官方参考（截至 2026-10-13）：
- Cloudflare Wrangler 新项目推荐 `wrangler.jsonc`，支持 `workers_dev`、`preview_urls`、`routes`、环境和 `mtls_certificates` 配置：https://developers.cloudflare.com/workers/wrangler/configuration/
- 对 Workers 侧 mTLS 的真实证书绑定，可使用 `wrangler mtls-certificate upload` 与 `env.<binding>.fetch()`；Cloudflare 代理的上游域名存在 520 限制：https://developers.cloudflare.com/workers/runtime-apis/bindings/mtls/
- Cloudflare Workers 环境会创建名字独立的 Worker；不等于完全独立账号与权限：https://developers.cloudflare.com/workers/wrangler/environments/
- Pages Functions 支持的绑定是子集，不能默认为已有 `jianshi-bua.pages.dev` 站点直接支持 Workers mTLS：https://developers.cloudflare.com/pages/functions/bindings/

**架构原则：** 未来实际认证与 mTLS 不应在公开静态 Pages 根目录下部署，而应在单独 Worker、独立权限及限流策略下以受控 Staging 为联调目标；数据库角色权限继续归可信后端管理。Worker 不持有 Supabase `service_role`，不直接接公网私有 SQL。

## 2. CI 安全门禁是可执行的

- `scripts/security/g2h7h_preview_admission.mjs`（与 Worker 实现独立）严格比对 Wrangler 配置字段、关闭的域名与 preview URLs、无路由/mtls binding、不含 Cloudflare/Supabase 账号密钥、不生成任何登录成功响应，以及十二项审批条件全部为 `false`。检查主站发布流程没有 `ops/cms-preview` 引用，P4.41 四个 cron 不变、`JIANSHI_AUTH_ENABLED: "0"` 不变，独立 CI 步骤存在。
- `tests/g2h7h_preview_admission.test.mjs`：真正使用 Node Web Request/Response 调用 deny-only Worker，测试所有方法、主站/预览域名、带 TokenHash/Cookie/Bearer 的请求仍全部 404、无敏感回显；自动恶意更改配置，验证打开路由、启用 Preview URL、添加证书、开启身份、伪造已授权、插入新成功响应或破坏旧 cron 都必须使审计 FAIL。
- `.github/workflows/cms-bff-isolated.yml`：对 PR 和 main 都执行独立行为测试与静态部署否决审计，不包含 `wrangler deploy`、Cloudflare Token、外部密钥/证书上传步骤。
- **审计的 PASS 标记是 `G2H7H_CLOUDFLARE_PREVIEW_BLOCKED_SAFE_PASS`，意为「拒绝未授权上线成功」；绝不是 `CLOUDFLARE_AUTH_LIVE_PASS`。**

## 3. 操作准入次序（后续批次逐门实现）

| 阶段 | 合格证据 | 目前结论 |
|---|---|---|
| 独立 Worker 配置 | 项目与现有 Pages 隔离、路由和权限逐项审阅 | 候选文件已建，真实项目未创建 |
| 安全的开发/部署授权 | 最小权限账号、不可跨 Production 的权限边界；凭据不进仓库/聊天 | NOT_DONE |
| mTLS 可信上游 | 独立非 Cloudflare 代理 Origin + 实际 CA/客户端身份与轮换 | GitHub Runner 测试完成；云端 NOT_TESTED |
| 真实 Staging GoTrue | 官方模板与跳转目标、安全日志脱敏、双用户不同角色 A/B IDOR | NOT_TESTED |
| 用户确认上线预览 | 所有上面条件真实通过 + 人工安全复核 + 再次明确批准 | BLOCKED |
| Production 登录开放 | 独立生产变更申请、真实回滚演练与审计 | FROZEN |

用户当前已允许**本地/PR 开发和隔离验收**，不等于批准公网部署、付费开通、使用真实身份凭据或生产写入。在没有 Cloudflare 可操作账号连接及再次云端授权的情况下，本批不以模拟结果冒充远端部署成功。

## 4. 既有冻结与自审说明

Staging `account_auth/cms_editor/v2_matchmaking=false`，邮件 challenge、PKCE、BFF session、CMS 内容应继续为零；Production `account_auth=false` 且不存在 `jianshi_cms`。只能只读复核。

P4.41 按 UTC `00:55,06:55,12:55,18:55` 四时槽，单日不超过一个真正的私有 claim，HN ≤7、RSS ≤1、GitHub REST ≤2；静态 `event=push` 私有研究步骤始终 SKIPPED。PR #133 保留 Draft。

审计是 AI 作者自审与独立自动测试的双层证据，**不是外部第三方独立安全审计**。每次必须 PR CI 先绿、Squash Merge，然后主分支 CI 与 Supabase 只读状态再次验收；失败和纠正过程写入 PR，不允许抹掉初次失败记录。

## 5. 下一批 G2-H.7I 的前提

本批保持 `real_cloudflare_deployment=false`。若未来正式连接 Cloudflare，必须先确定一个**完全独立、无公网路由的测试 Worker**，通过官方的最小权限方式授权，仅做只读配置核验/deny-only 身份探测；独立的公网部署必须再次被用户明确授权。现实测试 Secret、客户端证书、服务端证书和 Service Role 均不得以聊天文本方式传送。
