# JIANSHI F2.1｜G1-B 共用组件、内容筛选及 CMS 审稿内核

日期：2026-10-11。状态：**G1-B 本批次 PASS**（内容目录及离线 CMS 审稿内核）；不代表生产 CMS API、企业撮合、课程上传已经上线。

## 本轮真正在做的事情

| 交付 | 路径 | 行为 | 数据限制 |
|---|---|---|---|
| 统一导航与页脚 | scripts/release/f21_components.py | 公共6个导航、响应式菜单、真实 aria-current 和一致页脚 | 只使用静态冻结路由 |
| 企业方案本地搜索 | scripts/release/f21_catalog_filter.py | 关键词、3组分类、清除筛选、可访问结果数、无结果状态 | 只搜索既有四个经过编辑编写的应用方向，不访问网络、不记录查询 |
| CMS 审稿离线内核 | scripts/content/f21_review_workbench.py | 草稿创建、提交、独立审批、发布、撤回、版本冲突、审计记录、公开字段白名单 | 仅 Python 内存与合成数据；无真正账号、服务器或生产数据库 |
| 组件复用 | p446_content_hubs.py、p448_v2_local_drafts.py | 八个内容页与两个人才/需求本地草稿页复用统一导航 | 原用户草稿仍本地浏览器操作 |
| 自动验收 | tests/test_f21_g1b_components_and_cms.py | 验证十个页面、四类方案、脚本无网络、内容审核和权限拒绝 | 合成对象、零真实个人资料 |

## 必须保留的用户体验

- 首页仍是**唯一 JIANSHI 2.0 首页**，不恢复旧3D ring、旧图库或旧版冗余归档。
- /solutions/ 的筛选是增强功能：页面 HTML 直接包含四个已审核的方案，即使 JS 失效也可以阅读所有卡片；JS 运行时只隐藏不匹配卡片，不接触用户的浏览器存储。
- /marketplace/brief/ 和 /talent/portfolio/ 仍是未提交的临时草稿工具，不因导航重构而出现真实业务提交动作。
- 每个新页面仅一套主要导航和移动导航，aria-current 在有效频道上正确标记。
- AI 课程、企业真实订单、个人联系方式、浏览器支付均尚未开放，不能宣称实现。

## CMS 现阶段性质及下一步缺口

本轮 CMS 的内存状态机**不具备持久化和真实 API**。管理员鉴权、企业组织授权、审批审计的数据库事务化、乐观并发锁、数据保留/删除、课程对象存储需要单独 staging 设计与 E2E。不得用演示角色入参代替服务器可信身份。

下一批 G1-C：
1. CMS 编辑/审核后台在 staging 的安全分区建立表结构和版本历史，服务端认证身份、作者与审核员职责隔离。
2. 内容编辑工作台的真实 UI、预览、驳回理由和文件权属表单，先用合成样本。
3. 浏览器自动化验证四类方案筛选（包括搜索空结果、重置、键盘）、菜单和两本地工具；移动端 390px 和桌面 1440px 截图。
4. 经独立批准前不修改生产 Supabase schema、账户开关或研究采集频率。

## 发布四重验收

PR CI → main 自动构建 → Cloudflare Pages/Workers 部署成功 → 正式域名路径、按钮交互、旧研究链接可用。这四项分别记录，不可混为一个 PASS。

## G1-B 实际验收证据（2026-10-11）

- 功能合并：[PR #121](https://github.com/shisanyue950901-beep/jianshi-core/pull/121)，源提交 dc0c9d197baa1fc48a106177b8a326d3df615abf。
- GitHub PR 与主分支全量 CI：PASS；主分支自动静态快照和公开制品检查：PASS。
- Cloudflare Pages 与 Workers：对该提交部署 SUCCESS。
- 真实页面：https://jianshi-bua.pages.dev/solutions/；四个方案卡均为已有公开应用方向。
- 实际浏览器：初始4/4、输入“自动化”1/4、筛选“视觉与视频”2/4、重置4/4，全部通过。会话记录：https://agent.tinyfish.ai/runs/1d87fef7-350c-4f20-b889-dacf733e676b 。
- 原 /projects/、/marketplace/brief/、/talent/portfolio/ 与方案详情页面均经过只读线上访问核验。
- 真实 Safari/Android 实机、管理员可信身份认证、并发数据库审批与 CMS 媒体上传：**NOT_TESTED**；下一阶段单独完成。
- 本轮未修改 .github/workflows、数据库 ACL、账号开关或企业/个人真实私有资料。
