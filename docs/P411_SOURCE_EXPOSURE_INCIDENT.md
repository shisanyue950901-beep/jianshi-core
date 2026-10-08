# P4.11｜公开源码泄露与数据库视图 ACL 事故收尾

状态：HOTFIX_PENDING_PUBLIC_REDEPLOY

## 已核实的生产暴露面

2026-10-08 在线读取确认：
- /config/p46a_concrete_opportunity_prototypes.json 可直接访问
- /.github/workflows/publish-static.yml 可直接访问
- 说明 Cloudflare Pages 当前可能配置为仓库根目录输出，源码和配置不应直接放进公开制品

这是实际暴露而不是单纯理论风险。需尽快把 Cloudflare Pages 的发布目录改为纯静态输出 `web/dist`。
仓库内 `_redirects` 是根目录误发布时的临时防护，不可替代正确的发布目录设置。

## 数据库权限事故

Production 曾发现 13 个匿名用户可 SELECT 的技术、商业证据或数据渠道规则视图。

现已在 Production 与 Staging 执行 `scripts/security/p411_revoke_source_views.sql` 同等 SQL，
两个环境权限复核均为 0 个残留敏感视图 SELECT 授权。

保留 Edge Function service_role 的内部只读访问，未修改业务数据、评分引擎或表结构。

## 部署防护

- 在 `web/static/_redirects` 配置内网目录及源码目录全站临时重定向；
- 在 `web/static/_headers` 对页面设置 `Cache-Control: no-store`；
- 静态构建统一复制 `_headers` / `_redirects` 至 `web/dist`、`dist`、`public` 和根目录；
- CI 以 `scripts/security/p411_audit_public_artifacts.py` 检查网页、脚本、JSON 里是否出现第三方供应商、原始标题、编号、来源字段。

## 仍待云平台操作

**必须在 Cloudflare Pages 后台执行：**
1. 将生产项目的 Build output directory 从 `.` 或仓库根目录改为 `web/dist`。
2. 检查并移除可从公网访问的旧 Preview/Branch Deployments；确认域名路由和访问策略。
3. 对 Cloudflare 缓存执行清理，检查搜索缓存是否记录过历史配置和原始项目。
4. 检查已发布的历史配置内容是否包含需要轮换的凭据；已存在的公开信息无法保证从第三方缓存消失。

本仓库当前的 GitHub、Supabase 连接没有 Cloudflare Pages 后台项目配置和部署删除权限，
因此不能将这些步骤报告成已完成；需 Cloudflare 连接或用户在后台手动操作。

## 不变项

- OPP_V0.2、数据库表结构和数据采集不改；
- Auth Gates 保持关闭；
- PR #52 不合并；
- 6 个首批研究页继续 noindex,nofollow。

## 最终 Gate

```text
P411_PROD_SENSITIVE_VIEW_ACL = PASS_13_REVOKED
P411_STAGING_SENSITIVE_VIEW_ACL = PASS_13_REVOKED
P411_PUBLIC_BUILD_ARTIFACT_AUDIT = CI_PENDING
P411_STATIC_ROOT_DENY_RULES = DEPLOY_PENDING
P411_CF_PAGES_OUTPUT_DIRECTORY = PENDING_DASHBOARD
P411_OLD_DEPLOYMENT_CLEANUP = PENDING_DASHBOARD
P411_CACHE_PURGE = PENDING_DASHBOARD
```
