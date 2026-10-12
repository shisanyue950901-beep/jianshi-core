# 见势 F2.1｜G1-H 修复：Staging Edge HTML 被禁用，改用 Cloudflare Pages 预览

日期：2026-10-12。仅测试环境。保留正式账号 / CMS / 撮合默认关闭、P4.41 schedule 和研究预算不变。

## 真实观察

- Staging SMTP 先前 Auth HTTP 200，用户 QQ 收到邮件；数据库 auth.users 统计 confirmed_users=1、users_with_sign_in=1。
- 旧 Staging Edge 回调响应被网关强制设为 text/plain，CSP=default-src 'none'; sandbox。页面即使 HTTP 200 也只能显示源码，JS 不执行，不能算真正登录通过。
- 新 Cloudflare Pages **预览分支** staging-auth-callback (非 main)，部署地址：
  https://staging-auth-callback.jianshi-bua.pages.dev/_qa/staging-auth/
- 私有只读探针 #202：HTML HTTP 200 且 Content-Type text/html; charset=utf-8；#203：JS HTTP 200、Content-Type application/javascript。CSP/X-Frame-Options/no-referrer/noindex 已实际通过。
- Staging Edge v3 GET 返回 HTTP 302 Location 指向上述预览站（pg_net #204 请求自动重定向为 HTTP 200，Location 与预览页内容可见）；浏览器依据标准继承原 URL fragment，避免在服务端记录令牌。需浏览器实测确认。
- CI 和静态构建不是 E2E。浏览器中 URL fragment 清除、JWT /auth/v1/user、sessionStorage 刷新及退出动作仍需实际验收，不能报 PASS。

## 源码和安全边界

- web/staging-auth-preview/index.html 与 callback.js 仅公开 Supabase Publishable Key（可供客户端使用）；禁止 service_role/private key。
- 修改的 scripts/release/p412_build_public.py 仅当 CF_PAGES_BRANCH=staging-auth-callback 才复制到 web/dist/_qa/staging-auth，并附加严格安全响应头。即使未来误合 main，也不会向生产 branch 发布。
- Staging Edge 源码独立更新；Production Edge / 数据表 / 功能开关保持未改动。
- 此分支作为长期 staging 预览分支，不得直接合并 main；可用 draft PR 审计并执行 CI。
- 登录成功仅代表 Auth，不能证明 CMS 内部角色、企业隔离、收藏、完整八项 Auth Gate。

## 验收/操作

1. 回到显示原 HTML 源码的 Staging 回调标签页，按 F5；HTTP 302 应跳到 Cloudflare preview，原 fragment 的短期 session 应由前端获取并立刻清除。
2. 页面应显示「Staging 登录验证通过：已确认邮箱，JWT 身份验证通过。」刷新确认后，再按「退出测试会话」。
3. 若原 fragment 不存在或失效，直接更新 Staging Auth 的 Site URL 和 Redirect URLs 到 Cloudflare preview URL，重新发一次 Magic Link（不发送完整链接）。
4. 失败时检查 HTTP 内容类型、控制台 CSP/CORS、Staging publishable key、Auth E2E 聚合计数。绝不启用生产登录/CMS。

## 2026-10-12 实际登录与退出追加验收（覆盖上方「待验收」的历史状态）

**真实浏览器证据**：操作者收到新 Magic Link，在 Cloudflare Staging 预览页完成验证流程，随后页面显示「已退出并撤销当前测试会话。」；该状态只有会话检查通过并执行退出请求得到成功 HTTP 响应后才可由当前前端显示。请勿将纯静态/CI 运行当作登录事实。

**只读数据库聚合复核**：`auth.users` 共 1 名测试账号、1 名已验证、1 名存在登录记录；`auth.sessions` 在退出后剩余 0；`product_feature_flags` 的 `account_auth`、`cms_editor`、`v2_matchmaking` 仍全部为 `false`。

**只读 Auth 日志聚合**：`2026-10-12T08:51:00Z`—`08:58:00Z` 窗口 `auth_logs=5`、含 login/signed 关键词事件 2、含 logout 关键词事件 1、含 error/expired 事件均 0。这是与浏览器动作相互印证的日志聚合，不含邮箱正文、令牌或账号信息。

**当前最新判断**：
- QQ SMTP/收件/邮箱确认：PASS。
- Magic Link → 已验证用户的 JWT `/auth/v1/user` 检查 → 服务端 logout：**PASS（Staging 一账号的实际端到端流程）**。
- 页面刷新仍保持登录：NOT_TESTED；浏览器刷新时再次验证当前 JWT：NOT_TESTED。
- 退出后沿用旧 token 发起接口请求必须失败、不同测试用户 A/B 权限隔离、收藏/观察/提醒/私有 CMS 正向业务 E2E：NOT_TESTED。
- **八项生产 Auth Gate 不得因为这一项成功而统一设置 PASS**，生产与 Staging 功能开关继续关闭。

现行 Staging Edge Function 是 v4 纯 GET 302 跳转；早期 v2 HTML 与 v3 记载仅作事故历史。独立 Cloudflare branch 预览成功不代表主站账号上线。
