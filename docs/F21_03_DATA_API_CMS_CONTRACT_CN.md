# F2.1-03｜数据边界、API 与内容管理 CMS 合同

状态：CMS_CONTRACT_FIRST，第一批为离线验证模块；尚未建生产 CMS、未开通后端接口。

## 1. 四区数据隔离

A. 静态公共库：/projects/、/research/、/solutions/、/academy/ 的经审核公开文本，不含企业私有字段；唯一生成器 scripts/release/p412_build_public.py。
B. 业务私有域：staging jianshi_v2 六表（组织、创作者、作品、需求、申请、审核事件），强制 RLS，anon/authenticated 无直接权限；仅受控后端管理。
C. CMS 编辑域：内容草稿/版本/媒体权属/审稿事件，默认私有；发布后仅复制允许字段到公共静态快照。
D. 课程媒体域：私有原片、转码、授权播放 URL 和观看记录；不得以公开目录暴露未经授权的视频和附件。

## 2. CMS 模型（第一批）

内容统一字段：content_id、content_type、title、summary、category、tags、language、visibility、status、source_refs、source_verified_at、license_status、rights_owner、media_refs、reviewer_id、revision、created_at、updated_at、published_at、expiry_at。
内容类型：PROJECT_RESEARCH / SOLUTION_GUIDE / COURSE / LESSON / RESOURCE / EVENT / CASE_STUDY。
状态：DRAFT→IN_REVIEW→APPROVED→PUBLISHED；驳回 REJECTED→DRAFT，撤回 PUBLISHED→UNPUBLISHED；ARCHIVED 为终结或留历史。审批人与作者不能是同一主体。
内容公开门槛：事实来源/核验时间可追溯、媒体授权已确认、私有字段扫描通过、审核通过。对于课程还需媒体可访问性、章节一致性与版权复核。
课程视频阶段只建模型，不生成虚构课程。企业案例只有在获得真实使用授权并复核事实后才能成为 CASE_STUDY。

## 3. 管理后台最小接口定义（尚未实现）

POST /internal/content/drafts → 创建作者本人草稿；
PATCH /internal/content/drafts/{id} → 只有当前可编辑版本允许变更；
POST /internal/content/{id}/submit → 提交审核、锁定版本；
POST /internal/content/{id}/review → 经服务端管理员权限复核（作者不能自审）；
POST /internal/content/{id}/publish → 审核标记+授权+来源校验，发布不可含私有字段的公开投影；
POST /internal/content/{id}/retract → 公开下架，同时清除 CDN 缓存并留审计。
所有写接口必须校验会话、CSRF/同源策略、主体权限、资源归属、请求大小/频率、幂等请求 ID；生产未开放时全部返回 403 或 503（不收集正文）。
公开 GET /api/content 只能返回经过白名单投影的已发布内容，禁止直返 CMS 数据库行。

## 4. 第一批 G1 工程实现

- scripts/release/f21_design_tokens.py：设计令牌唯一源头，纯标准库；供现有静态构建工具后续使用。
- scripts/content/f21_content_contract.py：CMS 草稿/发布内容元数据离线校验器，审核门禁 fail-closed，不读写生产数据库。
- 测试采用 fixtures/f21/*.json 合成数据（如果创建）；不向 /web/dist/ 或生产内容复制样例。
- 以现有审核源为输入，不引入外部网络采集与新增定时任务。

## 5. 受控迁移和 API 上线前置

Auth Gate 八项 E2E 必须全通过；staging 设计内容 API 和人工审核 E2E 后才能评估生产 CMS 表迁移。数据库 migration 必须先 staging 备份/验证，生产使用单独明确授权的 release gate。
service_role 只能出现在可信服务端，不进浏览器、静态 JSON、公开日志；真实上传采用私有存储、签名地址、媒体扫描与单独授权。
