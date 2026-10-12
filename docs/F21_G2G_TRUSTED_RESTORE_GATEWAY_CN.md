# 见势 F2.1｜G2-G 第一批：可信 CMS 网关接通历史版本恢复

日期：2026-10-12。基线：G2-F 真实一次性 PostgreSQL E2E 已通过，但真实 Supabase Auth 和浏览器 CMS 正向业务尚未开闸。

## 本批实质交付

- `0058_jianshi_cms_restore_private_rpc.sql`：增加 `public.cms_internal_restore_v01(actor,payload)`。严格接受 `content_id/expected_revision/source_revision/request_id` 四个字段；先执行现有 Auth/CMS 门禁，随后调用 G2-E 私有 `restore_draft_revision`，不允许额外用户、角色或审批字段。
- 权限限制：SQL `SECURITY INVOKER`；撤销 PUBLIC/anon/authenticated EXECUTE，只有 `service_role` 可以调用。数据库原始内核依然保证作者归属、CAS、请求幂等、审计、恢复后重核版权/事实。
- `cms-staging-gateway/index.ts` 增加服务器内部 `POST /restore`，先走既有受平台验证 JWT → GoTrue `getUser` → session_id 与 `auth.sessions` 验证 → 8 项 Auth 门禁 → 服务端自动派生 actor → 专属私有 RESTORE RPC。
- 禁止浏览器直接向此网关发起跨域请求；`Origin` 拒绝、未设 CORS，生产 Supabase URL 无法通过 staging 锁。没有可信 BFF 之前不能把该路由当作已经向运营人员开放。
- G2-F 一次性 PostgreSQL 16 工作流扩展到加载原始 0058 迁移，并以 service_role 执行真实恢复 RPC、重复 request_id 和伪造角色字段拒绝，不再只通过模型测试验证恢复。
- 专项安全单元测试 `tests/test_f21_g2g_restore_gateway.py` 负责检查网关的严格白名单、身份/会话门禁、SQL 最小权限及隔离测试触发。

## 验收事实的层级

1. CI 静态与真实独立 PostgreSQL 测试通过：仅证明代码和数据库合同能在一次性隔离容器中执行。
2. Staging additive DDL 与 Edge v3（如果执行）：通过目录、权限和无凭证拒绝测试，继续 `cms_editor=false`、`account_auth=false`。
3. **未完成：真实浏览器登录会话 → 可信 BFF → CMS 正向写入 E2E**。现有 Edge 网关拒绝 Origin，不能因为部署成功就宣布编辑后台已打通。
4. 尚需 BFF 同源会话保护、CSRF、服务端速率限制、角色可撤销性、两用户隔离和全量审计。未满足前无生产发布。

## 项目隔离冻结

不改 Production 账号/CMS/企业撮合标记、不复制任何私有正文、session/JWT 或财务数据进入网页，不调用付费浏览器。P4.41 四个 UTC 原调度 `00:55/06:55/12:55/18:55`、每日 claim 和 HN7/RSS1/GitHub2 频次原样保留；任何 push CI 都不能计算为真实 schedule 采集。
