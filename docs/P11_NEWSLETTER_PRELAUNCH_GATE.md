# P1.1 Newsletter 上线前 Gate 冻结

状态：FREE_FIRST / PRELAUNCH

## 目标

在没有正式域名、没有 Resend Production 凭据时，继续允许用户表达订阅意向，但所有真实邮件发送保持 fail-closed。

关键规则：

- Resend API Key 存在不等于可以发信。
- newsletter_from_email 存在不等于可以发信。
- 只有 newsletter_launch_ready_v01() 为 true 时，确认邮件 dispatcher 与 daily sender 才允许进入真实发送链。
- Launch Gate 默认全部 false。
- 未开闸时 newsletter-subscribe 继续落到 WAITLIST，不伪造确认邮件或 ACTIVE 状态。

## Production 开闸条件

以下条件必须全部显式 PASS：

1. sender_domain_verified
2. confirmation_e2e_pass
3. daily_digest_e2e_pass
4. unsubscribe_e2e_pass
5. bounce_complaint_handling_pass
6. security_review_pass

并且 newsletter_provider_ready_v01() 必须为 true。

## 当前策略

- 域名购买：DEFERRED
- Resend：FREE_FIRST
- 当前官网：https://jianshi-bua.pages.dev/
- Production 实发：CLOSED
- WAITLIST：保持可用
- 任何单独配置凭据的动作都不能自动打开 Production 发件。
