# 见势 F2.1｜G2-H.4 私有持久会话与多连接限流

日期：2026-10-12。**交付性质：面向未来可信 HTTPS BFF 的持久会话底座，Staging-only 数据库迁移和一次性容器/Node 安全验收；不是运营后台上线。**

## 核心方案

- `db/migrations/0060_jianshi_cms_durable_bff_sessions.sql`：新增私有 `jianshi_cms.bff_sessions`，强制 RLS（FORCE RLS），仅 `service_role` 能读取、追加、更新。匿名/普通登录角色无表权限和函数执行权限。独立会话上限 15 分钟，撤销时间字段与密钥版本 ID。
- BFF 浏览器 Cookie 采用高强度随机不透明令牌；数据库只保存 HMAC-SHA256 摘要（带 BFF 专有密钥），CSRF 保存另一把密钥的 HMAC 摘要，二者互不相同。数据库不保存原始 Cookie、原始 CSRF 或明文 JWT。
- `scripts/qa/g2h4_session_vault.mjs`：BFF 侧用 AES-256-GCM 加密 GoTrue JWT（每次随机 IV、验证标签，AAD 绑定用户 UUID + GoTrue 会话 UUID），加密 envelope 和 `key_id` 进库；密钥由可信服务器密钥管理器管理，绝不写在数据库、源码或 HTTP 响应。新密钥轮换时可保留旧密钥读权；退役旧 key 时旧会话必须失败关闭。
- `jianshi_cms.bff_issue_session`：必须先检查现有 `ensure_write_gate` 的 CMS/账号/八项 Auth 门禁，且 `auth.sessions` 必须有效。只允许服务端授权操作。
- `jianshi_cms.bff_consume_session`：真实 PostgreSQL `SELECT .. FOR UPDATE` 锁住会话行；每次验证未过期/未撤销、GoTrue `auth.sessions` 与 CMS 角色门禁。写入时再次校验 CSRF 摘要，1 分钟最多 8 个有效写请求，多后端并发时配额仍一致。限流状态作为无令牌的返回值，不使用 RAISE 去回滚已更新计数。
- `jianshi_cms.bff_revoke_session`：紧急撤销必须在功能开关关闭后依然可用，不返回浏览器可探测的会话是否存在。
- GitHub Actions 隔离 PostgreSQL 16（原始 0037 + 0054–0060 SQL）实测创建、读取、权限、12 路并发限流、GoTrue auth.sessions 过期、功能开关关闭后的紧急撤销；Node 22 单元测试 AES-GCM 篡改、跨账号密文挪用、HMAC、密钥版本切换与退役。均不访问外部 Supabase API。

## 边界与需要继续完成的工作

| 项目 | 状态 |
|---|---|
| AES-GCM 封装与客户端随机令牌加密规则 | 待 CI 专项验收 |
| 独立 PostgreSQL 行级并发和角色 ACL | 待 CI 专项验收 |
| Staging 私有会话表安装（功能开关保持关闭） | 待授权后的非生产迁移与负向验收 |
| 实际 HTTPS BFF 连接该 SQL Store + Vault | **未实现**，当前只是分离的可测试组件 |
| 真实 GoTrue 邮箱登录、JWT 正向交换 | **未测试**，不得开启生产 |
| 多节点共享 Session 存储/分布式密钥配置、轮换演练 | **尚未部署** |
| 持久 CMS 页面与账号绑定、工作流真实发布 | **未实现** |
| Cloudflare Pages 未知内部路径软 404 | **未解决**，待单独修复路由规则 |

关键安全说明：测试只生成合成身份、测试密钥和测试加密文字；`service_role` 是受限的内部调用权限，不代表浏览器可写；数据库受控迁移不代表真实端到端认证。没有托管 BFF 的安全部署审批前不开放任何浏览器登录接口。

**安全冻结**：Production 不进行数据库更改；Staging `account_auth/cms_editor/v2_matchmaking` 始终关闭；任何 `event=push` 的静态构建不当作 P4.41 每日研究采集；维持原 UTC 00:55、06:55、12:55、18:55 四个 schedule、daily claim、HN 最多 7/RSS 最多 1/GitHub 最多 2 次预算。无收费浏览器，不读取私有来源 Artifact、财务记录或凭证。