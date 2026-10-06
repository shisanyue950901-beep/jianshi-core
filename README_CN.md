# 见势 JIANSHI｜P0 R1+R2 云地基与首个真实商业数据源

本仓库承接 `JIANSHI_P0_R0_DATA_FOUNDATION`，目标是把“免费优先”的数据地基变成可直接部署的工程，并完成 Empire Flippers 官方 Marketplace API 的真实字段适配。

## 当前状态
- 数据源许可 GREEN/YELLOW/RED Gate
- PostgreSQL/Supabase migrations
- Empire Flippers 官方 API 采集器
- 历史 snapshot + pipeline_run + quality gate
- GitHub Actions 定时任务模板
- pg_dump + gzip + SHA256 备份脚本
- 真实 API fixture 与单元测试

## 成本纪律
`FREE_FIRST`：P0 固定基础设施目标 ¥0/月；禁止自动升级付费方案。
