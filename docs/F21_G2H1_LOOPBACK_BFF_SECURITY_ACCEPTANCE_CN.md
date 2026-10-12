# 见势 F2.1 G2-H.1｜同源 BFF 安全契约与中文 CMS 工作台

**日期：2026-10-12。定位：第 1 批隔离工程验收，尚未接真实 Supabase 用户或 CMS。**

## 实际代码

- `scripts/qa/g2h_loopback_bff/server.mjs`：Node 原生 HTTP 的本地同源 BFF 合同测试服务器，**只能在 `JIANSHI_G2H_SYNTHETIC_ONLY=1` 下启动**，拒绝持有 Supabase URL、服务角色 Key、DATABASE_URL；只监听 `127.0.0.1`，Host 也必须是本机地址与端口。无任何外部请求/代理能力，不会转发真实 JWT 或私有 CMS 正文。
- 登录凭据由测试进程内 `issueFixture` 创建随机 256-bit 合成 Session Cookie（HttpOnly、SameSite=Strict、Path=/qa），**没有可公开调用的创建账号/登录/提权 URL**；绝不接受请求体的 `actor`、`role` 或其他越权字段。另有 15 分钟过期、显式撤销。因仅本机 HTTP 夹具，不冒充 HTTPS 生产 Cookie 安全性。
- `POST /qa/api/action` 强制同源 Origin、Fetch-Site、服务器端存储的 CSRF Token、JSON 类型/8 KB 限额、每会话 60 秒频率阈值和白名单操作+字段；拒绝操作不会改变内容修订、快照或审计事件。
- 合成角色 2 名作者、1 名审核员和 1 名发布者，仅能在批准的状态机操作；支持编辑、恢复旧版为新的未核验稿、审核、驳回、发布和撤回。禁止自审、非作者编辑、重复请求、过期会话、错误版本及仍有未撤回快照的恢复。
- `index.html`、`app.js`、`style.css` 为**可见的中文操作台**，带状态、版本历史、审计事件、模拟快照、中文拒绝反馈、移动端布局与键盘焦点。所有前端调用仅相对路径 `/qa/api/...`，不存储登录令牌或请求客户资料。
- `tests/g2h_loopback_bff.test.mjs`：真实本机 HTTP 交互测试；`tests/test_f21_g2h_loopback_bff.py` 将它纳入旧的全部 Python CI；新增独立 `cms-bff-isolated.yml`，明确 Node 22 和权限 `contents: read`，只在相关路径 PR/main push 执行。

## 安全冻结及证据等级

| 能力 | 当前判定 |
|---|---|
| 真正的本地 HTTP Cookie / Origin / CSRF / RBAC / 限流 / 撤销测试 | 以 CI 真实结果为准 |
| 中文 CMS 模拟工作台 HTML+JS 与浏览器本地协议 | 已写源码，但不代表真机视觉已通过 |
| 真实 Supabase GoTrue 登录、Session 验证和服务端 BFF 转发 | **NOT_IMPLEMENTED** |
| 真实用户账号下的 CMS 正向写入、审核、发布 | **NOT_TESTED** |
| 独立媒体授权、对象存储、内容来源人工终审 | **NOT_TESTED** |
| 生产部署与 CMS 业务开关 | **禁止** |

此本机实现并非一个已符合生产要求的 BFF：HTTPS Cookie Secure、受信代理路由、独立 Session 存储、分布式限流、密钥轮换、实际业务权限等均需要后续单独工程验证。

**绝不部署此 QA server 到 Cloudflare Pages / Workers、Supabase Edge 或公网服务器**。不能将 in-process 测试角色当作真实 Supabase 角色授权。`web/dist`、官方构建器和生产 Auth/CMS 完全不变。

保留 P4.41 的原 UTC 00:55、06:55、12:55、18:55 四个 schedule、日 Claim、HN7/RSS1/GitHub2 次数上限；新增工作流是 CMS 相关 PR/push CI，不是 schedule、不会触发真实采集，不能算日来源健康。

## 后续 G2-H.2

在独立 Staging 安全审批后，设计真实同源会话交换和已验证用户服务端 BFF；必须绑定现有 GoTrue 验证及实时 `auth.sessions` 吊销检查、可信服务端限流，再做多账号/多角色真实 E2E。达到安全门禁前保持失败关闭。