# 见势 F2.1｜G2-H.3 HTTPS 同源服务端会话与权限边界

日期：2026-10-12。**范围：真实 TLS/HTTP 请求 + 完全合成 GoTrue/CMS 上游。当前还不能开放真实运营后台。**

## 交付范围

- `scripts/qa/g2h3_https_bff.mjs`：以 Node 原生 `https.createServer` 构造仅绑定测试地址 127.0.0.1 的同源会话协议，必须具备 TLS key/cert（只从测试期间内存注入）。源模块无 CLI 监听入口，也没有对外用户登录、注册或 token exchange 路由。
- 服务端运行条件 `JIANSHI_G2H3_SYNTHETIC_ONLY=1`；存在真实 Supabase URL、数据库 URL 或服务角色密钥时主动禁止启动。它故意不可作为可生产部署的服务器直接使用。
- 会话只由测试进程调用 `issueVerifiedTestSession`，先调用 H2 的 `createStagingAuthAdapter.verify`（测试时模拟 GoTrue HTTP 响应），再生成随机 256-bit 不透明 Cookie。Cookie 带 `Secure; HttpOnly; SameSite=Strict; Path=/qa; Max-Age=900`。JWT 只在服务器内存里存储，不放入 Cookie、HTTP 响应或 URL。
- **每个 HTTP GET/POST 请求都重新调用 GoTrue/session/实时角色核验**，并且校验用户 UUID、session UUID 与首次会话绑定的身份一致；会话过期、服务端显式撤销、上游用户或角色撤销时不能凭旧 Cookie 继续访问。
- `POST /qa/api/action` 额外要求严格 Host、HTTPS、同源 Origin、Fetch-Site、CSRF、防超大请求体、严格操作字段白名单、请求唯一 ID 和角色类型；资源级读取/写入所有权检查由后端 dispatcher 执行，BFF 不得绕过它。
- 响应带 HSTS、no-store、frame/CSP/nosniff/referrer/permissions-policy。禁止把任何上游 token、服务密钥、未审核正文或 SQL 错误详情透传。
- `tests/g2h3_https_bff.test.mjs`：OpenSSL 在 GitHub Actions 的临时目录生成自签名测试证书，Node 原生 `https.request` 实际完成 TLS HTTPS、Cookie、来源防护、跨账号读取、独立审核、模拟发布/撤回、服务端角色撤销、CSRF、速率限制、会话超时和停用测试。
- `tests/test_f21_g2h3_https_bff.py` 将 HTTPS 测试纳入完整 Python 回归；原 `.github/workflows/cms-bff-isolated.yml` 只在相关代码 PR/push 时执行 Node22 E2E，无新 schedule。

## 证据分级与待完成

| 证据 | 可以证明 | 不可以证明 |
|---|---|---|
| 真正 TLS + localhost HTTPS 客户端 E2E | HTTP 协议、Secure Cookie、跨域/CSRF/权限拒绝确实执行 | 真实用户浏览器 JWT 登录 |
| 注入模拟 GoTrue 上游 | 每请求重新核验门禁/身份/Session/角色的错误处理 | GoTrue 在线鉴权成功或注册邮件已正确配置 |
| 内存合成 CMS dispatcher | A/B 隔离、审核流程规则可被 HTTP 测试覆盖 | 真实 Supabase CMS 正向编辑/发布 |
| 主分支 CI、静态构建 | 新测试未破坏原站且原型未进入公开构建 | 可信公网 BFF 已安全上线 |

## 真实生产链路尚有关键阻塞

1. 可信 HTTPS 托管环境与同源路由，及经过审批的 BFF 发布流程、回滚和安全审计。不能直接把测试 server 挂到公网。
2. **持久化/分布式服务端会话存储、原子限流和密钥轮换**；本项目当前只有内存测试会话，不可用于跨进程运营。
3. 通过真正 GoTrue 邮箱确认/JWT 的两账号会话 E2E、CSRF Cookie/会话绑定、服务端角色和资源级授权的正向业务测试。
4. 真实 CMS dispatcher、独立 CMS 数据读取投影、安全发布和撤回端到端。
5. Cloudflare Pages 内部路径 302→首页最终 200 的软 404 问题需独立查验 Cloudflare 路由；本轮不能将软 404 虚报为已修复。

## 冻结

不使用收费浏览器，不读取私有研究 Artifact、真实客户文稿、JWT 或财务数据；不开 Staging/Production `account_auth`、`cms_editor`、`v2_matchmaking`；不新增 P4.41 四个 UTC 调度槽，保留日 Claim、HN7/RSS1/GitHub2 调用预算。Push CI 不计作采集。