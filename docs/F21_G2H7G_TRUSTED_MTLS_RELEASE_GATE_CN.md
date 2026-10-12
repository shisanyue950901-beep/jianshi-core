# 见势 F2.1｜G2-H.7G：TLS 1.3 双向认证、证书轮换与真实 PG 隔离审计

日期：2026-10-13。基线 `main=ed3f6f4d129a567b3dea25186762568654725fda`。用户已批准继续推进**隔离研发及受控 PR 验收**，不等于授权实际打开用户登录、配置真实云端密钥或 Production 写入。

## 1. 外部真实服务限制（Cloudflare 与 Supabase）

本批已查官方资料：
- Cloudflare Workers 通过 `mtls_certificates` 绑定提供 `env.<binding>.fetch()`，证书在传输层呈现，不必把私钥导出到 Worker JavaScript：https://developers.cloudflare.com/workers/runtime-apis/bindings/mtls/
- 官方明确提醒：对 **Cloudflare 代理中的域名**发起 Workers 客户端 mTLS 请求可能返回 520；不能假设任意公网域名和现有 `*.pages.dev` 都能成为可信上游。
- Pages Functions 的资源绑定仅支持其文档列出的子集；**不能默认 Workers mTLS 绑定在当前 Pages 项目直接可用**：https://developers.cloudflare.com/pages/functions/bindings/
- Supabase 于 2026-10-12 发布 TLS 公告，最早 2026-11-10 停用部分旧 TLS 1.2 CBC 密码套件。本批选择 TLS 1.3：https://supabase.com/changelog?types=breaking-change

**部署决策：正式可信身份通道需要独立审查 Workers 专属服务与未通过 Cloudflare 代理的可信后端。现有 Pages 静态网站、Production 和 GoTrue 均不作任何真实修改。**

## 2. 真实验收链路的范围

在已有 G2-H.7F **一次性 PostgreSQL 16 Docker 容器**上新增独立 mTLS 传输试验：

`WebCrypto Worker 合成控制器`
→ `H7D Web Request/Response`
→ `G7G 注入的 synthetic mTLS Fetcher`
→ `Node https.request（TLS1.3、验证服务器 CA 与 localhost SAN、客户端证书）`
→ `127.0.0.1 的 Node HTTPS 双向认证代理`
→ `127.0.0.1 的既有 H7F Python HTTP 可信网关`
→ `Docker 内 service_role`
→ **实际迁移 0062 私有 SQL**，`bff_issue_email_state_v01` / `bff_consume_email_state_v01`。

原有 H7F 的明文 HTTP 仍严格只在同一 GitHub Runner 回环地址上充当内层服务；**不是**已将私有 PostgreSQL 直接暴露公网。外层 mTLS 是实测网络 TLS1.3，但 Worker Fetcher 是 Node 的**合成绑定 shim**，不能说已在真实 Cloudflare Workers runtime 跑通证书绑定。

## 3. 各文件职责

- `ops/cms-preview/worker-mtls-state-contract.mjs`：只接受 `https://h7g-state.example.invalid/v1/email-state` 不可解析固定端点和 `SYNTHETIC_G2H7G_MTLS_ONLY` Profile，**强制注入 synthetic binding**，通过绑定的 `.fetch()` 发送最小 JSON HMAC 摘要和过期时间。拒绝任何真实域名、Bearer 密钥、JWT、Cookie 等字段，错误完全脱敏；没有证书、Node 模块或服务角色的代码/配置。
- `scripts/qa/g2h7g_disposable_mtls_harness.mjs`：仅 Node GitHub 临时进程，使用 OpenSSL **运行时**生成彼此分离的 Server CA、Client CA、Foreign CA，服务端证书含 `DNS:localhost` SAN，签发合法客户端 A/B/C 和外 CA 证书。代理严格 TLS1.3、`requestCert/rejectUnauthorized`，除 CA 验证外额外用**客户端证书 SHA256 指纹允许列表**。即便签发于受信任 CA，未被允许的 C 证书仍拒绝。没有有效 mTLS 身份的请求不调用 PostgreSQL。通过 A/B 灰度与撤销 A 的证书指纹，确认旧身份被拒、新身份继续消费。临时私钥只存在 runner tmpdir，最终由 `close()` 删除。
- `tests/g2h7g_mtls_pg.test.mjs`：真实 HTTPS Client Certificate + 真实 PostgreSQL16 SQL 测试；无证书、外国 CA、客户端错误 Server-CA 信任、同 CA 未授权客户端、伪造 Host/Forwarded/Authorization、意外路由、单次回放及八个 A/B 并发消费。确认身份撤销前后的结果，并且 A 的撤销不损伤 B 的新连接。GoTrue/身份/会话仍为 `SYNTHETIC_`。
- `tests/g2h7g_mtls_contract.test.mjs`：纯 Web API 契约负向回归；无模拟 binding、非合成、真域名、错误 HTTP、HTML、异常回显、无效返回 JSON、客户端多余字段等全部失败关闭。
- `scripts/security/g2h7g_mtls_boundary_audit.mjs`：独立静态审计，检查没有已提交 cert/key/p12、真实身份密钥混入 Worker、没有自动公开 Functions、原有 UTC cron/账号关闭/数据库部署限制未改变；同时强制 BFF/PG 两份工作流包含本批测试。
- `scripts/qa/g2h7f_pg_http_runner.py`：复用同一个一次性 PG 16 容器，在 H7F 成功后额外执行 H7G，使用 finally 重新关闭容器内测试业务门禁。若 H7G 任一失败，整个 PG CI 必须 FAILED。
- `cms-bff-isolated.yml` / `cms-postgres-isolated.yml`：确保 PR/main 修改以上安全代码必定触发审计，无生产部署任务或 Cloudflare 凭据。

## 4. 审计矩阵与严格判定

| 严重性 | 门禁 | 通过条件 |
|---|---|---|
| BLOCKER | 实际账号开关被误开启 | Staging 3 flags=false，Production account_auth=false 且无 CMS schema |
| BLOCKER | 真正网站自动部署认证入口 | 根 `functions/`、`_worker.js`、`_routes.json` 不存在；发布流程无引用 |
| BLOCKER | 真实密钥、证书私钥写入 git | 独立审计排查，全部 cert/key 只在 runner 临时目录 |
| HIGH | 伪造客户端身份 | 没有证书、foreign CA、未授信 C 均拒绝且未触发 SQL |
| HIGH | 伪造服务端身份 | TLS 客户端验证 Server CA+SAN，错误 CA 断链 |
| HIGH | 身份轮换 | A/B 初始可用、A 撤销后不可继续，B 可继续 |
| HIGH | 分布式原子消费 | 两 Worker 身份，八路真正 HTTPS→PG 后端 1 赢家 7 拒绝 |
| HIGH | 明文密钥回显或错域 | HTTP/响应 body 及 metadata 无 JWT/token_hash，非 `.invalid` 生产域不可构造 |
| HIGH | P4.41 源采集边界 | cron 及来源预算不改；event=push 私有 claim/采集步骤应 SKIPPED |
| NOT_TESTED | 真实 Workers mTLS binding、云端路由与终端 DNS | 不能声称部署、公开入口或正式 mTLS 会话 |
| NOT_TESTED | GoTrue、签名 JWT、真实会话、A/B IDOR | 真实用户登录仍处于关闭门禁 |

**注意：** 这一批的证书轮换是隔离网关内的**指纹撤销模拟**，不代表真实 Cloudflare 控制台的证书吊销、CRL/OCSP、私钥失窃响应或零中断全球扩容已完成。单日短期证书测试不能替代长期证书生命周期运营和外部安全渗透测试。

## 5. 安全冻结与后续

- P4.41：`event=schedule` UTC 00:55 / 06:55 / 12:55 / 18:55；每日最多一次 private claim；HN≤7、RSS≤1、GitHub REST≤2。push 只能静态网站构建，不执行真实研究采集。
- Staging `account_auth=false,cms_editor=false,v2_matchmaking=false`；Production account_auth=false，CMS schema 缺失；除一时性 Docker 数据库外不执行真实环境的写操作。
- 不更改 G2-H.6 历史冻结或 PR #133（Draft）。
- 用户不需要交出密码、邮箱验证码、JWT、Service Role、证书私钥或 Cloudflare API Token。
- 合并后继续复验所有 main CI、Staging/Production 只读和静态私有采集 SKIPPED，并在 PR 记录失败修复和残余阻断。

只有 PR / main 实际 CI **SUCCESS** 后才能宣告 `G2H7G_TLS13_MTLS_REAL_DISPOSABLE_PG_PASS`、`G2H7G_CERT_ROTATION_TEST_PASS`、`G2H7G_STATIC_SECURITY_AUDIT_PASS`。真实云端准入和独立人工第三方审计仍为 **NOT_DONE**。
