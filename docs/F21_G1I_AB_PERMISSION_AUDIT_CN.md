# 见势 F2.1 G1-I｜A/B 默认拒绝权限实测（2026-10-12）

**本阶段先验收默认拒绝，不把双账号已经建立误认为互相隔离的完整正向业务 E2E。**

- Staging 已实际确认 12/12 个私有表 `RLS=true` 且 `FORCE RLS=true`（jianshi_v2 六表、jianshi_cms 六表）。
- `anon` 与 `authenticated` 对两个私有 schema 的 USAGE 权限均为 false；在这 12 个表上的普通角色 SELECT/INSERT 也均为 0；私有 schema policy 总数为 0，因此默认拒绝。
- `public.cms_internal_session_v01` / `public.cms_internal_write_v01` 两个内部 RPC：anon EXECUTE false、authenticated EXECUTE false、service_role EXECUTE true。
- 独立网络拒绝探针：匿名 HTTP POST `/rest/v1/rpc/cms_internal_session_v01` 请求，得到 **HTTP 401 permission denied**；探针编号 210。不包含 JWT、私有材料、有效用户 ID，使用全零 UUID。
- 三项 staging feature flags（account_auth, cms_editor, v2_matchmaking）全部 false；生产环境零变更。
- 用户 B Gmail 登录及 JWT 身份检查 PASS（实际浏览器截图）；**登录时刷新持久性、A/B 以各自 JWT 访问业务资源、CMS 私有角色正向写入和会话吊销重放仍 NOT_TESTED**，不可宣称 Auth 八项 Gate 或跨用户数据操作 E2E 完成。
- 新增 `scripts/security/f21_staging_ab_permission_audit.sql`：无私有记录/用户数据查询，仅输出结构、权限和开关聚合，结果只有 `PASS_DENY_BY_DEFAULT` 或 `FAIL_CLOSED_REVIEW_REQUIRED`。禁止在生产环境执行变更；本文件本身不写数据。
- 原 P4.41 四个 UTC 时槽、HN7/RSS1/GitHub2 限额保持；没有任何新增采集请求。

后续按阶段做 JWT 正向身份归属、真实 A/B 负向 IDOR、过期/注销 JWT、CMS 角色和版本锁；任何扩大权限操作必须独立验收与明确开闸审批。
