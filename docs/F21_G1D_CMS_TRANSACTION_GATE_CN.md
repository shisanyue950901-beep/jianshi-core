# JIANSHI 2.0｜F2.1 G1-D 私有 CMS 事务接口与审核门禁

日期：2026-10-11。性质：**仅 staging 的数据库事务能力**；不是正式管理员 API、公开后台、课程上传或商业订单系统。

## 第一批交付

- `db/migrations/0055_jianshi_cms_transaction_gate.sql`：新增私有角色授权表 `jianshi_cms.editor_grants`，实现四个安全函数：`ensure_write_gate`、`create_draft`、`edit_draft`、`change_review_state`。
- 只允许受信任数据库 service_role 调用私有函数；没有匿名和普通已登录角色执行许可，也不把 schema 添加到公开 Data API。
- 所有写接口第一关先检查 `cms_editor=true` 且 `account_auth=true` 且 Auth 八项验收合格；**当前三个条件没有同时满足，因此强制拒绝所有写入。**
- `editor_grants` 需要事先由可信内部管理员授予，仅具备单一 EDITOR / REVIEWER / PUBLISHER / ADMIN 权限；初始没有授权记录、`active=false`。
- 草稿插入、编辑、审核和发布均使用一个数据库事务：行锁 `FOR UPDATE`、期待版本号 CAS、不可变版本副本、不可变审核事件和请求幂等键。异常在数据库中整体回滚。
- 作者可以提交本人草稿，不能自审/自发布。审核员必须与作者不同；发布者也必须独立且具备授权。
- 对审核发布设来源、事实、版权、素材安全扫描门禁；产生的快照仅是存放在私有 schema 中的 `STAGED` 白名单，不自动发布到公开网站。撤回时在同一事务内标记对应快照 `RETRACTED`。
- 外部 `PUBLIC_URL` 仅允许不含查询、fragment、认证信息的 HTTPS URL；源引用的 JSON 嵌套字段必须精确白名单，不得随原始内容直接公开。

## API 与身份边界

这批交付的是**SQL 事务核心**，不是可以从浏览器直接访问的 HTTP API。未来需要独立服务端：
1. 验证真实 JWT、`session_id` 有效性，确保不是可由用户编辑的 metadata。
2. 服务端自行派生账号 ID、角色与组织边界，永不直接信任客户端传入的 actor_id 或 role。
3. 明确同源/CSRF 策略、正文大小上限、API 限速、审计日志脱敏；所有高危操作使用幂等键。
4. CMS 审核角色授权管理必须作为受保护的独立管理员动作；不允许使用前端自助授予 ADMIN。
5. 用 staging 两作者、两审核员、两企业的测试身份验证 IDOR、审稿自审、并发写入、断电中断和撤回。
6. 真实对象存储、安全扫描、视频转码和经授权播放 URL 尚未实现；`media_rights` 只登记权属元数据。

## 安全验收清单

- [x] PR #125 首轮 CI PASS；主分支需合并后再次验收
- [x] staging 迁移成功，第六张私有表和4个事务函数已核验
- [x] cms_editor、account_auth、v2_matchmaking 均 false，实际调用返回 PostgreSQL 42501 CMS_WRITE_DISABLED
- [x] staging 6表 FORCE RLS，anon/authenticated 无 SELECT/INSERT/EXECUTE、schema USAGE 也禁止
- [x] production 无 CMS schema 和 cms_editor 标记；account_auth=false
- [x] PR #125 合并后 Cloudflare Pages、Workers、main CI、静态快照全部 SUCCESS，原站各入口正常且内部 CMS 原型公网路径 404
- [ ] 真实 Auth/编辑/审批端到端 E2E：**NOT_TESTED（单独放行前置）**

## 尚需处理的工程债务

- 当前私有数据库事务遵循逐步状态转换，但真实 API 还需实现有效服务端会话、角色审批/撤销及并发重试策略。
- `public_allowlist_json` 是 **STAGED**；没有公开出站投影的自动流水线。
- 数据库独立校验不能替代应用层的内容来源审校或媒体病毒扫描；后续必须经过人与自动化组合审核。
- 不修改 HN Algolia≤7次/日、RSS≤1次/日、GitHub REST≤2次/日或原定 UTC 采集时槽。

**发布原则：** G1-D 阶段数据库 DDL 只允许 staging，业务功能保持关闭。未经安全验收或明确的生产发布授权，不把这个迁移应用 production。

## staging 真实权限与禁止写入证据（2026-10-11）

- 迁移工具：仅对 jianshi-staging 应用 `0055_jianshi_cms_transaction_gate.sql`，返回 `success=true`。
- 六张 CMS 表：逐表 `RLS=true`、`FORCE_RLS=true`，`anon_read=false`、`authenticated_read/insert=false`。
- 四个事务函数：`has_function_privilege(anon/authenticated,EXECUTE)=false`，`service_role=true`；公开 RLS policy 数为零。
- 三个功能标记 `cms_editor/account_auth/v2_matchmaking=false`，授权角色记录 `editor_grants=0`、内容记录 `content_items=0`。
- 直接探测数据库内部事务门禁：调用 `select jianshi_cms.ensure_write_gate(null::uuid,array['EDITOR']::text[])` 被 PostgreSQL 以 `42501 CMS_WRITE_DISABLED` 拒绝（预期结果）。
- 生产 Supabase 只读核对：没有 CMS schema 或 cms_editor 标记，账号继续关闭。

以上验证涵盖真实数据库的 **默认拒绝**，没有启用 Auth Gate 或测试完整实际编辑事务的正向路径。因此不宣称已经有可登录的 CMS 管理后台。

## G1-D 完整发布验收记录

- PR：[#125](https://github.com/shisanyue950901-beep/jianshi-core/pull/125)，合并 SHA `c89c641167bd6ae4c2825c5c378d4d8b117ef4dc`。
- 发布层独立确认：main 单元测试 SUCCESS、构建静态快照 SUCCESS、制品安全检查 SUCCESS、Workers Builds SUCCESS、Cloudflare Pages SUCCESS。
- 正式域名真实访问通过：`/`、`/solutions/`、`/marketplace/brief/`、`/talent/portfolio/`、`/projects/`；`/prototypes/f21c/` 为预期 404。
- 真实数据库 staging：6表全部强制 RLS，4个私有函数仅服务角色可执行，`cms_editor/account_auth/v2_matchmaking` 均关闭，`editor_grants=0`、`content_items=0`；未调用任何成功写入路径。
- production：无 CMS schema，`account_auth=false`；未运行迁移或上线真实写入接口。
- **已验收范围：私有数据库事务结构、最小权限、关门时拒绝写入与公开站隔离。未验收范围：真实 JWT、角色委托、成功编辑/审核事务、并发 E2E、存储扫描与服务端 HTTP API。**
