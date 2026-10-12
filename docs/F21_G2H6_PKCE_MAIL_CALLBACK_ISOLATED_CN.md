# 见势 F2.1｜G2-H.6 第一批：无密码邮件回调与一次性 PKCE 安全协议

日期：2026-10-12。本批为**隔离环境工程交付**，不是新登录方式已经上线。

## 本批内容

- `scripts/qa/g2h6_pkce_login_contract.mjs`：未来可信 HTTPS 同源 BFF 的无密码登录协定。开始流程生成 256-bit 随机状态、状态 Cookie 和 PKCE 验证器；验证器经 HKDF 派生的 AES-256-GCM 密钥加密后，才提交至私有状态存储。只存 HMAC 摘要与带鉴别标签的密文，不存邮箱、明文 verifier、原始 Cookie。
- Cookie 命名采用 `__Host-jianshi_pkce`（Secure、HttpOnly、SameSite=Lax、Path=/），有效期 300 秒；验证后清除此 Cookie，返回新的 `__Host-jianshi_cms`（Secure、HttpOnly、SameSite=Strict）服务端不透明会话 Cookie。TLS 响应有 no-store、no-referrer，成功后只进行 303 到 `/cms/` 的无 token 路径。
- 回调必须校验单一 `state`、单一 `code`、固定相对路径、同源 HTTPS/状态 Cookie；只有原子消费私有状态后才能调用真正的 PKCE `exchangeCodeForSession` 适配器、实时 GoTrue JWT + 会话 + CMS 角色验证器与 G2-H.4 持久会话颁发接口。消费失败/过期/重放/错误 Cookie 全部拒绝。
- `db/migrations/0061_jianshi_cms_pkce_one_time_state.sql`：Staging-only 私有 `bff_pkce_challenges` 表，强制 RLS/FORCE RLS、服务角色专用；`bff_issue_pkce_v01` 与 `bff_consume_pkce_v01`，原子 UPDATE ... RETURNING 确保多个 BFF 实例争用状态时最多一个成功。登录挑战的开始和消费均受账号/CMS 及八项 Auth 发布门禁控制。
- Node 22 + OpenSSL 临时证书：真实 HTTPS 回调安全测试，不向外网发邮件。测试八路并发同时使用同一链接只能成功一次、跨浏览器 Cookie 冒用、过期、撤销、错误参数和无 token 响应。
- 一次性 PostgreSQL 测试加载原始 0037、0054–0061 SQL，在六条不同连接并发消费状态，验证单成功、多失败、错误 Cookie 不消耗状态、过期拒绝及匿名不可执行。与原 CMS/持久会话事务共用独立容器。

## 重要边界

1. 本阶段 `sendMagicLink` / `exchangeCodeForSession` 是**注入式 PKCE provider 合同**，模拟服务响应。尚未连接真实 Supabase 的邮箱模板和 PKCE 交换流程；不能声称真实邮箱已完成登录。
2. 当前 Supabase Staging 旧回调页仍使用自己的 sessionStorage 临时身份流程；本批代码**不替换或部署**该入口，不更改现有测试邮箱或 SMTP 配置。
3. 不能把本地测试的 `pendingStore` 内存示例部署公网。生产集成必须调用私有 SQL 状态原子接口，密钥经可信密钥管理服务提供；必须审计 HTTPS ingress 不记录 code/state 查询串。
4. callback 模块只在 `JIANSHI_G2H6_SYNTHETIC_ONLY=1` 且测试 Origin 为 localhost/127.0.0.1 才可实例化；没有可公开监听的 HTTP server。正常邮件 OTP/PKCE 需核实 provider 如何生成 code 和 code_verifier，以及用户跳转后的同源域名/端口。
5. 真实 GoTrue 邮件登录、双用户 JWT 正向验证、受控公网 HTTPS BFF、真实 CMS 写入/审核、Cloudflare 软 404 均未通过，不得开启生产账号/CMS。

## 安全约束

不使用真实邮箱、JWT、刷新令牌、密钥、客户资料或私有研究 Artifact 做测试；不改变任何 Production 标记/表/服务，也不启用 Staging 账号、CMS 和撮合；不增加 P4.41 UTC 00:55、06:55、12:55、18:55 四个 schedule，不更改每日 claim 或 HN7/RSS1/GitHub2 访问预算。静态 `push` CI 不视为研究采集。

**结论门槛：** 本阶段只在 Node HTTPS、安全单测、一次性 PostgreSQL 原子状态以及主分支静态回归全部成功后结项。真实邮箱/BFF 仍留在下一阶段。

## 2026-10-12 实际验收结果（合并前）

- [CI 主回归 #38262520603](https://github.com/shisanyue950901-beep/jianshi-core/actions/runs/38262520603)：**SUCCESS**。
- [Node TLS 回调专项 #38262520472](https://github.com/shisanyue950901-beep/jianshi-core/actions/runs/38262520472)：**SUCCESS**，合成服务验证一次性 PKCE 回调、防重放、错误浏览器 Cookie、并发请求、过期和无令牌回显。
- [PostgreSQL 16 专项 #38262520710](https://github.com/shisanyue950901-beep/jianshi-core/actions/runs/38262520710)：**SUCCESS**，加载原始 SQL 迁移 9 项；真实六路不同数据库连接争抢一次性状态，**一成功、五拒绝**；过期、重放、错误 Cookie 均拒绝。原 CMS、HTTPS 会话集成仍 PASS，累计 26 项安全拒绝。
- Staging `apuibjhxinumxbfnqlkp` 仅执行私有加法迁移 0061，成功。表 `bff_pkce_challenges` 强制 RLS/FORCE RLS，匿名及 authenticated SELECT 均为 false，service_role SELECT=true，**当前行数 0**。三个私有 RPC 均 SECURITY INVOKER，且只有 service_role 可执行。
- 对 Staging 以 `SET LOCAL ROLE service_role` 调用真实私有挑战发放 RPC，已确认 `42501 CMS_WRITE_DISABLED`；直接用 postgres 执行会先被 `CMS_TRUSTED_SERVER_ONLY` 拦截，两者不可混淆。
- Staging CMS 内容、角色授权、持久会话和待验证 PKCE 状态均 0；`account_auth/cms_editor/v2_matchmaking=false`。Production 无 `jianshi_cms` schema，`account_auth=false`。
- **限制**：未发送真实验证邮件，也未完成真实 GoTrue PKCE code 交换/双账号登录；上线前需要确定邮箱模板/GoTrue PKCE 存储合同、可信 HTTPS 入口、回调查询串脱敏、密钥托管、持久会话及浏览器正向授权测试。旧 Staging 邮箱回调入口未被替换。
