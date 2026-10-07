# P4.1.5 PyPI 候选质量优化

日期：2026-10-07
状态：STAGING_REFINEMENT

## 目标

在不推 Production 的前提下，解决 P4.1.4 暴露的三个问题：

1. 降低 DEVTOOLS / AI 的宽松关键词误命中；
2. 把“带 GitHub URL”与“已存在于见势 GitHub 语料库”严格区分；
3. 判断 PyPI BigQuery 下载趋势是否值得作为后续 adoption signal。

## 新候选质量规则

不再使用：

`candidate_match = category_count > 0`

改为质量分：

- 命中业务扩展类别（Automation / Data / SaaS / Ecommerce / Creator / Marketing）：+3
- 存在非 GitHub / 非 PyPI 独立项目地址：+2
- 仅 AI 类：+1
- 仅 DevTools 类：+1
- Beta：+1
- Production/Stable 或 Mature：+2
- keyword count >= 3：+1

`score >= 4` 才进入 candidate。

Priority：

- HIGH >= 6
- MEDIUM = 4–5
- LOW < 4

这样纯 AI / DevTools 不会只因为关键词出现就自动进入候选。

## GitHub 互证语义

PyPI project_urls 中存在 GitHub URL，不等于“与当前 GitHub 采集重复”。

必须将 GitHub URL 规范化为：

`owner/repo`

再与 `github_repositories.full_name` 精确比较。

语义：

- exact overlap = TRUE
  - cross_source_role = TECHNICAL_ECOSYSTEM_CONFIRMATION
  - PyPI 作为已有 GitHub 项目的生态发布互证
- exact overlap = FALSE
  - cross_source_role = TECHNICAL_DISCOVERY
  - PyPI 发现了当前 GitHub query corpus 尚未覆盖的新技术项目

无论哪种情况，P4.1.5 都仍为 shadow-only。

## BigQuery 决策规则

BigQuery download trend 的价值不在“再发现一个 package”，而在区分：

- 只是刚发布；
- 有持续下载采用；
- 下载趋势正在加速。

如果精炼后的 PyPI candidate 仍能稳定产生新的非重复项目，则 BigQuery 值得作为后续 adoption signal 实验。

如果 candidate 本身质量不足，则不引入 BigQuery，避免给低质量候选增加复杂度。

本阶段不创建 Google Cloud 资源、不请求用户绑定信用卡、不执行 BigQuery 查询。


## Staging 最终实测

P415_V1 最终运行：

- RSS items = 80
- unique discovered = 76
- accepted packages = 60
- metadata success rate = 100%
- candidate count = 12
- candidate match rate = 20%
- HIGH = 5
- MEDIUM = 7
- LOW = 48
- exact GitHub overlap with current JianShi corpus = 0
- GitHub-linked projects not in current corpus = 40
- candidate GitHub-linked projects not in current corpus = 9
- candidate with non-GitHub project URL = 7
- package content stored = false
- BigQuery used = false
- scoring changed = false

当前版本化候选 View：

`pypi_candidate_shadow_v01`

只认：

`candidate_rule_version = P415_V1`

因此旧实验规则产生的 candidate_match 不会混入当前候选集。

当前 View：

- HIGH = 5，其中独立非 GitHub URL = 5
- MEDIUM = 7，其中独立非 GitHub URL = 2
- exact GitHub overlap = 0

## GitHub 重合结论修正

P4.1.4 中“候选大量带 GitHub URL”不能解释为“与现有 GitHub 数据重复”。

P4.1.5 采用 owner/repo 精确匹配后确认：

- 当前样本中带 GitHub URL 的 package 很多；
- 但与 JianShi 当前 github_repositories 精确重合 = 0；
- PyPI 实际在补充 GitHub Query 当前没有覆盖的新项目。

因此：

```
PYPI_GITHUB_URL_PRESENCE != CURRENT_CORPUS_DUPLICATION
```

## BigQuery 决策

结论：

`PYPI_BIGQUERY_ADOPTION_SIGNAL = RECOMMENDED_SEPARATE_EXPERIMENT`

原因：
- RSS + JSON 已经证明 PyPI 能发现新的技术项目；
- 当前欠缺的是“是否真的有人持续采用”，不是“还能不能发现项目”；
- PyPI 官方 BigQuery file_downloads 可以提供真实下载采用信号；
- 下载趋势适合用于区分“刚发布”与“持续被采用/增长”；
- 它仍然只能是 technical adoption，不是商业收入证明。

BigQuery 不作为 Production Shadow 前置条件。

本阶段不创建 Google Cloud Project、不配置凭据、不产生查询费用。

## P4.1.5 最终冻结

```
P415_TECHNICAL_GATE = PASS
P415_QUALITY_FILTER = PASS
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
```

下一阶段如果获准，只做 P4.1.6：将 PyPI 按当前 shadow-only 合同推 Production，不改变 OPP_V0.2 / public_ready，不同时引入 BigQuery。
