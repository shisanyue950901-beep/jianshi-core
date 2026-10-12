# 见势 F2.1 G2-H.7D｜Cloudflare Pages 预览路由适配与二重安全审计

阶段基线：`main=06ab1b3e0c6132782881303f73d5147d22ff3ba3`。日期：2026-10-13。

## 0. 对“每一步是否都由 ChatGPT 审计”的真实回答

G2-H.6–7C 已执行 CI 安全回归、PR/main 双次运行核查、Supabase Staging/Production 只读、权限/原子事务及冻结规则核对；这些是**持续自动验收和自我核对**。但不应把它写成全面独立代码审计，更未获得外部安全团队、实际登录渗透测试和公网 Cloudflare WAF/日志验收。此次增加两套互相分离的审计工件：
- 功能行为：`tests/g2h7d_pages_preview_contract.test.mjs` 模拟 Pages `onRequest({request,env})`，真实 Web Request/Response 语义，验证 GET/POST、Host、CSRF、Cookie、不泄漏与失败关闭。
- 静态交付边界：`scripts/security/g2h7d_preview_deployment_guard.mjs` 独立于路由代码检查 root `functions/`、`_worker.js`、`_routes.json` 和公共发布脚本、四个冻结 cron、`JIANSHI_AUTH_ENABLED: "0"`；任何不合规便使 CI 红灯。

这是**同一 AI 编写的双层自动化复核，不是独立人审或第三方审计**。审计仍可能遗漏逻辑缺陷。

## 1. 官方依据与落地限制

Cloudflare 官方文档：
- Pages Functions 的 `functions/` 根目录能够自动部署；默认路由可能覆盖静态请求；如确需功能路由，应使用部署产物的 `_routes.json` 显式划分：https://developers.cloudflare.com/pages/functions/routing/
- `onRequest(context)` 使用标准 Web Request/Response 和 `context.env`：https://developers.cloudflare.com/pages/functions/api-reference/
- 生产/预览 Wrangler 配置影响相应环境，**不能假定任意分支都有完全独立的配置**：https://developers.cloudflare.com/pages/functions/wrangler-configuration/
- `CF_PAGES_BRANCH` 是构建注入变量；尚不能仅凭它证明运行时安全边界：https://developers.cloudflare.com/pages/configuration/build-configuration/
- 预览分支是否自动发布由项目 Builds/Deployments 控制，默认可能发布全部非 Production 分支：https://developers.cloudflare.com/pages/configuration/branch-build-controls/

**部署决策：本批没有创立真实 Cloudflare 项目或开启任何 Pages Functions 路由。** 候选代码仅放 `ops/cms-preview/functions/auth/confirm.js`，既非现有仓库 `functions/` 目录，亦非 `web/dist` 发布物。

## 2. 功能实现（必须如实界定）

本批只提供 **Web API 兼容的边缘路由适配壳**，没有实际 Cloudflare runtime 部署，也不能接真实 GoTrue、JWT、数据库或者用户验证。代码只在 **虚构不可公开解析的 RFC 2606 域名** `https://h7d-preview.example.invalid` 和 `JIANSHI_H7D_PROFILE=SYNTHETIC_CONTRACT_ONLY` + `JIANSHI_H7D_CONTRACT_GATE=1` + 被注入的 `synthetic:true` 测试 Controller 三门禁同时成立时工作。

因此，即便误复制到现有 `jianshi-bua.pages.dev`，其真实 URL 必定失败关闭 `404`。在未来真正 Preivew 业务上线前必须**新架构审查**：放开域名开关是高风险安全行为，不能单独修改或默许其他人员绕过。目标是避免误上线，而非声称这套代码现已提供真实 CMS 服务。

Web API 请求安全：
- GET 邮件链接仅调用显式合成 `receiveLink`，要求 303 去查询参数，仅加设 Secure/HttpOnly Cookie；GET 不调用测试 `confirm`。
- 无查询参数 GET 只返回中文、无脚本的显式手动 POST 表单，带 CSP `form-action 'self'`、NoStore、NoReferrer、NoIndex。
- POST 必须同源 Origin、`Sec-Fetch-Site=same-origin`、空表单、正确 Content-Type；Content-Length 非零立即拒绝，流式读取避免任意体积缓存。只接收状态适配器返回的相对 `/cms/` 跳转与安全 Cookie；禁止上游自由控制重定向。
- 未通过运行时门禁、域名、Host、Forwarded、路径的请求直接 404 或 403。控制器所有异常统一脱敏，无响应内 JWT/TokenHash/上游错误。
- `/cms/` **404**，未发布任何登录入口/会话后台，不可给真实用户访问。

**注意：** 合成 Controller 由单测注入；Cloudflare runtime 无这个函数型 binding。它不是 Cloudflare 生产密钥配置，代码在真实 Pages 环境即使强行开启两标志依然因无可信 Adapter 而 404。不能把测试 Mock 冒充 Worker 可部署的业务适配器；H7B Node Crypto 与 Worker WebCrypto/HTTP 的实际接线 **NOT_IMPLEMENTED**。

## 3. 二重审计矩阵（在 PR/合并后按 CI 更新结论）

| 级别 | 风险 | 验证方法 | 放行标准 |
|---|---|---|---|
| BLOCKER | 把认证 Functions 发布到生产主站 | 独立静态脚本扫描根目录、web/dist、publish-static、release | 所有路径不存在，发布流程无引用 |
| BLOCKER | 实际 Pages host 意外可用 | Web Request 测试真实 `jianshi-bua.pages.dev` + 预览 Pages 域 | 仅 404，合成 Controller 调用计数 0 |
| HIGH | 页面响应中泄漏 token_hash/JWT | GET/POST/异常的 body/headers 检查 | 响应中无值，无原始查询参数重定向 |
| HIGH | 跨站发起 POST | Origin+Sec-Fetch-Site+空请求体+Content-Type 负向测试 | 消费调用 0 |
| HIGH | 开放重定向/恶意 Set-Cookie | 注入恶意测试 Controller 响应 | 403 拒绝 |
| HIGH | P4.41 配额被修改 | 比对原定四槽，主分支 static push 研究步 | 未修改、push 下均 SKIPPED |
| HIGH | Staging Auth CMS flags 或真实数据被污染 | Supabase 只读聚合 | 三开关 false，CMS/session/challenge 0 |
| BLOCKER | Production 账号/Schema 被更改 | Production 只读 | account_auth=false、无 CMS schema |
| NOT_TESTED | 真正 CF edge 和持久状态/真实 GoTrue/真实 A/B IDOR | 尚未部署，不存在可验链路 | 严禁宣称已经上线 |

## 4. 必须记录、尚无法消除的安全风险

1. `token_hash` 链接如果经过 CDN/Cloudflare ingress，**边缘入口此前的完整 URL 请求可能已经被记录**；后续 303 不能擦除上游日志。部署前必须独立域、代理日志脱敏与审计，禁止将其暴露给公共采集/分析系统。
2. 邮箱链接预取场景：GET 不兑换令牌可减轻普通扫描器误触，但能够持有用户 Cookie 或具备交互能力的高级扫描器另需威胁建模。
3. Cloudflare preview 和 production 环境不能只靠共享分支标识隔离；须专属预览 Pages 项目、独立可撤销密钥和极窄 `_routes.json`，且需要明确批准后才能部署。
4. H7C 隔离证书为临时自签名，并在 Node 测试里关闭 TLS 证书链校验以测试协议，不是公网可信 HTTPS 的合格证据。
5. 原 H7B Controller 使用 `node:crypto` 与私有 SQL，不能不经移植就部署 Worker；真实 GoTrue token_hash 验证、签名 JWT/sessions/角色及刷新/撤销/A-B IDOR 均 NOT_TESTED。
6. 实际 Staging 邮件模板 `{{ .TokenHash }}` + `{{ .RedirectTo }}` 与邮箱供应商链接改写/重定向尚未在真实服务读取和验证。

## 5. 本批冻结要求

- 不修改 P4.41 schedule / daily claim / HN7 RSS1 GitHub REST2 预算。不得用 push 构建重跑真正采集。
- Staging `account_auth/cms_editor/v2_matchmaking=false`，Production account_auth false 与 CMS schema 缺失继续保留。PR #133 Draft 独立。
- 不落真实 JWT、Email TokenHash、Supabase service-role 或 Cloudflare Secrets 到 GitHub/日志。
- 本批交付可审计的 Web API **预览适配契约**，但状态必须是 `PAGES_PRODUCTION=NOT_DEPLOYED`，`PAGES_PREVIEW=NOT_DEPLOYED`，`REAL_GOTRUE=NOT_TESTED`，`CMS_LOGIN=OFF`。

## 6. 本批审计签字口径

只能依据真实 PR & main GitHub Actions 报 `WEB_EDGE_CONTRACT_PASS` / `STATIC_RELEASE_BOUNDARY_AUDIT_PASS`。这些是 GitHub 流水线自动证据和作者自审，**不是人工第三方独立审计证明**。只要 BLOCKER 未清零或流程失败，PR 不能合并。

下一步 G2-H.7E：专属预览环境权限/Secret 规划、Worker WebCrypto 适配与分布式持久状态集成（仅隔离），云端部署需要单独风险许可；Staging 真实邮件验证和双账号 IDOR 不能提前放开。
