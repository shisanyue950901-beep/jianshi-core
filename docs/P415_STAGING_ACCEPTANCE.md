# P4.1.5 PyPI 候选质量优化 — Staging Acceptance

日期：2026-10-07

## 结论

```
P415_CI = PASS_RUN_151
P415_STAGING_COLLECTOR = PASS
P415_QUALITY_FILTER = PASS
P415_CANDIDATE_RULE = P415_V1
P415_CURRENT_CANDIDATES = 12
P415_HIGH = 5
P415_MEDIUM = 7
P415_EXACT_GITHUB_OVERLAP = 0
P415_INCREMENTAL_DISCOVERY = HIGH
P415_PRODUCTION_SHADOW_READINESS = PASS
P415_BIGQUERY = RECOMMENDED_LATER
P415_COMMERCIAL_PROOF = NONE
P415_SCORING_IMPACT = NONE
P415_PRODUCTION_CHANGE = FALSE
P415_FINAL = PASS_STAGING
```

## 最终 Staging 实测

P415_V1：

- RSS items = 80
- unique discovered = 76
- accepted packages = 60
- metadata success rate = 100%
- candidate count = 12
- candidate match rate = 20%
- HIGH = 5
- MEDIUM = 7
- LOW = 48
- exact GitHub overlap = 0
- GitHub-linked projects not in current corpus = 40
- candidate GitHub-linked projects not in current corpus = 9
- candidate with non-GitHub project URL = 7
- package content stored = false
- deprecated JSON downloads used = false
- BigQuery used = false
- scoring changed = false

## 质量规则

旧规则只要 category 命中就进入候选。

P415_V1 改为质量分：
- 业务扩展类别 +3
- 独立非 GitHub/PyPI URL +2
- AI-only +1
- DevTools-only +1
- Beta +1
- Production/Stable/Mature +2
- keyword count >= 3 +1

score >= 4 才进入候选。

优先级：
- HIGH >= 6
- MEDIUM = 4–5
- LOW < 4

## GitHub 互证

PyPI 中“存在 GitHub URL”不再被视为重复。

必须规范化 owner/repo，并与 github_repositories.full_name 精确匹配。

当前样本：
- exact overlap = 0
- 因此当前候选属于 TECHNICAL_DISCOVERY，而不是已有 GitHub 项目的重复。

## 当前候选 View

`pypi_candidate_shadow_v01`

仅包含：
- candidate_rule_version = P415_V1
- candidate_match = true

当前：
- HIGH = 5，其中 5 个有独立非 GitHub URL
- MEDIUM = 7，其中 2 个有独立非 GitHub URL
- exact GitHub overlap = 0

旧实验候选不会进入当前 View。

## BigQuery

结论：
`RECOMMENDED_SEPARATE_EXPERIMENT`

PyPI RSS + JSON 已经证明其项目发现价值。
BigQuery download trend 的作用是增加 adoption signal，用于判断“只是发布”还是“持续被采用”。

BigQuery 不是 Production Shadow 的前置条件。

P4.1.5 没有创建 Google Cloud Project、没有配置凭据、没有产生 BigQuery 查询。

## Production

已确认 Production：
- pypi source = 0
- pypi query = 0
- pypi cron = false

因此本阶段没有修改 Production。

PR #49 保持 OPEN，不在 P4.1.5 合并。

下一小步如果授权：
P4.1.6 只把现有 PyPI shadow 合同推 Production，不改 OPP_V0.2 / public_ready，不同时引入 BigQuery。
