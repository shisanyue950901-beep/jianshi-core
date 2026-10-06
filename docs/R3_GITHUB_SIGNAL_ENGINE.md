# 见势 R3｜GitHub 趋势信号引擎

## 目标
把“交易市场发生了什么”扩展到“开发者和开源生态正在做什么”。

## 发现面
当前 4 个低请求量查询：
1. 最近 90 天新仓库突破候选
2. AI Agent
3. LLM
4. SaaS

每轮最多约 200 个候选，跨查询按 GitHub repository ID 去重。

## 历史数据
`github_repositories` 保存当前标准化状态。
`github_repository_snapshots` 只追加变化历史。

## Heat Score v0.1
静态分：
- Popularity 25%
- Lifetime Star Velocity 35%
- Push Freshness 20%
- Repository Recency 10%
- Fork Signal 10%

有至少两个历史快照后：
- Static Heat 55%
- Recent Star Velocity 45%

因此第一天也能排名；运行一段时间后会自动从“当前热度”过渡到“真实增长速度”。

## Signal
满足以下条件才生成 `GITHUB_FAST_GROWTH`：
- 有前一历史快照
- 观测间隔 0.05–48 小时
- Star 增量 >= max(10, 前值的 0.5%)

## 成本
默认不配置额外 GitHub Token，Edge Function 使用公开官方 REST API，小请求量运行。
如果未来候选范围扩大，再单独配置低权限 GitHub Token 提升 API 配额。
