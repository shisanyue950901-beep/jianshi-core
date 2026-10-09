# P4.33｜商业数据自动清洗与证据审核流水线

**版本**：2026-10-09。继承 P4.26 / P4.30 / P4.31 / P4.32。定位：只读、私有、最小预算、真实来源身份审查、对外零写入。

## 先回答：是否“全部全自动，包括清洗”？

目前**不是**。正式上线后，已有 HN 每日限额检索可以完成“自动发现→自动基础清洗→同批去重→内部人工审核队列→48 小时私有 artifact”，而“具名法律主体核实、原始完整经营事实抓取、跨月来源变化、财务审计、L3/L4 晋级、公网发布”仍不在全自动流程中。单个 RSS 和 SEC 的按需收集能力已开发但尚未在真实 HTTP 环境完成可复现验收；这两个来源目前不自动进入每日任务。**能用来开发不是已经验证盈利。**

## 当前自动化层级及负责人

| 处理层 | 状态 | 门禁 |
|---|---|---|
| HN Algolia 发现 R1 | 已有定时工作流：UTC 00:55 附近，每日仅一个扫描槽，最多 6 个公司+1 个话题=7 次请求 | 失败不重试；不访问结果原文；每日实际产物仍待首次验收 |
| HTTP 健康测量（P4.33） | 新增请求尝试/成功/失败计数， ALL_REQUESTS_FAILED / PARTIAL_HTTP_SUCCESS 等 | 不能把 online 模式冒充“全部抓取成功” |
| 身份与来源初审 R2（P4.30） | 已有，20 个品牌和域名，法律实体均未确认 | 不将搜索标题匹配作为公司收入证据 |
| **统一字段清洗（P4.33）** | **新增**：清洗标题、解析可核 UTC 日期、标准化链接、去除追踪 query/fragment | 只输出内部 JSON |
| **来源去重及隔离（P4.33）** | **新增**：按 canonical URL 的 SHA-256 合并 HN 与官方 RSS 同一地址，保留原始来源途径；阻断受限挂牌、非法协议、私网/用户名/密码链接 | 同一 URL 在两个渠道出现不算独立交叉核验 |
| **增量检查（P4.33）** | 同一批次自动；只有显式传入 `--previous` 的旧私有报告才可比较跨天新增数量 | 没传 `--previous`，不得宣称跨天去重 |
| 合法网页原文/监管接口 R2 | SEC 官方 API / Fathom 官方 RSS 为手动显式 `--online` | SEC 需真实可联系邮箱；来源必须允许且受限 |
| R3 企业财务真实性及归属审核 | **未完成** | 历史自述≠已审计；不自动晋级或发布 |
| R5 一人小资金创业可复制性 | **未完成** | 仍需外部真实客户、获客及成本验证 |

## 本轮新增代码

1. `scripts/research/p433_private_evidence_etl.py`，离线、零网络请求：
   - 接收先前的 `p426_research_leads.json`，可选 `p432_fathom_rss.json`，可选 `--previous` 上次清洗报告。
   - 只从 P4.26 HN 搜索/官方 RSS 内部报告读取最少标题/原文链接/日期/来源类别，拒绝虚假审核字段、未受审公司映射、格式漂移。
   - 每次最多 40 条输入；受限挂牌网址不进入研究结果；不把动态页面售价或评论热度推导成 ARR、MRR 或净利润。
   - 统一 `contract=P433_PRIVATE_CLEAN_REVIEW_V1`，输出 `records` / `quarantine` / `source_health` / `duplicate_reference_count` / `new_to_private_review_count`。
   - 全部 `status=NEEDS_ORIGINAL_SOURCE_REVIEW` / `eligible_for_publication=false`。
2. `scripts/research/p426_daily_leads.py`：新增**每个请求真实成功与失败计数**，仍保持原有硬预算 7 次，不额外请求。
3. `.github/workflows/publish-static.yml`：仅在现有每天 HN 私有扫描成功生成本地 JSON 后运行离线清洗，加入**原来的** `research-leads-<run>` 私有 artifact，48 小时保留；原有调度次数不变。
4. `tests/test_p433_private_evidence_etl.py`：正向/失败/重复/跨来源合并/短品牌歧义/许可隔离/网络失败/私有输出负面测试。

## 已接入的每日流水线

```text
GitHub Actions 现有 6 小时静态任务（次数不变）
  └─ 每日仅 UTC 00:55–01:xx 时段
      ├─ P4.26：HN 6 公司 + 1 主题检索（最多 7 次）
      │   ├─ 请求 HTTP 健康计数
      │   └─ p426_research_leads.json（私有）
      ├─ P4.30：公司检索命中审核队列（完全离线）
      │   └─ p430_review_queue.json（私有）
      └─ P4.33：规范化/去重/来源隔离/质量指标（完全离线）
          └─ p433_clean_review.json（私有）
             上传到原同一个 artifact，48小时后自动过期
```

不能用“静态构建 SUCCESS”证明实际采集。下一次 scheduled 真实日扫描必须下载审查 artifact，核对 `scan_health`、HTTP 成功数、隔离率和 `source_health`；在这之前标记 **LIVE_ETL_UNVERIFIED**。失败时不改变公网、Supabase 或正式收录表。

## 在私有机器上的使用方法

HN 清洗，无网络：

```bash
python scripts/research/p433_private_evidence_etl.py --hn /tmp/p426_research_leads.json --output /tmp/p433_clean_review.json
```

Hacker News 与之前已取得且合法的 Fathom RSS 元数据合并清洗：

```bash
python scripts/research/p433_private_evidence_etl.py --hn /tmp/p426_research_leads.json --rss /tmp/p432_fathom_rss.json --output /tmp/p433_clean_review.json
```

与上次**私有报告**比较：

```bash
python scripts/research/p433_private_evidence_etl.py --hn /tmp/p426_research_leads.json --previous /tmp/previous_p433.json --output /tmp/p433_new_review.json
```

Windows 下 `/tmp` 路径可替换为独立于网站仓库的 `C:\JianShiPrivate\`。不把私有报告纳入 `web/dist`，不用高权限数据库写入。

## 费用与许可的阻断条件

- 私有仓库 GitHub Actions 有每月计划包含额度，但具体账单/剩余额度本轮不可得，不承诺绝对零费用，不创建额外 cron、仓储数据包、付费插件或高频重跑。
- HN 检索含的 Acquire / Flippa / Microns / Empire Flippers 等交易平台链接，会隔离而不是借助索引绕过挂牌使用限制。
- 官方 RSS 不能用作整站文章镜像；保存标题/日期/链接，不保存正文。
- `P433` 只负责机器结构化清洗；**没有法律主体/付费/利润认证能力**。
- CI PASS 不等于正式在公网/数据源网络运行成功。必须另行对 scheduled 运行产物进行取证。
