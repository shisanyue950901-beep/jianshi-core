# 见势 R8.6｜Auth 正式开闸 Gate

## 原则
登录入口不能因为一个环境变量误配就被打开。

生产账户功能改为双钥匙：
1. 构建侧 JIANSHI_AUTH_ENABLED=1
2. Production 数据库 account_auth=true 且 8 项 Auth Gate 全部 PASS

任一条件不满足：
AUTH_ENABLED = FALSE

## 8 项硬 Gate
1. custom_smtp_configured
2. magic_link_e2e_pass
3. jwt_ab_isolation_pass
4. save_e2e_pass
5. watch_e2e_pass
6. alerts_isolation_pass
7. session_logout_refresh_pass
8. security_review_pass

## 数据库
auth_launch_gates：
保存每项验收事实，不对 anon/authenticated 开放。

product_feature_flags：
account_auth 默认 false。

set_account_auth_feature_v01(true)：
只有 auth_launch_ready_v01()=true 才允许打开。
否则数据库直接抛出 AUTH_LAUNCH_GATE_NOT_READY。

public-feed 只公开最终布尔值：
features.account_auth

不公开内部测试证据或安全配置。

## 前端防刷
Magic Link 请求增加 60 秒客户端冷却，与 Supabase 服务端 rate-limit 叠加。
客户端冷却不是安全边界，只用于减少误点和重复邮件。

## 当前 Production 探测
/auth/v1/settings：
- email = true
- disable_signup = false
- mailer_autoconfirm = false
- anonymous_users = false
- 第三方 OAuth = false

这些设置适合 Magic Link 方向，但不代表 SMTP 已经生产可用。

## SMTP
Supabase 官方生产建议使用自定义 SMTP。
默认 SMTP 不作为见势正式开闸条件。

当前 Production Vault 仍缺：
- resend_api_key
- newsletter_from_email

因此：
- newsletter provider_ready = false
- account Auth Gate 必须保持 false
- JIANSHI_AUTH_ENABLED 必须保持 0

## E2E 顺序
SMTP 接通后按以下顺序验收：
1. 可控测试邮箱请求 Magic Link
2. 收信并点击，进入 /account/
3. Session 建立并刷新后仍有效
4. 用户 A 收藏一个机会
5. 用户 A 加入观察
6. 用户 A 读取自己的提醒
7. 用户 B 登录
8. B 无法读取/修改 A 的收藏、观察和提醒
9. A/B 分别退出登录
10. Security Advisor 复核
11. 8 项 Gate 逐项记录 PASS
12. set_account_auth_feature_v01(true)
13. 构建开关切到 1
14. Production 静态重建
15. 公网 /account/ 与机会按钮验收

## 回滚
任何 E2E 异常：
- 立即 set_account_auth_feature_v01(false)
- JIANSHI_AUTH_ENABLED 保持/恢复 0
- 不删除用户数据
- 修复后重新跑全部 Gate
