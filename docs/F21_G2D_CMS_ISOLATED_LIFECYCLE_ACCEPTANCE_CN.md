# 见势 F2.1 G2-D｜CMS 事务闭环的隔离模型验收

日期：2026-10-12。**安全原则：在实际 Staging 账号和 CMS 八项门禁未全部批准前，不临时开启真实编辑、审核或公开发布。**

## 交付内容

- `scripts/qa/f21_g2d_cms_offline_model.py`：只有 `SYNTHETIC_` 虚构角色/资料的内存版 CMS 事务合同模型，没有数据库连接、网络、真实邮箱、客户信息、文件写入或生产 API。默认门禁 CLOSED，只有测试显示指定的 `simulated_gates_ready=True` 才能走纯本地成功路径。测试模型状态采用原子副本成功后提交；被拒绝操作不改变已有版本、快照或事件。
- `tests/test_f21_g2d_cms_offline_model.py`：自动测试草稿创建与编辑、独立审核、发布白名单、撤回快照、再次送审发布、拒稿重新编辑、A/B 所有者越权、编辑者自审、作者自发布、版本 CAS、重复 request_id、非法跳转、来源/版权/媒体不合格及不合规 URL。
- 白名单投影仅含十一个指定的可公开字段，私有备注、内部审核字段不随快照输出。本模块不写入 `web/dist`，不从私有 Artifact 读取任何内容。
- 静态核对实际 SQL `0055/0056` 有相应门禁和 RPC 的关键合同条款，但**静态源代码比对不等于 PostgreSQL 事务已实际成功执行，也不是 SQL 与 Python 行为逐条件形式等价**。

## 本轮真实 Staging 只读与拒绝验收

1. 私有 `jianshi_cms` 六张表均启用 RLS + FORCE RLS。
2. `content_items` / `content_revisions` / `review_events` / `publication_snapshots` / `editor_grants` 五类记录以及其他 CMS 私有表：合计实际记录 **0**；没有生成真实测试用户、角色或业务内容。
3. `account_auth`、`cms_editor`、`v2_matchmaking` 全部 `false`，两个数据接口无普通角色执行权限。
4. 直接在 Staging 对 `jianshi_cms.ensure_write_gate` 与服务 RPC `public.cms_internal_write_v01` 发起两次**不会成功写入**的门禁探针，均被 PostgreSQL 以 `SQLSTATE 42501 / CMS_WRITE_DISABLED` 拒绝。这证明**关闭门禁下拒绝**，不证明开启后正向业务可用。
5. 所有数据聚合仅检查数量、RLS 与门禁状态，不读取真实私有文稿、财务/来源原文或凭证；不修改 Production。

## 状态矩阵

| 验收项 | 状态 |
|---|---|
| 独立 Python 合成全生命周期 | 待 CI（纯模拟） |
| 版本号、幂等请求、跨角色与证据失败回归 | 待 CI（纯模拟） |
| 实际 Staging 门禁关闭与默认拒绝 | PASS（真实 SQL） |
| 真实数据库成功 CREATE / EDIT / APPROVE / PUBLISH | **NOT_TESTED — 禁止为了测试打开门禁** |
| JWT 登录后进入真实 CMS API 的正向 E2E | **NOT_TESTED** |
| 真实并发冲突 / 崩溃后数据库恢复 | **NOT_TESTED** |
| 内部 STAGED 快照到 Cloudflare 公开站的发布流水线 | **NOT_IMPLEMENTED** |
| 真实旧内容版本回滚（选择过去修订版） | **NOT_IMPLEMENTED**：0055 只有 `REJECTED→DRAFT` 和 `PUBLISHED→UNPUBLISHED`，不支持选择旧版本内容；离线模型显式拒绝。不能以撤回发布等同版本回滚。 |
| 审核/版权/来源逐篇人工终审 | **NOT_TESTED** |

## 下一阶段必须做的工作

独立 Staging 环境下设计非生产授权的可回滚隔离事务夹具，并明确可以证明全部回滚的机制；审批生效前不开放真实角色授权和 API 开关。开发 `restore_old_revision` 之前先冻结「谁可以恢复、恢复时生成新修订版、是否必须重新审核及源证据更新」合同；任何历史版本不得直接覆盖已审核的当前版本。

**绝不改动** GitHub 原 P4.41 每日四个 UTC schedule 时段 00:55、06:55、12:55、18:55、claim、HN≤7/RSS≤1/GitHub≤2 次数。任何 push CI 或公开静态构建 SUCCESS 均不等同研究来源采集。
