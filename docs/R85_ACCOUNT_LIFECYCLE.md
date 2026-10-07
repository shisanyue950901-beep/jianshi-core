# 见势 R8.5｜账户生命周期与隐私控制

## 目标
登录开放后，用户不能只有“添加”，还必须能够撤销、退出和清理自己的行为数据。

## 新增能力
- 取消收藏
- 移出观察
- 提醒标记已读
- 查看提醒偏好
- 更新提醒偏好
- 清空见势行为数据

## 清空见势数据
clear_my_jianshi_data_v01 会删除：
- saved_opportunities
- watchlist_items
- user_alert_events
- 非默认 watchlist

并恢复默认观察清单和默认提醒偏好。

不会删除：
- auth.users 登录身份
- newsletter_subscribers 订阅关系

账户登录与邮件订阅是两个独立授权关系，不能把“清空站内行为数据”解释为“退订邮件”或“删除登录账号”。

## 前端
我的见势增加：取消收藏、移出观察、提醒偏好、清空收藏与观察数据。清空操作必须二次确认。

## Bug 修复
R8.4 的提醒已读绑定误用单元素选择器。R8.5 改为多元素选择器，保证所有提醒行都能绑定已读操作。

## 开闸状态
JIANSHI_AUTH_ENABLED 继续保持 0。本批不绕过 SMTP / Magic Link E2E Gate。
