# 见势 JIANSHI 2.0｜F2.1 G1-E｜CMS 身份与私有 HTTP 网关

日期：2026-10-11。阶段：G1-E 安全接入。**禁止宣传为生产 CMS 正式上线。**

## 一、本批次交付

| 文件 | 作用 | 对外是否开放 |
|---|---|---|
| `db/migrations/0056_jianshi_cms_session_guard.sql` | 只读会话存在性检查和仅 service_role 可调用的 RPC 转接器 | 否，仅 staging |
| `supabase/functions/cms-staging-gateway/index.ts` | 仅 staging、强制 JWT 验证的私有 CMS HTTP 网关 | 必须锁定 |
| `tests/test_f21_g1e_verified_gateway.py` | 对身份、会话、SQL 权限、字段白名单及公私隔离进行回归 | 本地/CI |

## 二、服务端真实操作路径

认证后的内部请求 → Supabase Functions 平台验证 JWT (`verify_jwt=true`) → 断言 staging URL → 运维开关 `JIANSHI_G1E_API_GATE=AUTH_E2E_APPROVED` → CMS、账号数据库开关及既有 Auth 8 项 E2E 全通过 → 服务端经 `auth.getUser(token)` 获取可信用户 → 验证 JWT 用户、角色、发行方、到期及 session_id → 私有 `auth.sessions` 检查会话未吊销 → 服务端根据可信 user.id 自动指定 `p_actor` → service_role 的 PostgREST RPC 转交既有私有 CMS 事务 → 审核/版本/素材门禁再判断。

**默认状态：** 运维开关不存在，`cms_editor=false`、`account_auth=false`。即使 staging Edge Function 存在，也不能写入。前端不能自行提升角色，不能传入 actor_id，不能在浏览器使用服务端密钥。

会话检查采用一段被限制在 `jianshi_cms` 私有 schema 的 `SECURITY DEFINER` 布尔函数，是因为 service_role 无法直接读取 `auth.sessions`。该函数只返回真/假，不返回表列、会话令牌或用户资料；仅 service_role 可以执行。两条暴露于 `public` API schema 的 RPC 由 `SECURITY INVOKER` 执行，并且显式撤销 PUBLIC/anon/authenticated 权限。这是安全敏感代码，必须保留专门测试、审计和授权检查。

## 三、已实现的路由（仅作为 staging 内部合同）

- `POST /cms-staging-gateway/drafts`：创建本人草稿；服务端从 JWT 派生账号。
- `POST /cms-staging-gateway/edit`：带期待版本号的草稿编辑。
- `POST /cms-staging-gateway/review`：审核状态转换；作者不能自审，发布须来源、版权及独立角色校验。

路由不向浏览器开放跨域 CORS；拒绝 Origin 请求，避免未经审批误接入生产前端。内容最大 12KB、请求字段白名单、仅 JSON、幂等 UUID；禁止记录 JWT、内容正文和数据库异常详情。真实管理员界面及私有素材上传仍未接入。

## 四、G1-E 功能开启前必须通过

1. 自定义 SMTP/验证码等八项 Auth 启动门禁全部达标；保持两个功能开关为 false 直至正式验收。
2. 提供至少两名合成测试作者、两名审核员和独立发布者；由可信后台授予角色，不通过注册页面自授。
3. 进行真实 JWT、退出后旧 token、过期/吊销 session、会话归属、管理员降权 E2E。
4. 两人并发编辑、错误版本、重复 request_id、拒绝/撤回、素材无许可、版权不明、非法来源 URL 各有对应失败断言。
5. 限流、CSRF/同源、异常审计、应用日志脱敏、独立私有对象存储和媒体扫描通过。
6. 后台 UI 连接 staging API，真实业务使用权限和 E2E 经安全复核。
7. 所有功能分开验收：HTTP 网关已部署 ≠ 登录成功 ≠ CMS 编辑成功 ≠ 生产发布授权。

## 五、运行验收栏（需填实际事实）

- [x] PR #127 首轮 CI 已通过；最终代码需再次运行并在合并后重验
- [x] staging 三个新函数实际核验：仅 service_role 可执行；合成无效会话返回 false
- [x] staging Edge Function cms-staging-gateway v1 ACTIVE，平台 verify_jwt=true；修复后需更新部署版本
- [x] 未携带 Authorization 的实际 GET 请求返回 HTTP 401；数据库开关仍全部 false
- [x] production CMS schema/标记均不存在，account_auth=false；staging 三开关均 false
- [ ] GitHub 主分支构建及 Cloudflare Pages 成功
- [ ] 全部 E2E 正向业务：**NOT_TESTED（未满足 Auth 安全前提，不允许冒充通过）**

## 六、持续隔离

不更改原 UTC 四个采集槽、HN Algolia 7／RSS 1／GitHub REST 2 限额，不更改数据库生产认证开关，也不触碰原研究匿名数据正文。内部测试稿、管理页面、RPC 参数或敏感素材不得导出到 `web/dist`。任何阶段不得通过关闭 RLS、公开 service_role 密钥或临时启用真实账号绕过门禁。

## staging 已执行的权限与发布核验（2026-10-11）

- PR #127：https://github.com/shisanyue950901-beep/jianshi-core/pull/127 。
- 已执行 0056 SQL staging 迁移，返回 success=true。私有 jianshi_cms.session_is_active 为安全限定布尔 SECURITY DEFINER；public 的两个精确 RPC 是 SECURITY INVOKER，三个函数 anon/authenticated EXECUTE=false，service_role EXECUTE=true。没有产生新内容或分配测试管理员。
- 无真实会话的全零合成用户/session UUID 返回 false。staging account_auth/cms_editor/v2_matchmaking 均 false，CMS content_items=0、editor_grants=0。
- Edge Function 首版 `cms-staging-gateway` staging 部署 ACTIVE 且 verify_jwt=true；不携带 JWT 的真实 HTTP GET 返回 401，未发现意外放开公共访问。
- production 再次只读验收：CMS schema 不存在、cms_editor flag 不存在、account_auth=false。
- Supabase advisor 对这次 CMS 私有函数未发现新的 WARN/ERROR；既有私有 CMS 表在 INFO 级提示无 policy，此为有意默认拒绝。其他非 CMS 历史警告未在本轮改动。

**尚无的证据：** 已登录用户成功提交、同一会话撤销后拒绝、实际 CMS 写入及并发 CAS E2E、安全完整压测。下一阶段必须完成，不能把 HTTP 401 或 SQL 权限核对当作完整 E2E。
