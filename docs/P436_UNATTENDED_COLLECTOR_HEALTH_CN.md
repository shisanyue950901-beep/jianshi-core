# P4.36｜见势商业数据无人值守采集与自动故障留证

日期：2026-10-09。继承 P4.26 至 P4.35 研发冻结条件：全部中文、仅个人研发研究、不自动商用、不得未经授权采集受限市场挂牌、Production 零写入、未经确认的收益声明绝不公示。

## 一、真实的数据源数量——不可用9个掩盖仅2个活跃来源

源数据：`config/p432_source_access_matrix.json`（9类）。

| 层级 | 数量 | 来源 | 状态 |
|---|---:|---|---|
| 真实 API / RSS 联网已验证并已接入每日自动研究槽 | **2** | Hacker News Algolia、Fathom 官方 RSS | 2026-10-09 P4.35 GitHub run 37933522433 取得 **HN 2/2、RSS 1/1 HTTP成功**；日常完整7+1 HTTP运行仍待次日验证 |
| 官方 API 代码已实现、按需、尚未完成真实 HTTP | **1** | SEC EDGAR submissions + companyfacts | 同一官方源的 **两个端点，不是两个独立数据源**；需真实有效操作者邮箱，自动任务目前禁止启用 |
| 官网公开内容由研究人员核对，批量自动抓取未授权 | **2** | Plausible、Buffer | 编辑性经营研究线索，未自动联网采集 |
| 未取得抓取权限的受限平台/站内内容 | **4** | Acquire、Flippa、Microns、Indie Hackers | 默认禁止批量自动抓取，个人私用不自动免责 |
| **合计** | **9** | 9种来源类目 | **不是9条常态自动采集管道** |

P4.35真实记录：GitHub Actions https://github.com/shisanyue950901-beep/jianshi-core/actions/runs/37933522433 ，HN 2次请求+RSS 1次全部HTTP成功，获得10条RSS元数据，统一清洗后的链接13条，零正式财务声明与零公开新增；历史索引13个SHA256指纹。**这是一次性 smoke，不是定时连续多天成功**。

## 二、P4.36 的无人值守规则

沿用已有 `.github/workflows/publish-static.yml`，没有新增任何 GitHub job 或 cron；每6小时的静态快照保持，但私有线索采集仍只有 UTC 00–01（通常是00:55）的每日一个时段：

- 每日 HN Algolia 最多 **7次**（6公司+1主题），Fathom官方RSS最多 **1次**；最多8次外部来源HTTP。无抓取网页正文、无代理绕过、无自动重试；
- 自动生成 HN R1、公司身份线索R2、RSS元数据、规范化/去重、跨日指纹、聚合健康，并依旧放入原48小时私有Artifact；
- 新增 `scripts/research/p436_unattended_guard.py` 严格交叉检查：是否真实8次尝试、成功数、清洗条数、索引指纹/日期/当前URL一致性、公司和财务未晋级、非公开；
- 自动健康判定：
  - `PASS`：HN 7/7 + RSS 1/1 HTTP成功、至少一条已清洗线索、上一份私有历史恢复成功，机器报告正常；
  - `DEGRADED`：至少1次真实HTTP成功但存在部分来源故障、历史冷启动或没有清洗记录；**写GitHub Actions Warning，不把抓取失败隐藏成成功**，每日工作流可正常结束；
  - `FAIL`：8次真实HTTP尝试全部失败，或结构化输入/安全门禁不可通过；**发GitHub Actions Error并使作业失败**，此前产生的私有数据仍尝试保留。
- 私有Artifact 上传采用 `always() && github.event_name == 'schedule'`：即使采集健康门禁失败，也能将既有文件和新 `p436_unattended_verdict.json` 保存48小时，供问题排查。GitHub Actions 本身标记失败后能否推送邮件/客户端提醒，取决于仓库与账号的通知配置；工作流本身不声称已经发送消息。
- 一次性的P4.35 push smoke已经验证成功，现**正式撤销它的 push 消息自动触发门禁**；以后的 push 构建不再消耗研究来源请求；
- GitHub 静态发行清单继续强制拦截研究配置、研究JSON、内部联系信息和未审计财务；机器生成的 `verdict` 必须写入仓库外 `$RUNNER_TEMP`，**不是公开网页**；
- 历史索引来自48h内的上一次私有Artifact，冷启动就标 `DEGRADED`；指纹设计最多1200个、45天逻辑时窗，但两天没有有效产物会失去历史；**不能宣称永久仓库**。

## 三、用户无需每日手工执行什么

正常情况下无需人工按时运行脚本：GitHub schedule → API/RSS → 规范化清洗/去重 → 私有留证 → 自动健康判定。只有在GitHub自行停用workflow、网络完全不可达、余额耗尽、授权/源结构变化、数据真实性模糊时才需介入。

异常调查路径：
1. [GitHub Actions · JianShi Static Snapshot](https://github.com/shisanyue950901-beep/jianshi-core/actions/workflows/publish-static.yml) 中找到日期和 `event=schedule` 的run；不要把 `push` 的静态PASS错当数据采集成功。
2. 查看汇总 `p435_scan_health.json`：HN成功/失败、RSS成功/失败、是否历史冷启动。
3. 查看新增 `p436_unattended_verdict.json`：PASS/DEGRADED/FAIL及原因码；如作业失败，`always()`仍尝试上传证据；若Runner本身未启动或GitHub存储出错，则Artifact无法保证存在。
4. 查看 `p433_clean_review.json` 与 `p434_hash_index.json` 的同批去重和跨日增量；来源标题不是营业额，尚无财务审计。
5. 不进行生产修复性写入，也不能因失败跳过L3/L4发布闸门。Github token、真实SEC联系邮箱不得放入JSON日志或网页。

## 四、当前验收状态和费用

- **P4.35 一次性真实跑通**：已验收；日常定时连续运行、日常7+1请求以及第二次历史索引恢复：本次开发时还没有可用 `event=schedule` 新报告，严格标记 **LIVE_DAILY_UNVERIFIED**。
- P4.36 CI 全量PASS仅表示代码与防护逻辑通过，不能凭合并后 `push` 构建验证下一次 `schedule` 的活数据。
- GitHub Actions 已有的四次/日静态作业不变，私有线索每天只一个槽，失败不增加额外高频重试；新增健康校验几乎不加网络开销，但**当前账户免费分钟余额/账单仍不可读取，不能承诺绝对免费**。
- 其他来源进一步扩容应遵循实际权限与有效的支付/收入证据边界，不能仅凭“我们自己使用”直接全量爬取第三方商业挂牌和限制性内容。

验收命令：`python -m unittest discover -s tests -p 'test_*.py' -v`。如希望在ChatGPT收到“超过一天未产生计划任务”的独立通知，可设置定时监控；该监控和 GitHub Actions 内部工作流是两个不同层级。
