# 见势 F2.1｜G2-H.7：真实 GoTrue 邮件合同核验与 HTTPS 同源入口决策

日期：2026-10-12。**本批仅交付官方合同审查 + 注入式合成 HTTP 线协议测试，不是已完成真实邮件登录/上线。**

## 一、核验基线与冻结

- 本批起点 `main=780cf0f56786197b3646613633d71fea42ac4956`；原 H.6 仍只允许 localhost/127.0.0.1 + `JIANSHI_G2H6_SYNTHETIC_ONLY=1`，不可作真实 GoTrue 验收。
- PR #133 是单独 Cloudflare Pages Staging Preview，仍保留 Draft/OPEN；与新 BFF 授权码方案分开，绝不直接 merge。
- 生产不写；Staging 不开 `account_auth` / `cms_editor` / `v2_matchmaking`，不发真实邮件、不迁移、不读取 JWT/刷新令牌。
- P4.41 UTC 四槽 `00:55,06:55,12:55,18:55`、daily claim、HN≤7/RSS≤1/GitHub REST≤2 完全冻结。push 静态构建不得冒充 schedule 研究采集。

## 二、H.6 设计合同 vs GoTrue 官方实际协议

| 项目 | H.6 合成接口 | 官方服务端实际合同 | 结论 |
|---|---|---|---|
| 发信 | `sendMagicLink({email,redirectTo,codeChallenge})` | `signInWithOtp({email, options:{shouldCreateUser:false,emailRedirectTo}})`；底层 GoTrue `POST /auth/v1/otp?redirect_to=...` body `email/create_user`，PKCE 可使用 `code_challenge/code_challenge_method` | **接口名称与字段需适配** |
| 默认邮件 | 模拟提供 `code` | 默认 ConfirmationURL 邮件链路可返回 fragment；浏览器端可能直接拿 session | **不能视为服务端已拿到 code** |
| 服务端邮件 | 期待 `/auth/callback?code=...&state=...` | 官方邮件模板可使用 `{{ .TokenHash }}` 构造链接至 BFF，BFF `verifyOtp({token_hash,type:'email'})`，REST `POST /auth/v1/verify` 返回 session | **需新分支协议；不与 code 互换** |
| 真正授权码 PKCE | `exchangeCodeForSession({code,verifier})` 注入接口 | `exchangeCodeForSession(code)` 或 `POST /auth/v1/token?grant_type=pkce`（body `auth_code,code_verifier`），仅在真实 GoTrue 发回一次性授权码的链路有效 | **保留 H.6，但不能在 token_hash 上调用** |
| verifier 绑定 | BFF AES-GCM 保存 verifier | SDK 通常在开始登录的一端保存 verifier；授权码兑换需要相同验证器。服务器代发 PKCE 必须证明 `code_challenge` 已按上游接受，不能靠假邮件参数推定 | **真实兼容未验** |
| 会话身份 | H.6 模拟 JWT 和角色 | 真实 GoTrue JWT `/auth/v1/user` + `auth.sessions` + 实时 `editor_grants` 与发布门禁都必须服务端重验 | **不可仅凭 tokenHash 认证 CMS** |
| 回调保密 | state/cookie、URL 不入日志 | 邮件 URL 的 `token_hash`、state 都需 ingress、代理、CDN、APM 等层脱敏；收到后立即无参数 303、Referrer-Policy no-referrer、Cache-Control no-store | **尚需公网链路验证** |

官方一手文档：
- https://supabase.com/docs/guides/auth/auth-email-passwordless
- https://supabase.com/docs/guides/auth/auth-email-templates
- https://supabase.com/docs/guides/auth/sessions/pkce-flow
- https://supabase.com/docs/guides/auth/server-side/advanced-guide
- https://github.com/supabase/auth/blob/master/openapi.yaml

**重要：** 邮件 `token_hash + verifyOtp` 是服务端邮箱验证分支，不能仅因为原 `/otp` 请求能携带 PKCE challenge 就宣称 `/verify` 返回的 session 已完成同一 PKCE verifier 校验。G2-H.7 明确分离该风险，后续实测决定能否构建等效强度的服务端会话。

## 三、本批代码与已建立的安全线协议

- `scripts/qa/g2h7_gotrue_tokenhash_wire.mjs`：固定 Staging GoTrue origin、显式 `POST /otp` 与 `POST /verify` 线协议；`create_user=false`、`type=email`、`redirect_to` 仅接受合成 localhost 同源 state；严禁真实 publishable/service key，强制注入 mock fetch，不读外部真实账号。
- `tests/g2h7_gotrue_tokenhash_wire.test.mjs`：运行闸门、白名单 origin、HTTP 方法/JSON 形状、禁止用户自动注册、错误 URL/邮箱、非法 token_hash、429、上游异常、HTML 响应、缺少 token 等失败关闭。mock 收到 HTTP 200 时只报告请求被接受，`deliveryVerified=false`。
- `.github/workflows/cms-bff-isolated.yml`：加入独立 Node 22 测试步骤，并在 PR/main 代码改动时触发。
- 本批**没有**把 token_hash 接进现有 H.6 `pendingStore`/BFF/Cloudflare，不修改 H.6 已冻结的一次性状态语义。任何真实邮件/邮箱模板更新均需要独立 Staging 人工测试和审批。

## 四、HTTPS 同源接入决策（暂定，尚未部署）

**首选待验证方案**：现有 Cloudflare Pages 的独立 Staging Preview + Pages Functions 提供 `https://<preview>/auth/*` 及未来 `/cms/api/*`，同一 host 使用 `__Host-` Secure/HttpOnly Cookie 和同源 Origin/CSRF；Functions 通过最小权限后端 HTTPS 连接固定 Staging Supabase，服务端只保留加密数据、密钥保存在 Preview-only Secrets 环境绑定。

选择理由：免自行维护 TLS 证书/单独服务器；Pages Functions 已支持路由、Secrets 和 preview/production 区分，且可复用现有 Pages preview。**但不能直接部署 Node `https.createServer` 的 G2-H.3/H.5 Harness 到 Workers 运行时**；必须重新实现 Web Crypto、Cookie/CSRF、服务端 token/session 轮换、超时与事务适配。

接入前置阻塞：是否能以现有 Pages 项目安全预览隔离 Functions；Cloudflare 计费/限额、环境变量权限；密钥轮换/KMS/备份；到 Supabase `service_role` 数据 RPC 的网络接入与最小权限、日志全链路脱敏；GoTrue Auth 模板和 Redirect Allow List 能否满足服务器 state 绑定；浏览器跨设备/跨标签邮件点击与链接预取/安全扫描；持久会话不可保存明文 refresh token；缓存/回退和软 404 必须隔离验证。未获许可不得开收费资源或生产路由。

备选：独立受控 Node HTTPS BFF。现有测试 Harness 接近 Node 环境，但需要额外可信主机、域名、持续 TLS、密钥托管、监控和成本，当前不推荐直接选用。

Cloudflare 官方资料：
- https://developers.cloudflare.com/pages/functions/
- https://developers.cloudflare.com/pages/functions/bindings/

## 五、下一验收门槛（不可用模拟结果替代）

1. 本 PR Node 合同测试和既有 CI success；确保 `event=push` 时 P4.41 私有研究步骤 SKIPPED。
2. Staging Auth 邮件模板必须经只读/审查确定实际 `token_hash`/redirect 行为；不得直接替换旧 preview 回调。
3. 将 state Cookie + H.6 一次性 DB 原子消费纳入新服务端 `token_hash` callback，并验证跨实例并发和错误 Cookie 不消费；**此批尚未完成**。
4. 真实 Staging 单账号 GoTrue URL → 可信同源 BFF → /user + auth.sessions + 实时角色 → 持久 Cookie 端到端证据，随后 A/B IDOR、吊销、登出后重放均拒绝；三项 Staging 业务标志继续关闭，除非单独正式审批授权受控正向测试。
5. 完整验证 Cloudflare Functions 预览路由、严格 404、响应安全头、脱敏日志和回退，Production 单独决策。

## 六、验收标记

- **PASS 范围**：官方 API 文档差异已审查、隔离的 GoTrue HTTP 线协议与负向安全合同（以 CI SUCCESS 为准）。
- **NOT_TESTED**：真实 GoTrue 邮箱模板、真正 PKCE code/token 交换、真实 token_hash 消费、真实 Server BFF 会话、Cloudflare Functions 预览部署、运营级双账号正向 E2E。
- **PRODUCTION_CHANGE=FALSE**；**STAGING_FEATURES_ENABLED=FALSE**；**P441_COLLECTION_CHANGE=FALSE**。
