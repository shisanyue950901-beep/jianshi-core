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
