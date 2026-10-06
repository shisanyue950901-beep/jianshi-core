# 见势 R8.3｜账户前端准备层

## 当前状态
Production Supabase Auth 官方 settings 实测：
- email = true
- disable_signup = false
- mailer_autoconfirm = false
- anonymous_users = false
- 第三方 OAuth = 全部关闭

因此产品方向确定为：
邮箱 Magic Link / OTP。

## 为什么现在不直接开放
当前项目未配置自定义 SMTP。

Supabase 官方说明：
- 默认 Auth 邮件服务只适合试用；
- 默认提供商发送额度非常低；
- 未配置自定义 SMTP 时，公开用户的邮件发送受到严格限制；
- 生产建议使用自定义 SMTP。

所以 R8.3 固定：
JIANSHI_AUTH_ENABLED=0

生产导航不显示“我的见势”，详情页也不显示收藏/观察按钮。

## 已准备完成

### /account/
隐藏路由，默认：
- noindex,nofollow
- 不出现可提交登录表单
- 明确说明账户数据层已完成，但登录邮件尚未开放

### 开关启用后
自动出现：
- 导航“我的见势”
- 邮箱 Magic Link 登录
- 我的收藏
- 我的观察
- 最新提醒
- 详情页“收藏机会”
- 详情页“加入观察”

## 客户端
Supabase JS：
@supabase/supabase-js 2.117.1

只使用 publishable key。
绝不在浏览器放：
- service_role
- database password
- Resend API key

## 最小权限修复
R8.1 早期 my_* security_invoker views 需要关联内部 opportunities 表。

R8.3 不给 authenticated 开放内部表，而是替换为三个 narrow RPC：
- get_my_saved_opportunities_v01
- get_my_watchlist_items_v01
- get_my_alert_events_v01

RPC：
- security definer
- 固定 search_path=public
- 必须 auth.uid() 非空
- 所有结果按 auth.uid() 过滤

## 开闸条件
只有以下全部通过，才把 JIANSHI_AUTH_ENABLED 改为 1：
1. Supabase Auth 自定义 SMTP 已配置；
2. 用真实可控邮箱完成 Magic Link E2E；
3. A/B JWT 隔离测试 PASS；
4. 收藏 PASS；
5. 加入观察 PASS；
6. 站内提醒只返回本人数据 PASS；
7. 退出登录与 session refresh PASS；
8. Security Advisor 无新增高风险问题。

任何一项未通过，都保持生产登录入口关闭。
