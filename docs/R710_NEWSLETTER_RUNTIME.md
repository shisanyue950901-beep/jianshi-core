# 见势 R7.10｜邮件运行时闭环

## 目标
把 R7.5 的轻量订阅从“能收邮箱”推进到完整运行时：

WAITLIST → 确认邮件 → ACTIVE → 每日 Top 10 → 退订

代码完整上线后，即使 Resend 凭证尚未配置，也保持 fail-closed，不会误发。

## 状态
### WAITLIST
邮件供应商尚未配置，或确认邮件暂时无法排队。

### PENDING_CONFIRMATION
确认邮件已经进入发送队列，等待用户点击确认。

### ACTIVE
用户完成双重确认，允许进入每日邮件发送池。

### UNSUBSCRIBED
用户主动退订，不再进入发送池。

## 稳定退订
R7.10 不再依赖必须保存原始随机退订 Token。

内部生成 newsletter_signing_secret，仅保存在 Supabase Vault。
退订链接：
subscriber UUID + HMAC-SHA256 signature

特点：
- 原始 signing secret 不出 Vault
- 数据库不保存可直接使用的退订 Token
- 每封历史邮件中的退订链接长期有效
- signing secret 轮换时可整体失效（如发生安全事件）

## WAITLIST 自动补确认
newsletter-dispatch-confirmations：
- 每小时执行一次
- provider 未配置 → no-op
- provider 可用 → 每次最多 20 个 WAITLIST
- 生成一次性确认 Token
- DB 只保存 SHA-256
- 队列失败自动回退 WAITLIST，避免卡死在无法确认的 PENDING 状态

## 每日 Top 10
newsletter-daily：
- 每天 09:10（Asia/Shanghai）执行
- 只查询 ACTIVE
- 读取 public_daily_brief_v01 前 10
- 每用户/每日最多一条，数据库 unique(subscriber_id, send_date) 硬幂等
- 邮件内含稳定退订链接
- 邮件只称“机会研究”，不做收益承诺

## Resend 凭证
运行时仍需要 Supabase Vault：
- resend_api_key
- newsletter_from_email

已存在：
- jianshi_project_url
- jianshi_publishable_key
- newsletter_signing_secret（由迁移内部生成）

在前两个外部凭证缺失时：
- 订阅表单继续正常收 WAITLIST
- hourly dispatcher no-op
- daily sender no-op
- 不会虚构“已发送”

## Cron
- 确认补发：每小时第 12 分钟
- 每日 Top 10：UTC 01:10，即北京时间 09:10
