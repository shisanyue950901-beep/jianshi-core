# 见势 F2.1 G2-E｜历史版本恢复与隔离操作台

日期：2026-10-12。范围：仅 Staging 的附加私有数据库合同和完全离线合成 UI，绝非正式 CMS 上线。

## 已编写

- 新迁移 db/migrations/0057_jianshi_cms_historical_draft_restore.sql：私有 SQL 函数 restore_draft_revision(actor,item,expected_revision,source_revision,request_id)，SECURITY INVOKER，仅 service_role 执行，且先经过现有 CMS+Auth 写入门禁。
- 仅允许拥有编辑权限的内容原作者，在 DRAFT 或 REJECTED 状态将历史修订复制为一个新的 DRAFT 版本。历史版本不覆盖；新版本 rights_declared=false、facts_checked=false，last_reviewer_id=null，published_at=null，记录 RESTORE 审计事件。之后必须重新编辑核验、独立审核才可再发布。
- 拒绝：未授权角色、非原作者、APPROVED/IN_REVIEW/PUBLISHED/UNPUBLISHED、预期版本冲突、源版本非法/缺失、重复请求、活跃 STAGED 快照。FOR UPDATE 锁与 CAS 防止竞态，失败则事务回滚。
- 更新 scripts/qa/f21_g2d_cms_offline_model.py：新增显式 restore_revision，原 restore_old_revision 不安全历史接口仍拒绝。模型成功不是 PostgreSQL 的真实正向事务。
- 新增 web/prototypes/f21g2e 作为本地合成操作台：合成版本、审核事件、模拟快照、拒绝提示，全部临时内存；没有真实账号、网络、后端、存储或服务密钥，且不复制进 web/dist。
- 测试 tests/test_f21_g2e_version_restore.py、tests/test_f21_g2e_safety.py、tests/f21_g2e_operator.test.cjs，覆盖追加式恢复、重置核验标志、CAS、幂等、所有者、未撤回快照、非法操作、移动端标记与公开产物隔离。

## 严格验收口径

| 证据等级 | 允许判定 | 明确不允许判定 |
|---|---|---|
| E1 CI 与模拟 | 合成流转和拒绝测试 PASS | 真实 Postgres 写入 PASS |
| E2 Staging DDL 权限 | 私有函数存在且权限最小化 | CMS 已开放 |
| E3 Staging 关闭门禁 | PostgreSQL 42501 / CMS_WRITE_DISABLED 拒绝 | 正向回滚成功 |
| E4 隔离数据库正向 E2E | 待独立审批及真正可回收沙盒 | 当前尚无 |
| E5 Production | 本批严禁 | 不得启动 |

生产 Supabase 不运行迁移，账号/CMS/撮合开关维持关闭；Staging 不创建真实角色或内容。P4.41 四个 UTC schedule 时段 00:55/06:55/12:55/18:55、日 claim、HN7/RSS1/GitHub2 上限均不改；push 构建不计入 schedule 采集。只检查结构权限与行数聚合，不读取私有正文、Artifact 或凭证。

真实正向 DB 事务、并发压力、可信授权前端、版权媒体扫描、正式站投影发布仍 NOT_TESTED / NOT_IMPLEMENTED。

## 本轮最终真实 Staging 核验

- PR #138 CI run 38241515654 = SUCCESS（Python + Node 真实离线行为模拟与原全量回归）；此结果不等于真实数据库正向 E2E。
- 通过 Supabase Staging 的迁移接口安装 0057 追加函数，迁移返回 success=true；只对 apuibjhxinumxbfnqlkp 生效。
- 只读 catalog：restore_draft_revision 存在，SECURITY DEFINER=false，anon EXECUTE=false，authenticated EXECUTE=false，service_role EXECUTE=true。
- Staging 负向调用恢复函数，PostgreSQL SQLSTATE 42501 / CMS_WRITE_DISABLED，证明真实数据库写入门禁没有被绕过。
- 迁移前后 Staging 的 content_items、content_revisions、review_events、editor_grants、publication_snapshots 均为 0；account_auth、cms_editor、v2_matchmaking 全为 false。
- 只读 Production：jianshi_cms schema 仍不存在，account_auth=false，未在生产执行 DDL。
- 严格验收结论：受控数据库函数部署/权限/负向拒绝 E2–E3 PASS。成功历史恢复、真实角色写入与浏览器后端 E2E 仍 NOT_TESTED，禁止误标 PASS。
