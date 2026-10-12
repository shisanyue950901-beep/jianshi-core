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

## 2026-10-12 后续自动验收补充

- SQL 审计已在 Staging 实际执行并得到 `PASS_DENY_BY_DEFAULT`：schema_count=2、total_private_tables=12、force_rls_tables=12、untrusted_table_grants=0、private_policy_count=0、schema_usage_closed=true、internal_rpc_count=2、internal_rpc_closed=true、closed_feature_count=3、features_closed=true。
- 浏览器 Staging 预览页增加「一键安全自测（只读）」：仅在 A/B 成功登录后显示，点击执行使用当前 JWT 的私有组织只读请求和 CMS 内部 RPC 全零 UUID 拒绝探针；不写入业务数据，也不读取响应正文。只根据 401/403/404/406 判定“默认拒绝”，其他状态 FAIL/未知，网络/CORS 错误一律 NOT_TESTED。
- 真实 Cloudflare 预览 HTTP 检查：HTML id=211 返回 200 text/html，包含新按钮；JS id=212 返回 200 application/javascript，包含受限接口安全自测代码。
- 静态与单元测试 CI run 38230700715 SUCCESS。这仍不是**已登录 JWT 的实际授权拒绝**，需要账号 B 在浏览器内点击一次按钮才可认定相应两项 HTTP 拒绝 PASS。
- 即使按钮两项通过，也不等于完整 A/B 跨账号 IDOR：目前私有表和后台默认完全关闭，开放业务 API 后仍必须重新执行完整角色×资源×操作测试。
