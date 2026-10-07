# 见势 R8.8｜机会级技术加速度

## 目标
“正在起势”不能只解释成一个静态热度分。
见势已经每 6 小时保存 GitHub 快照，因此直接复用真实历史差分。

## 数据来源
只使用现有 GREEN GitHub 官方 API 数据：
- latest snapshot
- previous snapshot
- delta_stars
- delta_hours
- recent_stars_per_day
- recent_velocity_score

github_rising_current 的有效窗口：
- 有 previous snapshot
- delta_hours >= 1
- delta_hours <= 48
- delta_stars > 0

## 机会级聚合
opportunity_github_acceleration_v01：
- rising_repo_count
- recent_stars_per_day_sum
- recent_stars_per_day_avg
- avg_recent_velocity_score
- max_recent_velocity_score
- avg_observation_window_hours

## 排序
R8.8 不改 OPP_V0.2 四个核心分数。

正在起势排序仍优先：
1. NEWLY_VALIDATED
2. EVIDENCE_ACCELERATING
3. RISING
4. 其他

同等真实日变化下，再使用：
- rising_repo_count
- max_recent_velocity_score
- heat_score

作为 tie-breaker。

## 对外解释
榜单可以显示：
“3 个技术项目近期仍在增星 · 合计约 120 星/天”

详情页显示：
- 当前加速技术项目数
- 合计星标/天
- 平均加速度分
- 平均观察窗口

固定说明：
“这组数据来自见势连续 GitHub 快照，只用于解释技术侧是否还在加速，不替代真实商业证据。”

## 不做
- 不把 GitHub 增星当收入
- 不把技术加速升级为商业验证
- 不增加 source_count
- 不改变 BUSINESS_SCORE
- 不改变 TECH_PLUS_COMMERCIAL Gate
