# 见势 R7.5｜轻量订阅与多源机会扩展

## 目标
1. 不做完整账号系统，先验证用户是否愿意持续接收“每日 Top 10 机会”。
2. 不降低多源 Gate 标准，通过增加新的官方 GitHub 发现查询，让更多已有商业赛道获得第二类独立证据。

## 多源扩展
新增 GitHub 查询：
- ecommerce
- affiliate_marketing
- newsletter
- youtube

映射：
- 轻量电商品牌与 Amazon 资产 ← ecommerce
- 联盟营销与内容资产 ← affiliate_marketing
- 创作者媒体资产 ← newsletter + youtube
- 原有 AI Agent / LLM / SaaS 保持不变

Staging 真实采集：
- discovery queries: 8
- unique repositories: 379
- quality gate: PASS
- multi-source opportunities: 1 → 4

## 订阅状态机
PENDING_CONFIRMATION → ACTIVE → UNSUBSCRIBED

同时支持：
- BOUNCED
- COMPLAINED

安全原则：
- 不需要账号和密码
- 邮箱表不开放 anon/authenticated 直读写
- 仅 Edge Function 使用 service-role
- 确认 Token / 退订 Token 只保存 SHA-256 哈希
- 同邮箱 10 分钟冷却
- 蜜罐字段过滤简单机器人
- 双重确认后才进入 ACTIVE
- 未配置邮件服务时 fail-closed，只记录订阅意向

## Resend 状态
ChatGPT 中连接 Resend 不等于 Supabase 生产环境自动获得 Resend API Key。
生产自动发信需要：
- resend_api_key
- newsletter_from_email
写入 Supabase Vault。

在这两个生产密钥接入前：
- 网站可以收集订阅意向
- 状态保持 PENDING_CONFIRMATION
- 前端明确提示邮件通道正在启用
- 不会虚假显示邮件已发送

## 前端
首页和四个日报页增加：
“每天把 Top 10 机会发给我”

不设注册墙。
