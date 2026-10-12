# 见势 F2.1｜G2-H.5 真实 HTTPS—加密持久会话—CMS 数据库集成验收

日期：2026-10-12。定位：**GitHub Actions 一次性 PostgreSQL + 自签 TLS 的真实跨组件集成测试**，不是真实 Supabase 用户登录，不是可直接上线的 BFF。

## 本轮工程突破

- 前 G2-H.3 的 HTTPS Cookie、G2-H.2 的 GoTrue 身份适配、G2-H.4 的 HMAC/AES-GCM 会话封装和 PostgreSQL `bff_sessions` 存储各自通过测试，但原来没有同一真实请求链。G2-H.5 将这些连接成可重复执行的完整请求。
- 新 `scripts/qa/g2h5_durable_https_bff.mjs`：Node 原生 TLS 请求先校验 Host/Origin/Fetch-Site、Cookie/CSRF 格式，随后 HMAC 摘要进入持久存储 `bff_consume_session`，校验 GoTrue 会话与 CMS 角色，解密 AES-GCM JWT 并再次核验 token+用户+会话绑定；仅通过后调用 CMS dispatcher。
- 新 `tests/g2h5_durable_https_pg.test.mjs`：真实 TLS 请求、两个独立 HTTPS 服务器实例、**同一一次性 PostgreSQL 私有会话表**、SQL service_role 最小权限、原始 0037/0054–0060 SQL、真实历史草稿恢复 RPC、CSRF 越权/跨用户读取、撤销、会话失效、跨实例数据库原子限流。
- GoTrue REST 上游在测试里仍为显式注入的合成 `/auth/v1/user` 响应（测试 token 虚构、没有有效签名），但功能开关、`auth.sessions`、实时 CMS 角色和真实内容版本均来自一次性 **真实 PostgreSQL**，不是 JS 内存状态机。
- 专项 GitHub Actions 在先执行原 G2-F SQL E2E 后，才执行 G2-H.5 TLS+数据库集成脚本；容器使用 Unix socket 内的 `docker exec`, 不访问远程 Supabase，不新增 Auth 账号或真实来源 HTTP 请求。
- 会话首次发放通过测试进程**直接调用** `issueSyntheticVerifiedSession`，没有 `/login`、注册、HTTP JWT 交换或对公网开放的认证接口。返回 Cookie 使用 `Secure; HttpOnly; SameSite=Strict`，真实 CSRF 原始 token 只在测试登录颁发时拿到，数据库保存摘要。
- 测试结束前关闭仅容器内的 `account_auth/cms_editor` 开关，确认不允许新会话发放。所有永久环境开关保持 OFF。

## 分级验收

| 项目 | 判定原则 |
|---|---|
| Node HTTPS BFF 与数据库事务一体化 | 以新专项实际测试 PASS 为准 |
| 跨 BFF 实例同一个 Cookie 与会话撤销 | 必须是真实数据库共享而非 JS Map |
| 真实 CMS 恢复版本及未重新核验标识 | 必须检查原始 SQL 写入结果 |
| 实际 GoTrue 邮箱登录 / OAuth / 用户 JWT | **NOT_TESTED**；测试上游仍是合成 HTTP 响应 |
| 可信公网 BFF 与分布式密钥管理 | **NOT_IMPLEMENTED**；测试模块不能作为部署入口 |
| 正式 CMS 审核、管理及 Cloudflare 同步 | **NOT_IMPLEMENTED** |

## 安全冻结

本轮不执行 Staging/Production 真实 CMS 正向数据写入、不部署新的 Supabase Edge 或 Cloudflare Worker。原有 Staging 私有会话表保持 0 条真实记录；账号、CMS、撮合全关。独立测试不使用收费浏览器和真实用户资料、JWT、邮箱凭证或研究 Artifact。

**P4.41 严格不变**：原 UTC 00:55/06:55/12:55/18:55 四调度槽、日 Claim、HN 7/RSS 1/GitHub REST 2 调用上限，push 的构建 SUCCESS 不视为 schedule 采集。Cloudflare 内部路径软 404 仍是后续独立问题。

## 后续真实上线阻塞

需要经过审批的同源 HTTPS 运行平台与安全密钥托管、跨节点会话持续性和加密密钥轮换实测、真正 GoTrue 邮件链接/JWT 正向验证、面向服务端审计的 CMS 列表/编辑/API 投影、真实运营用户角色 E2E。未全部验收前不开放生产。