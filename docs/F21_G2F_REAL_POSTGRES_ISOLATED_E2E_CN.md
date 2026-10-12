# 见势 F2.1 G2-F｜真实 PostgreSQL 隔离正向事务验收

日期：2026-10-12。目标：用**一次性 PostgreSQL 16 容器**验证原始迁移在真实数据库的功能，而非 Python 离线模拟。

## 隔离与执行

- `.github/workflows/cms-postgres-isolated.yml`：独立 GitHub Actions CI，只在相关私有 CMS SQL / 测试路径的 PR 或 main 推送时启动，不含任何 schedule、workflow_dispatch 或外部数据源请求。仅授予 `contents: read`。
- 每次启动 `postgres:16` 容器，使用固定、无商业意义的本地数据库 `jianshi_g2f`；所有语句通过 `docker exec` 和容器内部 Unix socket 执行。没有 Supabase URL/Token、远端数据库端口连接、收费浏览器。
- `scripts/qa/g2f_postgres_real_e2e.py` 实际加载仓库原始的五个 SQL 迁移：0037、0054、0055、0056、0057，不是重写一个简化版数据库逻辑。为脱离 Supabase 平台，额外创建**仅在容器中**的最小 `auth.users` / `auth.sessions` 合成表和 `anon/authenticated/service_role` 角色夹具。
- 先证明原始写入门禁处于关闭状态会拒绝；再仅在一次性容器中填充八项 Auth 测试布尔门禁、两项功能开关和五个合成用户的角色。真实 Staging、Production 开关保持关闭。
- 成功路径：CREATE→EDIT→将历史第一稿 RESTORE 为全新草稿→清除核验后不能直接审核→独立审核拒稿→返回草稿并重新声明事实/版权→复审→生成内部 STAGED 快照→撤回→再次送审、批准和发布。
- 失败路径：anon/authenticated 没有 schema/函数执行权限、使用 postgres 而不是 service_role 的可信调用被拒绝、非作者恢复、预期版本冲突、重复 request_id、自审、自发布、非法恢复、来源 URL 不安全。
- 并发：两条独立 psql 客户端针对同一修订写入，第一条事务持有行锁，预期仅一条成功，另一条得到 `CMS_STALE_REVISION`，不存在额外版本或丢失更新。
- 公开快照必须严格包含白名单字段，拒绝携带合成私有备注及合成财务声明。

## 明确不覆盖

- 真实 Supabase GoTrue 的邮件/JWT/session、PostgREST/RPC 可信边缘网关、生产 RLS/用户数据、浏览器 CMS 编辑授权和持久化 Cloudflare 发布投影。
- 容器内将测试门禁打开是为了验证真实 PostgreSQL 正向事务，**不是**账号或 CMS 的 Staging/Production 放行。容器角色、auth schema 是专门的合成夹具，不应冒充 Supabase Auth 原生行为。
- 免费 Actions 分钟与计费取决于用户账户和 GitHub 当前政策，本任务不购买任何套餐，也不承诺绝对零费用。
- P4.41 `event=schedule` 的 00:55、06:55、12:55、18:55 原四个 UTC 时段、当日 claim、HN≤7 / RSS≤1 / GitHub≤2 来源限额完全不改。

## 发布验收

本阶段 PASS 需要专属 PostgreSQL 集成工作流 SUCCESS，原有主 CI 不回归，公开静态构建不被修改。任何失败应定位为阻断，不能用之前的离线合成 PASS 代替真实数据库 E2E。
