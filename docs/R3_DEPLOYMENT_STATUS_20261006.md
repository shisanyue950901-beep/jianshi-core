# 见势 R3 部署状态｜2026-10-06

## 最终状态
`R3_GITHUB_SIGNAL_ENGINE = PASS_DEPLOYED`

## Production
- Supabase: jianshi-prod / Tokyo
- GitHub source: GREEN
- Edge Function: collect-github-trends / ACTIVE
- Cron: jianshi-github-trends-6h / ACTIVE
- Schedule: 32 */6 * * *
- GitHub API auth: 暂不配置额外 Token，使用公开官方 REST API 的低请求量模式

## 首次真实采集
- Discovery Queries: 4
- API result rows: 200
- Unique repositories: 195
- Parser errors: 0
- New snapshots: 195
- GitHub API minimum remaining seen: 6
- Quality Gate: PASS

## 当前数据库
- GitHub repositories: 195
- GitHub snapshots: 195
- Discovery provenance links: 200
- GitHub Hot candidates: 195
- GitHub Rising candidates: 0（符合预期；首轮尚无 >=1 小时历史窗口）
- Marketplace listings: 174
- Active Cron jobs: 2

## Staging 验收
1. 首次真实采集：195 unique repositories / 195 snapshots / PASS
2. 立即重复：new_snapshots = 0，证明幂等
3. 发现微窗口问题：约 3 分钟的小 Star 增量会夸大日化速度
4. 修复：Recent Velocity 仅在 delta_hours >= 1 时启用
5. 合成 6 小时增长样本：+20 stars -> 80 stars/day，成功生成 GITHUB_FAST_GROWTH
6. 合成数据已全部清理

## 安全
- 新表全部 RLS enabled
- anon/authenticated 默认无核心表权限
- 所有公开视图改为 security_invoker=true
- Source Gate 继续 Fail-Closed
- pg_net linter warning 已审查：当前 Supabase build extrelocatable=false，无法安全迁移，接受平台级例外

## 重要产品约束
`github_hot_current` 是内部原始技术热度，不直接等于“商业机会榜”。

GitHub 星标可能受到社区结构、事件、营销甚至异常增长影响。
因此 R4 必须在公开排名前加入：
- 商业相关性
- 用户问题/需求证据
- 一人公司适配度
- 中国化机会
- 竞争强度
- 多源共振

只有通过 R4 Opportunity Gate 的条目，才允许进入“见势公开热榜/正在起势”。
