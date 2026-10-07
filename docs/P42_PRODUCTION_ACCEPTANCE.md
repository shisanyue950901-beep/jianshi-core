# P4.2 前台机会产品化 — Production Public Acceptance

日期：2026-10-07

## 结论

```
P42_PR = PASS_MERGED_43
P42_CI = PASS
P42_MAIN = PASS
P42_STATIC_WORKFLOW_FIX = PASS_MERGED_45
P42_STATIC_SNAPSHOT_RUN = PASS_RUN_47
P42_STATIC_SNAPSHOT_COMMIT = fd55f532c9ceb1685c12acd3408145d0f6d317b8
P42_PUBLIC_HOME = PASS
P42_PUBLIC_OPPORTUNITIES = PASS
P42_PUBLIC_DETAIL = PASS
P42_FINAL = PASS_PRODUCTION_PUBLIC
```

## 公网站验收

站点：
https://jianshi-bua.pages.dev/

### 首页

已确认公开首页显示：

- 商业机会发现与决策平台
- 发现下一个值得做的项目
- 面向中国个人创业者的项目机会、四维评分和行动判断
- 已验证机会 / 待验证方向
- 今日推荐 / 正在起势 / 内容选题
- 原始技术项目降级为“证据库一角”

首页不再以“海外资讯/开源项目列表”为产品主叙事。

### 机会库

路由：

`/opportunities/`

已确认返回 200，并显示：

- 当前方向数量
- 已验证 / 待验证数量
- 值得深入研究 / 值得验证等决策标签
- 四维评分
- 搜索与筛选前端契约

首次公开验收时：
- 当前方向 = 6
- 已验证 = 4
- 待验证 = 2

这些数字会随真实数据变化，不作为永久冻结值。

### Opportunity 详情

样板：

`/opportunity/solo-saas/`

已确认新版详情公开可访问，并包含：

- 决策结论
- 机会/目标用户/商业模式说明
- 真实商业样本
- asking price / Sold 语义披露
- 中国化适配 / 一人公司适配
- MVP 难度 / 资金强度 / 获客难度的“尚未完成编辑审查”状态
- 内容机会
- 技术供给证据
- GitHub 技术加速度

未知信息仍明确显示未知，没有为完整性编造成本、周期或收入。

## 发布链修复

P4.2 初次合并后，静态构建本身成功，但 `.github/workflows/publish-static.yml` 仍用旧 Hero 文案做 grep 验收，导致 Verify public artifact 失败。

PR #45 已修复：

- 静态验收改为 P4.2 新 Hero
- 新增 `opportunities/index.html` 验收
- 新增详情层级验收
- `opportunities/**` 加入 snapshot paths-ignore
- `opportunities` 加入 snapshot git add

修复后 Static Snapshot run #47 全步骤 PASS，并生成新静态快照 commit。

## 未改变

- OPP_V0.2 = UNCHANGED
- public_ready Gate = UNCHANGED
- Source Policy = FAIL_CLOSED
- account_auth = FALSE
- Newsletter launch = CLOSED
- Marketplace = DEFERRED

## 下一阶段

`P4.3 = USER_BEHAVIOR_ANALYTICS`

目的：在真实引流前建立可验证的用户漏斗，而不是用注册数或页面访问量代替 PMF。
