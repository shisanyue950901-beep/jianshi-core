# P4.29｜Acquire.com 与同类商业数据源扩展（2026-10-09）

## 使用边界（基于平台官方条款）
Acquire.com 买卖双方条款 https://acquire.com/buyerseller/ 第3.1节明确禁止未经书面许可利用自动或人工方式提取挂牌、资料、广告信息，自动查询及公开转载。通用条款 https://acquire.com/terms/ 亦限制机器人爬取。所以不使用爬虫、第三方搜索绕取挂牌、登录绕过、NDA绕过；没有书面授权不得同步 app.acquire.com/public/ 信息。
Flippa 服务条款 https://flippa.com/terms-of-service/ 限制未经书面许可复制、提取、重复利用挂牌、价格、数据汇编，或使用机器人批量提取。所以仅登记官网及有原作者链接的研究背景，不复制其挂牌数据库。
Microns.io 对微型商业项目相关，自动采集及转载许可尚未确认，因此保持关闭。
Indie Hackers 的 Founder Reports 可作为研究线索，但第三方 RSS 不视为官方许可接口；不自动抓取受限制原文。
Hacker News / Algolia 继续沿用公开搜索 API，只保存讨论和URL元数据，最多 6 家候选加 1 个主题，单请求4秒、128KiB，且绝不直接发布项目。
SEC EDGAR 的公司报告可用于具名公司历史监管依据，正式自动查询仍需满足其访问政策；本轮未启用新增查询。

## 本轮新增
1. config/p429_market_source_registry.json 维护6个信息来源、用途、具体使用限制、许可状态和4篇官方公开研究/创始人案例的链接与原创中文摘要。
2. scripts/release/p429_build_source_atlas.py 构建来源透明页面 /sources/ 。该页面只是来源说明和对官方公开文章的有限原创解释，未自动读取任何 Acquire/Flippa 的挂牌记录，亦未生成未验证正式项目。
3. 正式首页有「商业市场数据从哪来」入口，来源页列出信息来源接入状态和「推荐项目」严格证据门槛。
4. 现有 p426_daily_leads.py 在同样7次公共搜索请求上限内轮换 Show HN revenue、bootstrapped founder revenue、micro SaaS paying customers、solo founder business 等主题；不直接或绕道采集受限制平台记录。

## 首批研究资料
- Acquire.com 2025 成交倍数研究：https://blog.acquire.com/acquire-com-biannual-acquisition-multiples-report-jan-2026/ 。行业盈利质量背景，不能当成某个匿名公司已审计。
- Acquire.com 单人创办并出售 Helploom 的采访：https://blog.acquire.com/bootstrapped-profitable-and-acquired-in-four-days/ 。具名创业者访谈，不等于企业财报。
- Acquire.com 无外部融资创办并出售项目的访谈：https://blog.acquire.com/how-to-sell-a-bootstrapped-saas-startup-without-vc/ 。启发单人创业研究，不能照搬推算收入。
- Flippa 2026 H1 交易研究：https://flippa.com/blog/digital-ma-insights-h1-2026/ 。汇总交易研究，不将行业倍数当个人启动收益。

## 取得商业平台书面授权后才能正式扩充挂牌数据
需要平台明确许可自动获取、内部保存、用户端展示及更新的具体字段、保留时长、速率和再分发条款。其后优先使用经授权 API / 数据导出，不反向工程网页私有端点。先进入隔离研究队列、记录数据归属、币种单位、报告期、卖家自报与平台核验差别。身份不明时不把匿名挂牌财务转给具名企业。原始数据缺失或来源冲突始终 FAIL_CLOSED。

## 验收/成本
新增来源页面不改变正式 L3/L4 三家、内部待验证17家的准入门槛。不可擅自启用 TinyFish、付费浏览器、商业数据库订阅或额外高频任务；不得修改 Supabase Production、Cloudflare 付费设置和历史 PR #52。现有私有 GitHub Actions 免费额度未知，仍可能消耗配额。GitHub CI/发布产物不代表 CDN Safari 真机验收。
必须检查6源注册/4篇官方文章、禁止受限挂牌批量导出、可访问来源URL、8条 sitemap、原3家正式档案、8张 WebP/动效和所有公开源安全扫描。