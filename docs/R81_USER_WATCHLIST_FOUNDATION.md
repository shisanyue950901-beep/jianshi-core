# 见势 R8.1｜用户收藏与观察清单基础

## 产品原则
公开榜单、机会详情、今日机会、值得做、值得讲继续无需登录。

登录的价值不是“解锁本来能看的内容”，而是：
- 收藏机会
- 建立个人观察清单
- 选择要监控的变化
- 后续接入提醒

## 数据对象

### user_profiles
私有用户资料。
默认：
- locale = zh-CN
- timezone = Asia/Shanghai

### saved_opportunities
一键收藏。
支持私有备注，最多 2000 字。

### watchlists
用户可建立多个观察清单。
新用户自动生成：
“我的观察清单”

每个用户最多一个默认清单。

### watchlist_items
跟踪某个机会，并准备三类提醒开关：
- 首次通过多源验证
- 新增有效证据
- 分数变化

默认分数变化阈值：3.00。

### alert_preferences
提醒总开关。
R8.1 默认：
- 站内提醒 = 开
- 邮件提醒 = 关
- 每日摘要 = 关
- 每周摘要 = 关

不会因为用户注册就自动订阅邮件。

## 安全

所有用户表：
- RLS = ON
- anon = 无权限
- authenticated = 仅按 auth.uid() 访问自己的数据
- watchlist_items 通过所属 watchlist 的 user_id 验证所有权

新 Auth 用户 trigger：
auth.users INSERT
→ user_profiles
→ 默认 watchlist
→ alert_preferences

## Staging 验收策略
当前工具安全层不允许通过自动化写入 Auth 密码或直接构造 auth.users 测试用户，因此 R8.1 采用：
- migration execution
- pg_policies 检查
- grants 检查
- trigger/function 检查
- security advisor
- CI contract tests

真实 A/B JWT 隔离测试在 R8.2 登录通道接通后执行，不伪造 PASS。
