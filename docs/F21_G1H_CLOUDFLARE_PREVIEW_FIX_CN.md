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
