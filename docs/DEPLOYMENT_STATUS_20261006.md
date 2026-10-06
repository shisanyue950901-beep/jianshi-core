# 见势部署状态｜2026-10-06

## 云环境
- Supabase Free / Tokyo (ap-northeast-1)
- jianshi-staging：ACTIVE_HEALTHY
- jianshi-prod：ACTIVE_HEALTHY
- 固定成本：¥0/月（当前免费额度内）

## 数据库
已应用 migrations：
- 0001_core
- 0002_marketplace
- 0003_seed_sources
- 0004_security_hardening
- 0005_advisor_hardening
- 0006_collector_runtime
- 0007_canonical_history_view

## 数据源
- Empire Flippers：GREEN / 官方 API / 自动采集
- Acquire：RED / 禁止自动采集
- Flippa：RED / 禁止自动采集
- Microns：RED / 禁止自动采集
- SideProjectors：YELLOW / 待审

## Collector
- Supabase Edge Function：collect-empire-flippers
- JWT 校验：开启
- 生产 Cron：jianshi-empire-flippers-6h
- Schedule：17 */6 * * *
- 官方 API 速率限制：<= 1 request/sec
- 最大单次页数：10

## 验收
Staging：
- 首次真实调用：2 页 / 40 条 / parser error 0 / 新 snapshot 40
- 重复调用：2 页 / 40 条 / 新 snapshot 0
- 证明 snapshot 去重有效

Production：
- 首次完整真实调用：9 页 / 174 条 / parser error 0
- 当前 marketplace listings：174
- canonical history：以 source_updated_at 去重
- Quality Gate：PASS

## 安全
- 核心表 RLS 已开启
- anon/authenticated 默认无核心表权限
- Vault 保存定时调用信息
- RED/YELLOW source 自动采集 Fail-Closed
- service role 不暴露给浏览器

## 运行策略
真实采集由 Supabase Cron + Edge Function 承担。
GitHub Actions 只用于 CI，不承担生产采集，以降低成本和减少生产密钥面。
