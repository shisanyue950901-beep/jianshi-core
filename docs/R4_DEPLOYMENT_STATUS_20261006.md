# 见势 R4 部署状态｜2026-10-06

## 最终状态
R4_OPPORTUNITY_ENGINE_V01 = PASS_DEPLOYED

## Production 数据
- active evidence: 312
- first score snapshots inserted: 24
- second refresh inserted: 0
- opportunity families: 6
- active cron jobs: 3

## Production 排名
1. 轻量电商品牌与 Amazon 资产
   - HEAT 100.00
   - CONTENT 90.20
   - BUILD 47.25
   - BUSINESS 71.22
   - SINGLE_SOURCE / public_ready=false

2. 创作者媒体资产
   - HEAT 89.69
   - CONTENT 91.16
   - BUILD 58.67
   - BUSINESS 76.81
   - SINGLE_SOURCE / public_ready=false

3. LLM 应用与工具
   - HEAT 87.07
   - CONTENT 89.98
   - BUILD 61.87
   - BUSINESS 40.47
   - SINGLE_SOURCE / public_ready=false

4. AI Agent 工具与自动化
   - HEAT 84.97
   - CONTENT 90.44
   - BUILD 61.24
   - BUSINESS 39.74
   - SINGLE_SOURCE / public_ready=false

5. 联盟营销与内容资产
   - HEAT 72.06
   - CONTENT 77.13
   - BUILD 49.01
   - BUSINESS 78.86
   - SINGLE_SOURCE / public_ready=false

6. 一人公司 SaaS
   - HEAT 59.52
   - CONTENT 74.79
   - BUILD 69.19
   - BUSINESS 73.04
   - MULTI_SOURCE / public_ready=true

## 解释
HEAT 高不等于可公开推荐。
电商、Creator、Affiliate 当前商业证据很强，但只有 Empire Flippers 单一来源，因此 Gate 不放行。
AI Agent / LLM 当前 GitHub 技术信号很强，但缺少第二种商业证据，因此 BUSINESS 分受到惩罚。
Solo SaaS 同时有 GitHub + Marketplace，因此成为首个真正双源共振机会。

## 自动运行顺序
- 00/06/12/18:17 Empire Flippers
- 00/06/12/18:32 GitHub Trends
- 00/06/12/18:45 Opportunity Engine

三段流水线互相错开，避免读到半更新状态。

## 安全与验收
- Staging first: PASS
- Production idempotency: PASS
- score snapshot duplicate suppression: PASS
- Security Advisor: no ERROR
- RLS private-by-default remains intentional
- pg_net schema warning accepted because extrelocatable=false
- AI API cost: 0

## 下一步
R5 应建立公开网站只读投影：
- 今日热榜
- 正在起势
- 机会详情
- 证据来源
- 四分模型
- public_ready Gate
公开站绝不直接读取 raw/private tables。
