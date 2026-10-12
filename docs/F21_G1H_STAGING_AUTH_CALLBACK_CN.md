# 见势 F2.1 G1-H｜隔离 Staging 邮箱回调验收

日期：2026-10-12。范围：仅 jianshi-staging Auth 邮箱确认 / 临时会话核验。**禁止部署到生产 Supabase 或公开静态站**。

## 交付及证据

- 代码：`supabase/functions/jianshi-staging-auth-callback/index.ts`；静态回调页及服务端 JWT 验证均属于 staging，不接入私有 CMS。
- staging Edge Function：`jianshi-staging-auth-callback` v2 ACTIVE，因页面本身无需 JWT 可公开访问，`verify_jwt=false`；**所有 POST 会话操作在函数体中验证带签名 Bearer 用户身份，邮箱已确认且为隔离测试账号**。
- 实际 HTTP：GET 回调页面 200（private probe id=197）；不带 Authorization 的 POST /session 401 NO_TOKEN（id=198）。以上均不等于带真实 JWT 的正向 E2E。
- 邮件：此前首次注册请求获得 Auth HTTP 200，用户确认收件；原始确认链接的回调是 `http://localhost:3000`。令牌曾出现在聊天中，不能继续使用旧链接。
- 隐私：浏览器收到 URL hash 后立即清除；令牌不出现在回调页正文或服务端日志；no-store/no-referrer/CSP/noindex。
- 路由：Supabase Edge 内部可能将 `/functions/v1/slug` 重写为短路径；v2 放宽 GET 内部路径、POST 仍严格限制到 session/logout。

## 唯一必须手工的控制台配置

在 **jianshi-staging** Authentication → URL Configuration 中：
- Site URL：`https://apuibjhxinumxbfnqlkp.supabase.co/functions/v1/jianshi-staging-auth-callback`
- Redirect URLs：添加上述**完全相同**的 HTTPS URL，避免宽泛通配。
- 不要修改 **jianshi-prod** 的 Site URL，也不要改生产账号开关。

保存以后，从 staging 发起**一次全新的**发信请求，确认新邮件的 redirect_to 是上述 URL。完成点击、JWT 正向鉴权、刷新同页及退出 E2E 后才能打勾。**旧邮件链接不复用**。

## 未完成 / 禁止宣称 PASS

- Auth URL Configuration 尚需控制台人工保存；本 PR 无法修改托管项目 Auth 配置。
- 完整注册回调/JWT/刷新后持久性/登出后台会话吊销、A/B 跨用户权限仍 NOT_TESTED；只验证了无凭证访问会拒绝。
- staging `account_auth`、`cms_editor`、`v2_matchmaking` 保持 false；production 功能开关及 CMS 零改动。
- P4.41 原有四个 schedule 时槽、HN7/RSS1/GitHub2 限额完全不变。

## 最新修正与终态（2026-10-12；以下覆盖本文早期 v2 阶段描述）

首次实现 v2 将 HTML 放在 Supabase Edge Function 内，由于平台实际以 `text/plain` / sandbox 下发而无法运行。现已改为 **Staging Edge v4 纯 GET 302 跳转到 Cloudflare Pages 预览分支** `staging-auth-callback`；静态 HTML 与 JS 置于该分支，使用非特权 publishable key，由浏览器调用 Staging Auth。任何主站构建不得发布预览登录页面。

2026-10-12 浏览器实际截图显示「已退出并撤销当前测试会话。」；代码路径要求先有 `/auth/v1/user` 已验证身份，且退出 HTTP 请求成功，才能显示这条反馈。同窗口 Auth 日志聚合：登录相关 2、退出相关 1、错误 0；数据库退出后 `auth.sessions=0`、已确认用户 1。故单账号 Magic Link/身份核验/退出 **PASS**；独立刷新、过期会话、A/B 跨账号、收藏/观察/提醒、CMS 写入及全部八项 Auth Gate **未完成**。

原文提及的 v2 Edge POST /session 路由已删除，勿据历史说明调用；版本 v4 只提供 GET 302，POST 为 405。保持生产项目无改动；Staging 的 `account_auth/cms_editor/v2_matchmaking` 全部 false。完整更新见 [Cloudflare 预览修复与验收](F21_G1H_CLOUDFLARE_PREVIEW_FIX_CN.md)。
