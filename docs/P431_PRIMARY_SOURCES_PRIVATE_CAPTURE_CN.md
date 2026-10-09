# P4.31｜合规新增原始商业证据源（内部采集第一批）

**基线**：P4.30 `main` 合并提交 `870b1f6`；严守既有 L3/L4 准入。当前正式 3 家及 17 家待核实项目不变。

## 2026-10-09 已核查的权利边界

| 来源 | 官方许可/访问机制 | 当前执行 |
|---|---|---|
| SEC EDGAR submissions | 美国 SEC 官方开放 JSON API，无需 API 密钥；需声明操作者 User-Agent 并遵守 Fair Access | **新增按需双请求采集器**，单 CIK、只读、无自动定时、私有输出 |
| SEC EDGAR companyfacts | 官方 XBRL 结构化公司财报 API，同上 | **新增按需采集**，只生成报告期/accn 配对的待复核事实 |
| Fathom Analytics 官方文章 | 官网公开编辑性资料；自动批量抓取/再分发权限未审核 | 本次只手动阅读 3 篇、内部记原链接与极简事实描述，不缓存文章、不批量抓取 |
| HN Algolia | P4.26 已有公共元数据接口 | 不增加每日 7 请求硬预算 |
| Acquire.com | 买卖双方条款未经书面许可禁止自动或人工提取挂牌等数据 | 挂牌禁止抓取，私用不豁免 |
| Flippa | 条款限制未经书面许可提取和重复利用 | 挂牌禁止抓取 |
| Microns.io | 官方条款第 9 条 C 明确禁止无授权 crawl/scrape/spider | 挂牌禁止抓取 |

官方政策：
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- https://www.sec.gov/about/developer-resources
- https://www.sec.gov/about/privacy-information
- https://acquire.com/buyerseller/
- https://flippa.com/terms-of-service/
- https://www.microns.io/terms

公开原始内容仅链接，不复制整篇文章。不能因“仅内部自用”默认获得对受限挂牌网站的抓取权限。

## 本次实获的第一手可归属候选（Fathom）

独立通过公开网页工具阅读以下原始页面（2026-10-09），只保存最少量内部编辑信息于 `config/p431_private_primary_source_leads.json`：
1. 2019-11-04 创始人 Paul Jarvis 叙述历史 MRR 约三倍增长；**没有从倍数推算 MRR 绝对额**：https://usefathom.com/blog/v2
2. 2021-06-29 官方说明历史过去 12 个月收入和客户各增长 200%；**并非 2026 年金额、净利润或审计数据**：https://usefathom.com/blog/new-fathom
3. 2024-12-02 公司披露 Jack Ellis 收购共同创始人 Paul Jarvis 的股份；**不是不相干第三方的并购挂牌，也没有披露成交对价**：https://usefathom.com/blog/acquired

全部标记 `NEEDS_REVIEW`、`POTENTIAL_L3_NOT_ADMITTED`，法律实体尚未独立核验，未更新 `config/p424_project_research_evidence.json`。2024 股权事件只是实体和经营历史背景，不是收入指标。

## 新增 SEC 双 API 采集器

`scripts/research/p431_sec_primary_probe.py` 仅对 **NerdWallet** 冻结的 CIK `0001625278` 开放，且只会请求：

- `https://data.sec.gov/submissions/CIK0001625278.json`
- `https://data.sec.gov/api/xbrl/companyfacts/CIK0001625278.json`

执行要求：
- **必须显式启用 `--online`** 并提供真实操作者邮箱给 SEC User-Agent。没有真实邮箱就拒绝访问；不使用私有个人资料推断联系地址。
- 最多 **2 个** HTTPS 请求，间隔至少 1.5 秒，响应单个最大 16 MiB、单次 8 秒超时；403/429 停止，不重试、代理绕过或回退爬网页。
- CIK 同时存在于受审登记；两份返回的 CIK、公司名称都须匹配。仅允许同一次 10-K/10-K/A 的 accession、申报日期、FY 报告期和 USD XBRL 标签；不同来源相同数字**不意味着独立交叉证实**，多种收入标签不得相加。
- 输出只允许**仓库外路径**，保留两份原始响应哈希、公司名称、10-K 官方链接与字面候选字段；**不写原始 JSON 到仓库**，不写 Supabase，不能晋级正式目录。
- 运行时邮箱不进入报告或 Git。SEC 访问成功时报告 `LIVE_OFFICIAL_SEC_API`；在测试模式必然 `OFFLINE_FIXTURE_NOT_LIVE`。构建、CI 或存在脚本**不能算真实联网采集成功**。

### 手动按需运行（需具备真实网络、真实联络邮箱）

```bash
python scripts/research/p431_sec_primary_probe.py \
  --online --case nerdwallet \
  --contact "实际操作者联系邮箱" \
  --output /tmp/p431_private_sec_review.json
```

本轮执行环境联网无法解析 `data.sec.gov`；**尚未真实执行两项 SEC API**，其状态为 `LIVE_UNVERIFIED`。不能声称抓到最新财务。

### 完全离线回归

```bash
python -m unittest tests.test_p431_sec_primary_probe -v
python -m unittest discover -s tests -p "test_*.py" -v
```

数据采集器支持 `--fixtures <目录>`（包含 `submissions.json` 与 `companyfacts.json`），并明确写 `OFFLINE_FIXTURE_NOT_LIVE`。测试使用合成样本，不混充 SEC 实时证据。

## 下一阶段（明确尚未完成）
- 补全 Fathom 的合法实体和创始人自述边界，校验历史收入的原始语句，必要时变更为新增证据 PR；仍不可将官方文章等同独立财务审计。
- 在经许可、有联系方式和可控额度的执行环境中完成 SEC 的第一次真实 API 采集，审核期别/合并范围和最新申报；根据 SEC 撤回/更正状态定期复核。
- 选出 2–3 家有原始经营透明度的轻资产项目优先进行需求、客户、获客与交付成本验证。新候选不自动进正式榜。
- **仅当 GitHub Actions 免费额度、调度实际产出及用户授权条件核实后**，再考虑把在线 SEC 采集纳入现有低频调度。不新增高频 cron、付费浏览器、付费数据库或生产 Supabase 写入。
