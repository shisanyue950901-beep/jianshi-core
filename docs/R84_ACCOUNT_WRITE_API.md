# 见势 R8.4｜账户写操作最小权限收口

## 目标
在正式打开登录前，把浏览器对用户私有表的直接写入权限收回。

R8.3 已经把读取收敛为窄 RPC。
R8.4 将写入也收敛为窄 RPC。

## 新增 RPC
- save_my_opportunity_v01(opportunity_id)
- watch_my_opportunity_v01(opportunity_id)
- mark_my_alert_read_v01(alert_id)

三者都：
- 只允许 authenticated 执行
- 必须 auth.uid() 非空
- 固定 search_path=public
- 只能操作调用者自己的数据
- 不向 anon 开放

## 权限变化
authenticated 不再直接访问：
- saved_opportunities
- watchlists
- watchlist_items
- user_alert_events

前端不再执行：
- saved_opportunities upsert
- watchlists select
- watchlist_items upsert

而是调用窄 RPC。

## 提醒已读
用户点击自己的提醒后，客户端调用 mark_my_alert_read_v01。
函数按：
alert_id + auth.uid()
更新，不能标记其他用户提醒。

## 当前生产开关
JIANSHI_AUTH_ENABLED 仍保持 0。

R8.4 不改变登录开闸条件：
1. 自定义 SMTP 已配置；
2. Magic Link E2E PASS；
3. A/B JWT 隔离 PASS；
4. 收藏 PASS；
5. 加入观察 PASS；
6. 站内提醒本人数据隔离 PASS；
7. 登出 / Session Refresh PASS；
8. Security Advisor 无未解释的高风险问题。

SMTP/Auth E2E 未通过前，公开导航和机会详情仍不出现账户入口。
