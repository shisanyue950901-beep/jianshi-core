# P4.32｜内部商业证据：合法多源采集试点

**日期**：2026-10-09。**边界**：对内研究，不对外发布；不商用不自动免除平台访问条款。未取得许可的内容不通过变更抓取身份、搜索镜像、付费浏览器、登录数据或隐藏 API 绕过。

## 一、来源矩阵

配置 `config/p432_source_access_matrix.json`，9 类来源按实际权限明确分组：

| 数据源 | 自动访问 | 输出类型 |
|---|---|---|
| Fathom 官方 RSS `https://usefathom.com/blog/feed.xml` | **单次按需**，官方博客明确邀请订阅 RSS | 标题、日期、单篇官方链接，不保存正文，不验证收入 |
| Hacker News Algolia | **复用 P4.26** 每日 6 公司 + 1 主题，不新增请求 | 公开索引元数据，不当作财务 |
| SEC EDGAR | **复用 P4.31**，最多 2 官方请求且要求真实联系邮箱 | 结构化财务候选，仍需公司主体复核 |
| Plausible 官方公开文章 | **编辑性核实链接**，不批量网页抓取 | 具名公司历史自述 |
| Buffer Open 透明度面板 | **编辑性核实链接**，未授予批量采集许可 | 有时点的动态自报数据，需另核月度期间 |
| Acquire / Flippa / Microns 挂牌 | **禁止自动抓取**（需许可） | 不落地 |
| Indie Hackers 网页内容 | **禁止抓取**（条款禁止爬取） | 不落地 |

关键原文：
- SEC: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Fathom RSS: https://usefathom.com/blog
- HN API: https://hn.algolia.com/api/
- Acquire: https://acquire.com/buyerseller/
- Microns: https://www.microns.io/terms
- Indie Hackers: https://www.indiehackers.com/terms
- Flippa: https://flippa.com/terms-of-service/

## 二、可运行代码与安全机制

新增 `scripts/research/p432_publisher_rss_probe.py`，仅白名单 Fathom 官网官方 RSS：

- 明确 `--online` 才发起 **最多一次 HTTP GET**，不接任何外部参数 URL、不给其跟随重定向、拒绝异常媒体类型和状态；
- 每次最大 **256 KiB**、6 秒超时、取最多 **10 条**元数据，重复 URL 去重，仅接受 `https://usefathom.com/blog/<slug>`；
- XML 拒绝 DTD、ENTITY；只提取单篇标题/URL/发布时间，**不存文章描述、正文、作者联系方式**；
- 输出里包含来源摘要 SHA-256，报告必须写到仓库以外的私有路径；从不访问 Github/Cloudflare/Supabase 生产接口；
- `--fixture` 严格标记 `OFFLINE_FIXTURE_NOT_LIVE`；在线成功则标记 `LIVE_RSS_HTTP`；任何一条均未证明经营业绩或 L3/L4；
- 不自动调度；不改已有每日 7 次 HN 预算，也不新增 GitHub Actions 定时任务、远程浏览器和付费 API。

在具有网络连接的 Windows 电脑手工运行：

```powershell
python scripts/research/p432_publisher_rss_probe.py --online --output "C:\JianShiPrivate\p432_fathom_rss.json"
```

输出目录应与仓库和 Cloudflare 发布根目录隔离。不应长期采集文章全文或将原文镜像到项目仓库。

**本轮运行环境网络访问限制**：容器内对 `hn.algolia.com`、`data.sec.gov`、`usefathom.com` 均 DNS 解析失败，因此这次**未产生 LIVE_RSS_HTTP 和真实 SEC HTTP 响应**。Github CI 成功只能证明代码/离线负面测试成功，不能冒充真实联网抓取。

## 三、已实际核对的公开一手资料样本

`config/p432_private_editorial_observations.json` 新增 4 条**网页人工检索核对后的简要结构化观察**（非 RSS 自动获取），来源仍仅在私有仓库：

1. **Plausible**，2026-05-12 官方披露：2026 年 1 月试用 2,423、4 月 4,464，增长约 84%；2/3/4 月新增付费订阅人数分别 652/953/1,156。该站自己承认没有进行严格 A/B 测试，不能归因“改版必然增加 84%”。来源：https://plausible.io/blog/homepage-edits-conversion-lift
2. **Buffer** 官方动态透明度仪表盘（未指定本轮同一可核报告期），检索显示约 26.79m USD ARR、2.23m USD MRR、81,976 客户；这些值是历史时点的界面观察，不是稳定最新数据，更不是审计利润。来源：https://buffer.com/metrics
3. **Fathom**，2026-04-20 官方披露收购 Gauges，**不显示成交金额或净利润**。来源：https://usefathom.com/blog/fathom-acquires-gauges
4. **Fathom**，2026-04-05 官方说明 V4 更新，只证明产品运营/研发背景，不作为收入证据。来源：https://usefathom.com/blog/announcing-fathom-v4

元数据文件明确：
- `retrieval_method=PUBLIC_PUBLISHER_PAGES_REVIEWED_VIA_WEB_NOT_RSS_OR_API_AUTOMATED_FETCH`；真实原文页面访问与程序 RSS/API 响应不可混称。
- 只留少量中文自述、可追溯 URL、明确报告期、数字和限制；不保存文章全文，未计算净利润；
- `Buffer` 不在既有20家身份台账中，仍只是待确立法律主体和经营范围的新公司线索；
- `publication_allowed=false`、`verified_revenue=false`、`legal_entity_verified=false`；目前不能新增网站正式推荐。

## 四、验收与下阶段

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

全量 CI PASS 后 PR 合并，再确认主分支与 Static Snapshot SUCCESS、公有目录仍然只有 Carrd/Plausible/NerdWallet。用户要求项目筛选而不是文章聚合，后续 R3 应优先对新的公司经营数据进行 **实际付费、来源主体、时段、币种、退款/获客成本**核实。

如要增加持续自动抓取频率，需要先核验 GitHub 私有仓库 Actions 免费配额/账单，不应仅因为外部 API 免费就默认 Actions 零成本。
