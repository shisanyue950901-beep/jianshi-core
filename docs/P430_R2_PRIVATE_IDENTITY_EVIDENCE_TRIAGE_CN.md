# P4.30｜具名商业证据自动核实 R2（内部首版）

## 目标与已做范围
- 继承 P4.25：只有可归属 L3/L4 的审核经营资料进入正式项目榜，HN 搜索、官网/收费、交易市场行业样本都不够。
- 冻结 20 个历史候选的品牌及官网主机名映射：`config/p430_company_identity_registry.json`。这是编辑记录，**不证明法律实体已核实**。全部 `legal_entity_status=UNVERIFIED`，与公开收入、实际净利润无关。
- 新增 `scripts/research/p430_company_evidence_review.py`：解析原 P4.26 有界 HN 检索报告，生成各公司“下一步找原始披露”的私有研究队列；不访问 HN 外部链接、不依赖 LLM。
- 对经独立检查使用权限后由授权方式取得、单独输入的文本快照，可做第一层公司/域名/来源路径校验、原始文本 SHA-256 指纹、MRR/ARR/付费客户的字面数字识别，保留币种不明、原始披露日期及真实性未核实标记。该能力**只生成审核候选，不能自动晋级 L3/L4**。
- 同一旧 `publish-static.yml` 中每日条件扫描成功时，直接进行离线 R2 入队，复用现有 48 小时私有 artifact；**不增加 cron、不增加网络请求、不上传第三方文章全文**。

## 当前真实证据能力
| 环节 | 状态 | 说明 |
|---|---|---|
| 发现 | 已有 R1 | 每天最多 6 家+1 主题，HN Algolia 元数据；新调度是否真正成功仍需首次实测 |
| 主体映射 | **R2 第一层已开发** | 品牌/官网域名强制对应，20 个法律实体身份仍未核实 |
| 原始全文取得 | **未接通** | 不自动访问受限网站；需要合法的原始输入或明确的官方许可机制 |
| 字面指标识别 | **待审候选** | 不把 MRR 当 ARR、不把 $ 默认成 USD、不计算利润或复制性 |
| 独立核证 | **未完成** | 需要官方实体信息、同一时段来源互证、纠错/撤回检测 |
| R3 晋级 | **未启用** | 台账、首页和 `web/dist` 不被这个研究脚本写入 |
| R5 单人创业可复制性 | **未完成** | 必须有客户需求、成交试单、成本与获客证据 |

## 本地隔离用法

从现有 R1 研究产物创建内部复核队列（**零外部请求**）：

```bash
python scripts/research/p430_company_evidence_review.py \
  --leads /tmp/p426_research_leads.json \
  --output /tmp/p430_review_queue.json
```

经独立合法取得且已有明确使用权限的原始文本，准备以下**本地**输入（不要放入 Git 或公开目录）：

```json
{
  "contract": "P430_PRIVATE_SOURCE_SNAPSHOTS_V1",
  "items": [{
    "case_id": "plausible",
    "asserted_brand": "Plausible",
    "asserted_home": "https://plausible.io/",
    "source_url": "https://plausible.io/blog/open-source-saas",
    "published_on": "2022-06-22",
    "source_text": "仅在合法获得的原始文章中填写该原文的内部研究片段"
  }]
}
```

```bash
python scripts/research/p430_company_evidence_review.py \
  --snapshots /tmp/approved_text_snapshots.json \
  --output /tmp/p430_private_review.json
```

最大 6 条、131072 字节输入、每条文本最多 48000 字符；拒绝危险 URL、未知身份、任意第三方来源、受限交易平台、带用户名密码或非 HTTPS 来源。上述示例纯说明格式，不是已取得合法授权或已获取原文。目标输出严禁落入仓库、尤其 `web/dist`。**报告是内部 REVIEW_ONLY，不是财务审计结论。**

## 风险与费用门禁
1. Acquire.com、Flippa、Microns、Empire Flippers 的挂牌信息不提取、不转载、不通过 HN 搜索绕过权限。第三方访谈需要逐个显式列入白名单，当前只含既有 Carrd 访谈；SEC 路径也必须匹配当前已知 CIK，报告仍待核查。
2. 不使用 TinyFish、付费 LLM/API/数据库；不读写 Supabase Production/Auth/RLS、不触碰 Cloudflare 方案设置与无关 PR #52/#49。
3. 新增的是原有每日研究步骤的**离线后处理**，没有新增 GitHub 定时执行次数或搜索请求。私有仓库 Actions 费用额度在当前工具权限下尚不能实时确认；在额度未确认前，不新增额外定时工作流、手动高频运行或付费部署。
4. `source_text_sha256` 是输入文本指纹，不证明输入真来自原始网页；来自输入的 `published_on` 也必须后续校核。短名称（如 Kit）自动阻断；跨公司财务描述不能凭同页出现品牌就归因。
5. GitHub CI 成功不等于首次真实日报已产出、不等于 Cloudflare 公网页面或手机端视觉验收。

## R2 / R3 后续验收入口
- 在许可明确的 SEC、官方经营披露中按来源单独增加 **受控低频** 原文读取器，包括 robots/协议、期限、User-Agent、来源大小、哈希和回退规则；**没有明确权限不启用**。
- 监管主体需核对 CIK、法定实体和合并范围；自行披露须记录说话人身份、原文日期、报告期、金额、货币单位及“未经独立审计”。
- 将 `NEEDS_REVIEW` 转换为审计 PR，需要第二来源或独立复核结论、差异报告、撤回检测和负面测试。**不能从单个自动文本数字直接提交公开收入台账。**
- 在外部交易行业背景与具名项目证据之间保留强制隔离；对已通过的新项目单独完成单人创业成本、获客、需求试单门禁。
