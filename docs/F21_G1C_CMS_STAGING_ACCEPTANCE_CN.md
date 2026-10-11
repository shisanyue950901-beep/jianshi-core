# JIANSHI 2.0｜F2.1 G1-C 私有 CMS 底座与内部编辑原型

**阶段日期：2026-10-11。状态：STAGING_DB PASS / PR_CI PASS / DEPLOY 待核 / UI 真人交互 NOT_TESTED。**

## 本轮真实实施边界

| 交付物 | 位置 | 状态/性质 |
|---|---|---|
| CMS 私有五表 | db/migrations/0054_jianshi_cms_private_foundation.sql | 仅 staging 可执行的受控 DDL，schema jianshi_cms |
| 编辑与审核预览 | web/prototypes/f21c/index.html | 离线交互预览，全部合成条目，不参与 web/dist 静态公开发布 |
| 自动化测试 | tests/test_f21_g1c_private_cms.py | 结构、默认拒绝、CMS 审核合同、私有原型不泄漏 |
| 源代码基线 | f21_content_contract.py / f21_review_workbench.py | 延续先前离线审核内核，不直接接入生产账号 |

## 数据结构五表

1. content_items：内容主键、类型、作者、当前版本、状态、审核人与发布时间。
2. content_revisions：每稿版本序号、作者、待发布正文 JSON 与来源证据。仅 service_role SELECT/INSERT，追加式版本记录，不向普通账号开放。
3. media_rights：私有素材键、版权持有人、许可依据、使用同意、扫描结果；不包含永久可公开 URL。
4. review_events：独立审核和内容生命周期事件，包含来源状态、动作、操作者、私有原因和请求幂等键；仅 service_role SELECT/INSERT。
5. publication_snapshots：经核验的白名单 JSON，**仅内部待发布制品**。该表绝非公共 Data API 或 CMS 自动上线接口。

整套 schema RLS/ FORCE RLS，拒绝 PUBLIC/anon/authenticated 的 schema、表、序列访问。没有用户 RLS policy、没有公开 API、没有 security definer 函数。普通角色无调用或枚举内部数据的权利。开关 cms_editor=false。角色的真正受控访问、内容与审计表的跨表事务性一致性仍须 staging API E2E。

## 当前前端是什么，不是什么

原型在 web/prototypes/f21c/index.html，只有三个合成示例（解决方案、学习课程大纲、工具目录），支持左侧导航、示例切换、编辑、本地预览和恢复，不通过网络保存。
明确不包含账号登录、管理员权限校验、真实审批按钮、素材上传、真实媒体链接、生产公开页面；仓库代码可供研发审查，但 Cloudflare web/dist 不包含该原型。

## G1-C 验收表（填写实际证据，不预先算成功）

- [x] PR #123 首轮全量 CI PASS
- [x] staging 五表实际创建，5/5 均 FORCE RLS
- [x] staging anon/authenticated 对 schema 与表均无权限；序列由 SQL REVOKE 严格约束，cms_editor=false。数据库审计零 policy
- [x] production CMS schema 仍不存在、cms_editor 标记不存在、account_auth=false
- [x] PR 回归测试验证 web/dist 中不存在 web/prototypes/f21c/
- [ ] main 静态构建与 Cloudflare SUCCESS，原站首页/项目/方案保持正常（合并后核验）
- [ ] 原型编辑及切换的独立浏览器交互核验（如受支持），报告明确是否完成

## 下一批 G1-D 必须完成

1. 独立后端用户授权 API：受信任身份验证、最小角色权限、同源/CSRF、限速、带版本锁的事务、严禁作者自审、审计与发布原子性。
2. 真正私有的 staging 素材对象存储，包含大小、类型、恶意文件扫描和许可记录；禁止将永久对象链接直接放公开网页。
3. 两作者/两审核员/两企业隔离测试，错误角色、过期会话、重复动作、并发、撤回和服务停机 FAIL_CLOSED。
4. 真实 CMS 管理页面使用 staging API，只有 Auth Gate 全过后才考虑可控上线；禁止把本地原型直接改名为“正式后台”。
5. Supabase 私有 schema 没有用户直连许可，production 不应用本阶段 DDL，除非另有专项发布授权。

**已有规范：** docs/F21_IMPLEMENTATION_INDEX_CN.md 为入口。采集 cron、来源上限、真实 schedule 验收口径严格不变。

## staging 实际 SQL 核验证据

迁移 API 返回 `success=true`（仅项目 jianshi-staging）。五表 `content_items`、`content_revisions`、`media_rights`、`review_events`、`publication_snapshots` 的 `relrowsecurity=true` 与 `relforcerowsecurity=true`，逐表检查 `anon_select=false`、`authenticated_select=false`、`authenticated_insert=false`。 schema USAGE 权限对 anon/authenticated 均为 false，`pg_policies` 中策略数为 0。

功能标记：staging `cms_editor=false`、`account_auth=false`、`v2_matchmaking=false`；production `jianshi_cms` 不存在、`cms_editor` 标记不存在、`account_auth=false`。两环境均未插入客户数据或试验商单。

**注意：**上述是结构和权限元数据检查，不等于使用真实 JWT 的两账户 API 渗透测试；生产真实管理员 CMS 功能尚未部署。
