# 见势 F2.1｜G2-H.7C：隔离真实 TLS 邮箱确认预览页与 HTTP 端到端验收

交付日期：2026-10-12。起点 `main=dd77a778db84918b8819d85926228121f2b91312`。

## 本阶段实际目标与严格边界

G2-H.7B 已有单次数据库消费与加密邮件确认状态，却只有控制器测试、没有真实 HTTPS HTTP 网关、HTML 确认页面与响应头证据。本阶段在**本机 GitHub Actions 临时 OpenSSL 证书**上运行 Node 22 HTTPS 浏览器式协议测试，暴露明确用户按钮而不是让 GET 自动兑换 OTP；不部署 Cloudflare Pages Functions，不修改真实 Supabase Auth 邮件模板或任何环境 Secret。

**不是**可信公网 Staging BFF、没有用户浏览器真实点击、没有真实 GoTrue 邮箱/JWT、没有 CMS 正向运营。隔离网关仅监听 `127.0.0.1:0` 临时随机端口，并要求 `JIANSHI_G2H7C_SYNTHETIC_ONLY=1` + H.7B 独立合成门禁。正常执行必须没有 SUPABASE/DATABASE/CLOUDFLARE 敏感凭证环境变量。

## 新增代码

- `scripts/qa/g2h7c_loopback_https_preview.mjs`：TLS listener 仅允许本机回环，严格校验 Host（`localhost:<实际端口>`），拒绝外部 Forwarded Host/Proto、非 TLS、非 `/auth/confirm` 路由；不向日志写原始路径、query、Cookie 或正文。
- HTML：`GET /auth/confirm?state=…&token_hash=…&type=email` 只触发 H.7B `receiveLink`，经 AES-GCM 封装加密 HttpOnly 意图 Cookie 后 `303 Location: /auth/confirm` 清除查询串，**不调用 `verifyOtp`**。
- 无参数 `GET /auth/confirm` 只有同时携带状态 Cookie + 意图 Cookie 才返回纯 HTML **手动 POST 表单**，文案标明合成测试；没有 JavaScript、隐藏 Token、真实邮箱、虚假登录成功信息。
- `POST /auth/confirm` 必须 Content-Type `application/x-www-form-urlencoded`，正文为零长度，真实同源 Origin + `Sec-Fetch-Site=same-origin`；H.7B 状态数据库 CAS（在此为合成内存，单独 PG16 事务已在 H.7B 实证）成功后才进入模拟 GoTrue 和合成持久 Cookie。失败统一不包含上游、验证 Token 或 SQL 错误正文。
- `/cms/` **故意保持 404**；不能通过返回 303 就宣称后台可用。
- 本批把 H.7B 的本机合成 origin 从固定无端口 `https://localhost` 安全扩展为 **严格受限的** `https://localhost:<随机测试端口>`；state、redirectTo、Origin 均绑定完全相同的 scheme/host/port，非 localhost 被拒绝。

## 测试证据要求

- `tests/g2h7c_https_preview.test.mjs`：生成一次性 OpenSSL 证书；真实 Node TLS socket 发起 GET/POST，检查 HTML/CSP/no-store/no-referrer/noindex/HSTS（本机 `max-age=0`）、`Secure/HttpOnly/SameSite` Cookie；GET 之后仍未兑换邮件，手动 POST 才会成功；无凭据邮件安全扫描器 GET 403；伪造 Host、Forwarded、跨站 Origin、Fetch Metadata、非法内容类型或正文均拒绝；八条并行 HTTPS POST 一成功七拒绝；过期、重复 token_hash 参数、未受控内部路由全部拒绝。
- `.github/workflows/cms-bff-isolated.yml`：新增两项源码文件变动的 PR/main 自动运行和失败关闭构建门禁。
- GitHub 主 CI 和 Static Snapshot 依旧回归；push 的四个私有 daily claim/research 步骤必须 SKIPPED。
- H.7B 的 PostgreSQL 16 **真实**六路原子测试已经单独于 PR #148 验收；本阶段只是 **HTTP + 合成内存**的连接层，不得冒称已在同一 E2E 内与真实数据库/GoTrue 集成。

## Cloudflare HTTPS Preview 现状与尚未解决

本次 Node `https.createServer` 需要 OpenSSL 的 `key/cert`；Cloudflare Workers/Pages Functions 不是 Node 持续监听的 TLS Server，**不能将测试代码复制到 `functions/` 作为生产/预览路由**。上线方案仍需服务端 Web Request/Response 实现和独立 Preview Secrets，确保 preview/production binding 不串线。

正式入口之前继续检查：Cloudflare Functions 路由、环境密钥/KMS 与轮换、Ingress/CDN/WAF/代理日志中的 token_hash/state 脱敏及查询串处理、邮件模板 `{{ .TokenHash }}` + `{{ .RedirectTo }}` 兼容性、真实签名 JWT 的 /user + auth.sessions + 实时私有角色检验、A/B 后端资源权限、持久会话和刷新/撤销、严格 HTTP 404 与缓存/回滚、移动设备跨浏览器邮箱链接失配，以及用户主动点击的真机验证。

**严格标记**：`LOCAL_TLS_HTML_PROTOCOL_PASS` 需 CI 实际成功；`CLOUDFLARE_PREVIEW_DEPLOY=NOT_DONE`；`GOTRUE_REAL_EMAIL=NOT_TESTED`；`ACTUAL_BROWSER_CLICK=NOT_TESTED`；`PRODUCTION_ACCOUNT=DISABLED`。

## P4.41 / Staging / Production 冻结

- `event=schedule` UTC 00:55、06:55、12:55、18:55；每天最多一次 claim；HN ≤ 7、RSS ≤ 1、GitHub REST ≤ 2；不手动 collect、push 不计真实研究采集。
- Staging `account_auth=false`、`cms_editor=false`、`v2_matchmaking=false`。新邮件状态/PKCE/CMS 数据继续为零，旧 PR #133 Draft 不合并。
- Production `account_auth=false`、`jianshi_cms` 不存在；禁止一切 Production 写操作和业务上线。
