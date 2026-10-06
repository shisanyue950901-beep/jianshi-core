# 见势 R5｜公开网站与只读 API

## 核心原则
1. 公开网站绝不直接访问核心表。
2. 浏览器永远拿不到 Supabase service-role。
3. public-feed 只返回人工定义的公开投影。
4. OPPORTUNITY 与 WATCH 必须视觉和文案明确区分。
5. public_ready 继续由多源 Gate 决定，前端不能绕过。
6. P0 网站使用纯静态生成，目标运行成本接近 0。

## 页面
- 首页
- 多源验证机会
- 单源观察池
- GitHub 技术信号
- /opportunity/{slug}/ 详情页

## API
- ?view=home
- ?view=catalog
- ?view=detail&slug=...

## 部署
静态产物：web/dist
推荐：Cloudflare Pages

构建命令：
python web/build.py

构建环境：
JIANSHI_API_URL=https://<prod-ref>.supabase.co/functions/v1/public-feed

Cloudflare 只负责静态文件托管，不持有数据库管理员密钥。
