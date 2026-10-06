# 见势 R5 部署状态｜2026-10-06

## 最终状态
R5_PUBLIC_API = PASS_DEPLOYED
R5_STATIC_WEB = BUILD_READY
CLOUDFLARE_PAGES = PENDING_ACCOUNT_HANDOFF

## Production API
- Supabase Edge Function: public-feed
- verify_jwt: false（公开只读接口）
- 核心数据库仍 private-by-default
- Service Role 仅在 Edge Function 服务端使用
- raw_items / jobs / audit / source policy 等私有数据不进入公开响应

## Production 数据
- 商业挂牌样本：174
- GitHub 趋势仓库：195
- 多源验证机会：1
- 单源观察：5

首个多源机会：
- 一人公司 SaaS
- GitHub evidence: 50
- Marketplace evidence: 6
- Total evidence: 56
- HEAT: 59.52
- CONTENT: 74.79
- BUILD: 69.19
- BUSINESS: 73.04

## 公开信息架构
首页：
- 见势品牌 / 定位
- 数据规模
- 已通过多源验证
- 单源观察池
- 技术侧信号

详情页：
- 四分模型
- 商业判断
- GitHub 技术证据
- Empire Flippers 商业证据
- 中国化适配
- 一人公司适配
- 风险/状态披露

## 质量修正
首次 Staging API 验收发现 GitHub 总榜会把 generic breakout 项目混入首页。
R5 增加 public_tech_signals_v01，只允许：
- ai_agents
- llm
- saas
三类发现查询进入公开“技术信号”。

内部 UUID、marketplace internal id、source API URL 均从公开响应移除。

## 前端成本策略
R5 不启动 Next.js 运行时。
采用 Python 静态生成：
- 构建时读取 public-feed
- 输出纯 HTML/CSS/JS
- Cloudflare Pages 静态托管
- 页面访问不查询数据库
- 目标前端运行成本 ¥0

未来真正需要登录、收藏、会员后，再升级动态应用层。

## 待办
只剩 Cloudflare Pages 的账户级连接/登录授权。
完成后设置：
- Repository: jianshi-core
- Build command: python web/build.py
- Output directory: web/dist
- Env: JIANSHI_API_URL=<production public-feed URL>
