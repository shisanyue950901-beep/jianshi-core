# 见势 F2.1｜G2-H.7 第二批：邮箱 token_hash 二阶段确认与数据库原子状态（隔离验收）

日期：2026-10-12；基线 `main=ffe64b27331cb74953a332a6e039978ec30cb027`。
**安全边界：本批为 Node 合成 GoTrue + 一次性 PostgreSQL 真实事务，而非真正 Supabase 发信、已部署 Staging 登录或真实用户正向 CMS E2E。**

## 核心设计和威胁模型

官方 Supabase 邮件模板支持 `{{ .TokenHash }}` 和 `{{ .RedirectTo }}`。已有 `signInWithOtp` 的 `emailRedirectTo` 持有状态，例如 `https://localhost/auth/confirm?state=<随机状态>`。未来审核后的 Staging 邮件模板可构成 `{{ .RedirectTo }}&token_hash={{ .TokenHash }}&type=email`，但是 **模板尚未读取/部署/实测，真实邮件链接行为 NOT_TESTED**。

本批刻意不沿用 H.6 的 `encrypted_verifier` 字段，因为服务端 `token_hash/verifyOtp` 不等于 `code+code_verifier/exchangeCodeForSession`。专门新建 `0062_jianshi_cms_email_tokenhash_state.sql`：
- 私有 `jianshi_cms.bff_email_challenges` 只存 HMAC 状态/浏览器 Cookie 摘要、5 分钟过期和原子已消费标记；**不存邮件、token_hash、PKCE verifier、Access/Refresh Token**。
- `bff_issue_email_state_v01`/`bff_consume_email_state_v01` 仅 `service_role`，强制 RLS/FORCE RLS，不开放 `anon/authenticated`；复用 H.6 服务角色 + `account_auth/cms_editor` + 全部 Auth 上线门禁。条件 `UPDATE ... consumed_at IS NULL ... RETURNING` 保证跨数据库连接单赢家；错误 Cookie、过期、重放失败。
- 新加法 SQL **只先进入 GitHub**；Staging 仅在 CI/审计通过之后再考虑应用。Production 永不自动迁移。

隔离 Node 控制器 `scripts/qa/g2h7b_tokenhash_confirmation.mjs`：
1. **start**：生成 256-bit 状态及独立 Cookie；SQL challenge 发放；要求原有 G2-H.7 synthetic mock-only 发信适配；`__Host-jianshi_mail_state` 为 Secure/HttpOnly/SameSite=Lax，TTL 300 秒。
2. **receiveLink（只读 GET）**：严格要求 `state/token_hash/type=email` 三参数及原浏览器状态 Cookie；**不交换 token、不消费 SQL**；使用 AES-256-GCM（AAD 绑定 HMAC Cookie）将 token_hash 与 state 装入 5 分钟 `__Host-jianshi_mail_intent` Secure/HttpOnly/SameSite=Strict 临时 Cookie，303 跳无查询参数的 `/auth/confirm`。防止邮件安全扫描器单纯 GET 立即消耗真实链接。恶意扫描器持有原 Cookie/可 POST 等高级情形依旧要专门审查，不能宣称解决所有邮件预取问题。
3. **confirm（明确用户 POST）**：必须同源 Origin + `Sec-Fetch-Site: same-origin` + 正确方法/路径及双 Cookie；鉴别解密意图，数据库 **先原子消费状态**，再通过 GoTrue 的 `verifyTokenHash`（合成）换回令牌，然后独立验证 `/user`、`auth.sessions`、CMS 角色（真实桥接未实现），合成颁发 15 分钟服务端 Cookie。上游交换失败也不允许重放同一状态。
4. HTTPS Host、代理日志脱敏、UI 人工确认页、真实 Secrets、会话持久化、Refresh Token 轮换、Cloudflare Pages Functions 入口均 **NOT_IMPLEMENTED**；当前 Node 模块 **不能**接公网。
5. 本协议同浏览器 Cookie 绑定：跨设备、不同浏览器或无共享 Cookie 的邮箱点击失败关闭；手机邮件打开桌面发信需要单独设计受控 OTP 或迁移策略，不得降级成无 state 的服务端直接确认。

## 自动验收范围

- Node 22 `tests/g2h7b_tokenhash_confirmation.test.mjs`：测试 GET 不兑 token、显式 POST 同源确认、加密密文无令牌回显、仿冒/重复 Cookie、额外参数、CSRF/跨站、过期、错浏览器、上游失败烧掉挑战、两个控制器八并发争抢一赢家。
- PostgreSQL 16 原生隔离容器：加载原 `0037,0054–0062` 共十份迁移；同时经不同连接六次消费：1 true / 5 false；检查强制 RLS、匿名无权限、重复发放、错误 Cookie 未燃烧、过期和功能开关关闭下拒绝。
- `cms-bff-isolated.yml`、`cms-postgres-isolated.yml` 注册上述测试，不能执行真实 source collect 或携带远端 Supabase 凭证。

## 保持冻结的最高约束

- P4.41 `event=schedule` UTC `00:55/06:55/12:55/18:55`、每天一次 daily claim 和 HN≤7/RSS≤1/GitHub REST≤2 不改动；`event=push` 仅静态构建，采集步骤应为 SKIPPED。
- Staging `account_auth=false`、`cms_editor=false`、`v2_matchmaking=false`；既有 CMS/持久会话不能为方便测试被开启或写入合成数据。
- Production `account_auth=false`，无 `jianshi_cms` schema；生产零写入。
- PR #133 为现行独立 Auth 回调 Preview，不随此 PR 合并。
- 禁止读写或输出真实邮件链接、验证 token_hash、JWT、Service Role Key、原始私人研究 Artifact。

## 严格验收判定

**代码及 CI 通过时仅可写：** `G2H7B_SYNTHETIC_TOKEN_HASH_CONFIRM_PASS` 和 `G2H7B_REAL_DISPOSABLE_PG_ATOMIC_PASS`；真实 Staging/Production GoTrue 登录、双账号越权、浏览器交互、HTTPS Server BFF、业务运营 **全部 NOT_TESTED**。

下一批：① Staging 邮件模板 **只读** 查明真实形态；② 合法隔离 HTTPS/Cloudflare Preview 中设计并实现无密钥两步交互；③ 依审批用真实 Staging 密钥受控集成，不默认开业务开关；④ A/B 角色与后端撤销/IDOR E2E；⑤ 完整密钥/日志/缓存/软 404 审核后再考虑 G2-H.8。 
