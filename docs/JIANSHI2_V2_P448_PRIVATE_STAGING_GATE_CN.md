# JIANSHI 2.0｜V2 商业撮合安全试点（P4.48）

**记录日期：2026-10-11。状态：STAGING PRIVATE BACKEND PASS / PUBLIC LOCAL DRAFT ONLY。**

## 一、本轮可以真实使用的功能

### 企业端：`/marketplace/brief/`
- 本地整理项目名、实际问题、成果、素材授权、交付验收、工期和保密要求。
- 点击“生成本地草稿”展示纯文本，可主动复制；可清空。
- 不需要账号、手机号、邮箱、企业证件；没有服务端上传和订单创建接口。

### 创作者端：`/talent/portfolio/`
- 本地整理擅长方向、代表作品、真实贡献、授权范围和交付方式。
- 区分演示作品与客户授权案例；同样只在浏览器页面存在，不上传到任何服务。

**隐私约束：** 不使用 `fetch`、`XMLHttpRequest`、`sendBeacon`、`WebSocket`、第三方脚本、`localStorage`、`sessionStorage`、Cookie 或后端提交。浏览器刷新后内容不保留；复制由用户主动触发，用户负责选择安全保存位置。所有输入更新使用 `textContent`，不用 `innerHTML` 注入用户内容。

两个工具是 **草稿准备能力**，绝不宣传为已经具备发布商单、真实竞标或企业撮合。

## 二、staging 私有数据模型

仅在 **jianshi-staging** 建立以下表，位于非公开 `jianshi_v2` schema：

| 表 | 作用 | 发布权限 |
|---|---|---|
| `organizations` | 企业基本身份与审核 | 默认私有 |
| `creator_profiles` | 创作者档案与展示同意 | 默认私有 |
| `portfolio_items` | 作品与版权声明 | 默认私有 |
| `service_requests` | 企业私有需求与单独审核的公开摘要 | 默认私有 |
| `request_applications` | 申请意向和沟通摘要 | 默认私有 |
| `moderation_events` | 管理员审批审计 | 默认私有 |

SQL 基线：`db/migrations/0053_jianshi2_private_matching_foundation.sql`。

**实际 staging 验收记录：**
- 6/6 张表 `RLS = true` 且 `FORCE RLS = true`；
- 6/6 张表的 anon SELECT、authenticated SELECT、authenticated INSERT 均为 false；
- anon / authenticated 无该 schema 使用权限；
- staging 的 `v2_matchmaking=false`、`account_auth=false`；
- **生产 Supabase 尚不存在 `jianshi_v2` schema 或 `v2_matchmaking` 标记**；
- 本轮没有读写任何真实需求、创作者个人内容，也没有造测试商单。

以上检查是权限元数据核验，**不是**完整 E2E 或渗透测试。

## 三、V2 实际开通之前必须完成

1. 完成现有 R8.6 Auth 启动全部 E2E：SMTP、Magic Link、不同用户间隔离、会话刷新和安全复核。此前不得将 `account_auth` 置为 true。
2. 在 staging 实现独立的受验证服务端 API，核验 Supabase JWT 和用户真实会话；不依据用户可编辑 metadata 做权限判断。
3. 提供企业成员授权和企业认证审核。企业只能读写其自己组织的需求草稿；除已审、已获公开授权的摘要，普通访客不能看到企业资料。
4. 创作者档案默认私有。只有作品版权、公开授权、管理员审核都满足时才可公开资料；私人联系方式单独授权。
5. 申请必须由已登录本人提交且目标需求处于已公开状态；同一个需求同一创作者不得重复投递。金额、客户联络信息和私人沟通信息不在公共列表中。
6. 审核与状态转换必须在受控服务端完成，并有审计日志、异常封禁、重复提交限制、数据导出与删除机制。
7. 完成 A/B 用户越权用例、匿名接口渗透用例、HTML 注入、反复提交、隐私删除及异常停机后的 FAIL_CLOSED 演练。
8. 再决定是否将独立 schema 安全迁移到生产。**禁止因静态页面 CI PASS 而自动部署 backend 或开启账号开关。**

## 四、生产隔离和公开内容边界

- `scripts/release/p412_build_public.py` 仍是唯一公共制品生成器；从现有源准入列表生成三个具名商业案例。
- 6 类匿名研究与正式项目档案保持独立，静态站只展示审核过的公开汇总，不读取新私有 schema。
- 不修改定时采集工作流、HN/RSS/GitHub 数据源调用上限、P4.36/P4.37 的验证策略。
- 站点新表单是纯本地编辑，不上传数据；**不是招聘平台或支付系统**。

## 五、下一阶段建议

V2.1：staging 内部 API 与两个隔离测试用户、企业认证/申请审核流程；完成角色越权和状态机测试后，才开发可切换的前端 API 接入。V2.2：经用户批准后开始小规模受控试点，仍不开放自动分账和平台托管。
