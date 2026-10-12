# 见势 F2.1｜G2-H.7F：Worker→真实 PostgreSQL16 的隔离 HTTP 链路与独立安全审计

实施日期：2026-10-13。基线 `main=1e1f36643003dd41e45457b280e6a8df88cb4500`。

## 1. 严格定义交付

本批解决了 H.7E 的重要证据缺口：此前 Worker WebCrypto 只能连接**合成内存状态适配器**，H.7B 的真实 PostgreSQL 行锁并发测试又是**独立执行**，两者没有处于同一请求链路。

本批在一次性 GitHub Actions **PostgreSQL 16 Docker 容器**内，采用以下原生真实路径：

`Worker Web Crypto Controller` → `Web Request/Response 的人工 POST 网关` → `Worker fetch/HTTP 客户端` → `127.0.0.1 Python ThreadingHTTPServer` → `docker exec psql / SET ROLE service_role` → **真实仓库迁移** `jianshi_cms.bff_issue_email_state_v01` / `jianshi_cms.bff_consume_email_state_v01` → PostgreSQL 原子 UPDATE → 合成 GoTrue / 身份 / 会话。

这个路径真正执行 PostgreSQL 16 中的私有 SQL 函数，并在多条实际 HTTP 请求、多条 psql/PostgreSQL 后端连接下检查单赢家。其他依赖仍然模拟，不是真实 Supabase Auth 或业务上线。

## 2. 代码与验收对象

- `ops/cms-preview/worker-pg-disposable-http.mjs`：Worker Web API 兼容 fetch client，只允许 `http://127.0.0.1:<端口>/v1/email-state`，拒绝普通网络域名、跳转、远端 Supabase REST、查询参数、非专用合成 Profile 和任何非固定 `SYNTHETIC_` 假密钥；请求体字段白名单，只发送状态和 Cookie 摘要及过期时钟。拒绝 HTML、非 JSON、额外返回字段、非预期状态码、无效的 `used` 类型；错误结果脱敏。实际生产不可用。
- `scripts/qa/g2h7f_pg_http_runner.py`：须已存在一次性 `postgres:16` 容器与真实 0037/0054–0062 迁移。拒绝任何外部 Database/Supabase/Cloudflare 凭据，确认容器正在运行、固定 `jianshi_g2f` DB 且账号门禁初始关闭，仅在 disposable DB 打开合成 8 项资格门禁及 Auth/CMS 两项开关。HTTP 仅本机监听，固定假 Bearer，接受 JSON 白名单和固定路径，使用数据库自身时钟确定有效期、PostgreSQL 行级原子消费；请求日志禁用、错误不反射；测试完成 `finally` 重新关闭测试 DB 的账号门禁。这里的 `service_role` 只在容器内部执行，不存在远端 Supabase service-role key。
- `tests/g2h7f_worker_pg_http.test.mjs`：Node 22 真正通过多次 HTTP 与容器中私有 PostgreSQL 函数交互；覆盖错误 Cookie 不燃烧、重复发放拒绝、重放、恶意 Header、业务 URL 错误、**两个独立 Worker 实例 + 八个 HTTP POST/psql 连接争抢同一 state，一次成功七次失败**；GET 页面不消费、HTML 隔离。真实 GoTrue/JWT 等只能使用合成字符串。
- `tests/g2h7f_bridge_contract.test.mjs`：不连数据库的单独拒绝测试，覆盖 URL、HTTP response shape、假密钥、缓存跳转、任何额外字段和上游错误，BFF 专项独立跑。
- `scripts/security/g2h7f_http_pg_boundary_audit.mjs`：独立静态审计。检查没有根 Functions 发布、没有修改正式发布管道、固定 UTC P4.41 四槽、账号静态关闭、Node/Worker 各自运行时边界、假的 loopback-only 凭据、不允许生产 Supabase 域名/密钥，所有文件同时纳入 BFF 和 PostgreSQL CI 的变更触发。
- `.github/workflows/cms-postgres-isolated.yml`：在原有 `g2f_postgres_real_e2e.py` 和 G2H5 实际容器 E2E 之后添加 H7F 真 HTTP 服务步骤；**不创建新云端数据库或生产采集源**。
- `.github/workflows/cms-bff-isolated.yml`：先测合成 HTTP 失效关闭再测第二份静态审计。

## 3. 固有安全限制（绝不能冒充公网可信 BFF）

1. 隔离传输是 `127.0.0.1` 的明文 HTTP；由于只在单机 GitHub runner 回环接口测试，不能视为真实跨网公网 mTLS 认证、可信代理、WAF 或密钥托管。
2. 真实 PG 在一次性 Docker 容器中，**不是实际 Staging/Production**；八项 Auth 资格门禁的正向打开只在 disposable DB，不会设置真实环境。
3. PostgreSQL 私有 schema 的 SQL 由测试专属 Python 可信进程用 `SET ROLE service_role` 运行；这并不是可公开访问的 PostgREST RPC，也不应把 SQL/service-role 直接暴露给 Worker/浏览器。
4. Worker Controller 的 HTTP 适配器只认固定 `SYNTHETIC_H7F_DISPOSABLE_PG`，实际域名永远不被允许，合成测试密钥不是安全的生产认证凭据。
5. 没有真实 GoTrue 验证、JWT 公钥核验、auth.sessions/角色授权、存取真实 Refresh Token、持久会话生命周期、双账号 A/B IDOR、真实邮件模板或 Cloudflare Preview 项目。
6. Worker/Cloudflare 与真正可信中间层的生产设计仍需独立 Private Networking/TLS、IP/Origin/WAF、多租户 RBAC、短期可轮换服务身份、审计日志脱敏/拒绝 URL 原始 token_hash 和密钥封装的审批。
7. 用户跨设备打开邮箱无原浏览器 Cookie 时仍严格失败关闭。

## 4. 防护冻结

- P4.41 UTC 只在 00:55、06:55、12:55、18:55 四槽调度；一天一项私有 claim，HN ≤7、RSS ≤1、GitHub REST ≤2；`event=push` 仅静态更新，采集步骤应全部 SKIPPED。
- Staging `account_auth/cms_editor/v2_matchmaking=false`；CMS 内容、邮件状态、PKCE、BFF Session 仅只读确认仍为零，任何变更须另审批。
- Production account_auth=false、无 `jianshi_cms` schema，**Production 零写入**。
- 独立 PR #133 保留 Draft，不并入本批。
- 无真实 JWT、邮件、GoTrue token_hash、Supabase service-role key 进入仓库/日志。

## 5. 审计结论条件

必须以实际 GitHub PR 与 main workflow 通过为准，正式标签只有：
- `G2H7F_REAL_DISPOSABLE_HTTP_PG_PASS`：已确认 Worker→HTTP→真实临时 PG SQL，含跨连接争抢。
- `G2H7F_BOUNDARY_AUDIT_PASS`：独立 static 规则及旧安全回归通过。
- `REAL_STAGING_GOTRUE=NOT_TESTED`；`REAL_CLOUDFLARE=NOT_DEPLOYED`；`PRODUCTION=UNCHANGED`。

由模型开发并运行的二级测试/静态审计**不是**独立人审，必须据实留档；发现故障会保留 CI 失败链接与修复原因。
