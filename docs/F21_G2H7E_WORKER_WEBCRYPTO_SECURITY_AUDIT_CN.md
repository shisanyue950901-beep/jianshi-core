# 见势 F2.1｜G2-H.7E：Worker 原生 WebCrypto、跨实例状态合同与双层安全审计

日期：2026-10-13；起点 `main=ba98a694e0208b44ce56f9047d306522eca8a60f`。

## 1. 本次完成的实际范围

### Worker 原生密码学

新增 `ops/cms-preview/worker-email-crypto.mjs`。它完全使用标准 Web Crypto（`crypto.getRandomValues`、`crypto.subtle.importKey`、`crypto.subtle.sign`、`crypto.subtle.deriveKey`、`crypto.subtle.encrypt/decrypt`）和 `Uint8Array`，**不依赖 Node node:crypto/Buffer/process 或联网能力**。支持：
- 256-bit 随机 `state` 与独立浏览器 Cookie；HMAC-SHA256 不同域标签 `state\0`、`cookie\0`，发给私有待消费状态适配器的仅为十六进制摘要。
- HKDF-SHA256 从 32 字节注入的合成密钥导出 AES-256-GCM 密钥，沿用 H.7B 的标签 `JIANSHI_G2H7B_EMAIL_INTENT_V1`；12 字节随机 IV，128-bit GCM tag，AAD 绑定原浏览器 Cookie 的 HMAC 十六进制摘要。
- `token_hash` 不写数据库、浏览器可见 HTML 或明文 Cookie；邮件 GET **只**封装加密意图并 303 去查询参数，用户 POST **先单次消费**状态，再模拟 GoTrue 兑换和角色/会话验证。
- 五分钟有效期、输入白名单、严格重复参数/重复 Cookie 检查、CSRF/Origin/Sec-Fetch-Site、会话 Cookie 仅 HttpOnly/Secure/SameSite。普通邮件扫描器拿不到原浏览器 Cookie 时不会消耗状态。
- 不可公开解析的 `https://h7d-preview.example.invalid` 固定 origin、`SYNTHETIC_H7E_ONLY` 固定 profile，状态仓库/GoTrue/验证身份/会话颁发四个依赖全部要求 `synthetic:true`。**没有任何真实 Staging/Production 登录凭据。**

### 新增测试

`tests/g2h7e_worker_webcrypto.test.mjs`：
1. 真实 Pages 域名、非合成身份/密钥/数据源一律 fail-closed。
2. 真实 Web Request/Response 上下文调用 H.7D `onRequest`，测试加密意图 Cookie→中文 GET 表单→手动 POST→一次性合成 Session，页面/响应不回显 OTP/JWT/邮件。
3. 使用独立 Node `createHmac`、`hkdfSync`、`createDecipheriv` 解密 **Worker 生成的 AES-GCM Envelope**，逐字节校验 H.7B 密钥派生、AAD、state/token_hash 和到期时钟；这是真实密码学跨实现验证，而不是简单 mock。
4. 错误浏览器 Cookie、篡改 GCM tag、重复 Cookie、错误链接参数、无 Cookie 扫描器、过期。
5. 两个不同的模拟 Worker 控制器共享一个合成原子适配器，16 个同时 POST 预期恰好 1 次成功，15 次重放拒绝；没有模拟成功值冒充真实 PG。
6. Role/Session/GoTrue 上游错误 fail-closed，状态已消费不可恢复重放。

另新增 `scripts/security/g2h7e_worker_webcrypto_audit.mjs`，**与功能测试独立的静态代码审计门禁**，禁止 Node Crypto、直接 fetch、进程环境、非密码学随机数、公开主站/Production Supabase origin、实时日志和危险动态代码；同步复核正式 Pages 发布边界、P4.41 cron、公开 Auth=0，且仍运行上一轮 H.7D 发布路径审计。

## 2. 外部文档核对

- Cloudflare Workers Web Crypto API（支持 HMAC、HKDF、AES-GCM）：https://developers.cloudflare.com/workers/runtime-apis/web-crypto/
- Cloudflare Pages Functions Bindings 与 Production/Preview Secrets： https://developers.cloudflare.com/pages/functions/bindings/
- Cloudflare Pages Functions 的 `functions/` 自动路由机制：https://developers.cloudflare.com/pages/functions/routing/
- Cloudflare Wrangler 环境：Pages 预览配置不是任意分支独立环境，需要专属项目隔离：https://developers.cloudflare.com/pages/functions/wrangler-configuration/

## 3. 安全冻结与残余阻断

**本阶段不创建 Cloudflare 项目、不部署 Worker、不开放任何真实 Pages Functions 路由、不安装真实密钥、不接入真实 GoTrue/邮箱模板、不改 Supabase 生产或 Staging 数据/开关**。路径仍为 `ops/cms-preview`，不能被 `web/dist` 或 Pages 根目录打包。

原 `0062_jianshi_cms_email_tokenhash_state.sql` PostgreSQL 16 已完成真实六数据库连接 1 胜 5 败；本次 Worker `pendingStore` 是注入的合成适配器，虽然测了两个控制器和 16 并发，但**尚未通过 HTTP 与真实 PostgreSQL/Supabase RPC 进行跨机集成**。代码使用 `synthetic:true` 构造门禁，无法将其配置成真实账号认证；真实 JWT 签名校验、auth.sessions/actor_role、会话持久化和回收仍独立待做。

仍存在的阻断：
- 云端 Pages Preview 项目/路由/Secrets、WAF/负载日志中的原始邮件 URL 隐私与 token_hash 脱敏；
- 浏览器对 Email Token Hash 链接可能跨设备，无原浏览器 Cookie fail-closed；
- 确认后真实 GoTrue token_hash POST 与 Trust Adapter、JWT/会话角色交叉校验、真实 A/B IDOR；
- 分布式状态 SQL-RPC 的真实 WebCrypto HTTP 桥接、刷新/撤销及密钥轮换；
- 实际安全人员/独立第三方代码审计，Cloudflare Worker runtime 真实 E2E；
- 还未为用户开启任何登录或后台页面。

冻结：P4.41 `event=schedule` 只有 UTC `00:55/06:55/12:55/18:55`，每日一 claim，HN ≤7、RSS ≤1、GitHub REST ≤2；`event=push` 私有研究步骤 SKIPPED。Staging 三开关继续 false；Production account_auth=false、没有 jianshi_cms schema；PR #133 不动。

## 4. 审计证据签署标准

功能测试、独立 WebCrypto 静态安全审计、旧 H.7D 发布隔离审计、PR 两项 CI，全部 PASS 方可合并。合并后再次核实 main 的 CI、静态构建/private SKIPPED、Staging/Production 只读安全快照，再在 PR 中记录每一项证据、失败修复及残余风险。

**合格表述仅限** `WORKERS_WEBCRYPTO_SYNTHETIC_PASS`、`NODE_CROSS_CRYPTO_VECTOR_PASS`、`WORKER_STATIC_RELEASE_AUDIT_PASS`；`REAL_CLOUDFLARE_PREVIEW=NOT_DEPLOYED`、`REAL_GOTRUE=NOT_TESTED`、`TRUE_DISTRIBUTED_PG_INTEGRATION=NOT_TESTED`。作者自审与 CI 自动门禁**不是**第三方独立审计。
