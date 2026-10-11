# JIANSHI 2.0 F2.1｜正式实施入口与里程碑板

日期：2026-10-11；第一批实施范围：G0 基线 + G1 最小风险骨架。
F1 冻结是历史产品定位资料；实施优先采用 F2.1 六份文件，不能将 G1 合并误报为完整 CMS 或真实撮合上线。

## 一、唯一工程实施规范（六份）

1. [G0 产品与页面审计](F21_00_PRODUCT_PAGES_AND_G0_AUDIT_CN.md)：代码源头、全站页面/角色、已交付和待交付。
2. [UI 设计与动效](F21_01_UI_DESIGN_SYSTEM_MOTION_CN.md)：设计令牌、页面、交互与移动端验收。
3. [状态机与权限](F21_02_BUSINESS_WORKFLOW_RBAC_CN.md)：业务权限、企业/个人隔离、非法状态转换。
4. [数据库、API 和 CMS](F21_03_DATA_API_CMS_CONTRACT_CN.md)：四区数据隔离、内容审核、待建 API。
5. [内容与质量工厂](F21_04_CONTENT_FACTORY_QUALITY_CN.md)：版权、来源、课程、合成样本与评分。
6. [测试、部署和回滚](F21_05_QA_RELEASE_ACCEPTANCE_CN.md)：G0-G5 门禁、E2E、真实域名与回退。

## 二、G0 证据与冻结点

- GitHub 版本证据从 PR 的 base/main SHA 获取；CI 与 Cloudflare 状态分别验证。
- 唯一正式制品：scripts/release/p412_build_public.py → web/dist；web/build.py 的 CF_PAGES 路径只接受经审核的静态快照。
- 生产 UI：P4.45 单首页；P4.46 八个内容页；P4.48 两个浏览器本地草稿工具。
- 正式研究：原有三条具名历史证据案例、六类匿名行业研究独立存在；公开显示受来源准入与隐私扫描约束。
- staging V2 六表 Force RLS（已只读核实）、账号与撮合开关关闭；生产账号关闭且未部署 V2。
- GitHub 工作流四个 UTC 时槽、HN7/RSS1/GitHub2 限额不变；真实 schedule 验收需用 event=schedule 运行证明。

## 三、G1 第一批可运行产物

- scripts/release/f21_design_tokens.py：11 项设计语义变量，增量注入 p445/p446/p448 页面；不恢复旧界面。
- scripts/content/f21_content_contract.py：离线 CMS 草稿模型、状态机、独立审核、来源和版权限制、公开白名单；没有业务 API。
- tests/test_f21_implementation_baseline.py：G0/G1 合同测试，失败禁止合并。
- 本轮不修改生产数据库、ACL、密钥，不开启真实 CMS。

## 四、G1-B 已完成记录

- [G1-B 组件、方案筛选、CMS 离线审稿验收](F21_G1B_SHARED_UI_CMS_WORKBENCH_ACCEPTANCE_CN.md)：PR #121 已合并，正式企业方案目录的真实浏览器交互 4→1→2→4 全部通过。
- 统一站点导航/页脚覆盖 8 个内容页及 2 个本地草稿页；仅方案目录新增已审核的前端筛选脚本。
- CMS 内核实现合成数据审核、版本校验、发布和撤回。**仍无真实管理后台、身份认证 API 或数据库持久化。**

## 五、G1-C 私有 CMS 底座（已通过 staging 安全验收）

- [G1-C CMS staging 合同与内部 UI 验收](F21_G1C_CMS_STAGING_ACCEPTANCE_CN.md)：私有五表迁移、内部合成数据编辑原型与隔离测试。
- 仅 staging 允许迁移，必须同时确认匿名/普通用户权限为零以及 production 没有 CMS 结构。
- 此阶段**不是**生产 CMS 后台，不接入公开站点的企业资料、订单或课程上传。

## 六、G1-D 私有事务接口（结构与拒绝写入验收通过）

- [G1-D CMS 事务、服务端角色与门禁](F21_G1D_CMS_TRANSACTION_GATE_CN.md)：写入 API 尚未部署，新增数据库受信任服务调用的写事务、版本锁、双人审核、私有快照。
- CMS+Auth 双开关与八项 Auth E2E 未放行时，私有事务一律拒绝写入。production 不迁移 CMS 或开放账号。

## 七、G1-E staging HTTP 网关与会话核验（已通过关闭门禁安全验收）

- [G1-E CMS 身份、真实会话与私有网关验收](F21_G1E_STAGING_CMS_GATEWAY_ACCEPTANCE_CN.md)：staging 专用会话存在性校验、仅服务角色可调用的 RPC 桥与 JWT 网关。
- 未经账号 E2E，运维开关保持关闭；不接入公网 CMS 管理界面，不开放内容提交，不把测试稿写入正式站点。

## 八、G1-F 内部 CMS 工作台与可执行流程测试（本轮）

- [G1-F 合成审核工作台与验收](F21_G1F_CMS_UI_SYNTHETIC_ACCEPTANCE_CN.md)：可切换内容队列、角色、审核状态、版本差异与素材版权；可执行 Node 单测。仅内部离线模拟，非已认证管理后台。
- GitHub 交付 `web/prototypes/f21f/`，不进入 production 静态发布；staging 数据/功能开关保持关闭。

## 九、下一阶段任务清单

G1-A：设计系统组件化；首页、目录、详情、工作台和 CMS 高保真预览与浏览器回归。
G1-G：安全门禁和自定义 SMTP 完成后，使用隔离测试用户连接 staging CMS API，完成真实 JWT、跨用户、并发版本锁、失效会话和私有素材 E2E；否则继续构建内部离线可验收组件，禁止扩大生产功能。
G2：有证据的方案、项目专题和资源内容生产 + 搜索/筛选；合成内容不能进生产。
G3：staging Auth E2E、两企业两创作者隔离、业务状态机全链路安全验收。
G4：真实企业试点与人工撮合。
G5：真实课程上传、学习进度与 AI 辅助推荐，按权限与内容审查放行。

## 十、结项口径

使用 PASS / CONDITIONAL / FAIL，分别报告 PR CI、主分支构建、Cloudflare 部署、实际生产 URL，注明尚未验证的 E2E。G0/G1 第一批完成不代表 CMS 服务端、真实订单或课程上传已经交付。
