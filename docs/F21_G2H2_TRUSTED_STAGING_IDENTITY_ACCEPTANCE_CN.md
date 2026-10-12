# 见势 F2.1｜G2-H.2 可信身份适配层（第一批）

时间：2026-10-12。**范围：Staging 后端身份验证合同与独立安全回归；不提供公网 BFF 登录服务。**

## 实际交付

- `db/migrations/0059_jianshi_cms_trusted_role_read.sql`：新增 `public.cms_internal_actor_role_v01`，执行时委托 0055 的 `ensure_write_gate` 检查所有 Auth/CMS 发布门禁并实时读取 `editor_grants`。函数为 `SECURITY INVOKER`，普通登录角色和匿名用户均不得执行；仅 service_role 允许调用，角色信息不写入网页。
- `scripts/qa/g2h2_trusted_auth_adapter.mjs`：服务端候选身份适配层，目标 Origin 固定于 Staging HTTPS。每次调用依次核对两个功能开关、八项 Auth 发布准备状态、GoTrue `/auth/v1/user` 远程验证、JWT 关键声明和 `auth.sessions` 服务私有 RPC，最后实时查询 CMS 角色；账号不存在、会话吊销、token 失效或角色变化全部拒绝。
- 只在 GoTrue `getUser` 已返回受验证身份后解析 JWT 的非权威元数据。不能使用浏览器传来的 `actor/role`，不会缓存角色。带服务角色密钥的调用仅限服务器；重定向禁止、远端请求有 6 秒超时。
- Node 22 模拟 GoTrue HTTP 服务响应进行正向适配路径和拒绝场景测试：包含平台门禁、无效/过期/伪造声明、未确认账号、会话吊销、角色吊销、返回字段错误、传输故障、非固定项目 URL。
- 实际一次性 PostgreSQL 容器加载原始 `0037/0054–0059` 迁移，校验新增 SQL 角色 RPC 只有可信服务角色可执行、非法身份拒绝，以及旧的 CMS 恢复/并发回归。容器内允许合成门禁，绝不向现有环境申请临时正向放行。

## 严格验收等级

| 证据 | 结论范围 |
|---|---|
| Node 模拟远端身份适配测试 | 适配层逻辑正确，不证明真实 GoTrue 账号已经完成 JWT 正向 E2E |
| 一次性 PostgreSQL SQL E2E | 原始 CMS 数据库门禁、角色读取、事务和锁真实执行，不证明 Supabase Auth / RLS 网络链路 |
| Staging additive 0059 DDL + 关闭门禁检查（如执行） | 仅证明新私有函数最小权限、拒绝关闭场景 |
| 真实用户使用浏览器进入 CMS 后台 | **NOT_TESTED**，不得开放账号、CMS 或撮合权限 |

## 隔离与质量债务

- 现有 `/scripts/*` 在 Cloudflare Pages 某路径触发 302 到首页，最终 HTTP 200，是需单独路由修复的软 404，而不是源码泄漏。必须先确认 Cloudflare Pages Functions 的实际构建、部署和回退机制，不能把无依据的 `_redirects 404` 规则直接用于正式站。
- 不部署身份适配层到公网、Cloudflare、Supabase Edge。它目前只是可被可信服务端引用的未启用模块。
- 不接收或输出聊天中的登录邮件链接、会话 JWT、Service Role Key 或客户正文。
- P4.41 `event=schedule` 的 UTC 00:55、06:55、12:55、18:55 和每日 claim / HN7+RSS1+GitHub2 限额不变；push CI/静态构建不计入真实采集。

## 下一批 G2-H.3

由经过批准、支持同源 HTTPS 的 BFF 部署环境承接此适配层，采用 Secure/HttpOnly/SameSite Cookie、CSRF、可靠服务器会话存储、速率限制和多用户资源读取权限。然后在专门隔离的测试账号上执行真实邮件登录→GoTrue JWT→会话撤销→审核及历史恢复 E2E。