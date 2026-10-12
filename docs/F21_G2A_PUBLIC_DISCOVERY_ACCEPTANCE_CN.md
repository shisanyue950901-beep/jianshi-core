# 见势 JIANSHI 2.0｜F2.1 G2-A 公共内容发现中心

日期：2026-10-12。范围：**公开静态内容整合与筛选**；不扩展认证/CMS、不抓取新数据、不改采集周期。

## 交付

- 新入口 `/discover/`，将 17 条**已有独立公开页面**汇集为四类：企业方案 4、匿名行业研究 6、公开项目档案 3、实用指南 4。
- 卡片仅使用人工编审的标题/简述/证据边界文字与固定内部 URL。不将网页上的数字自动转换为“真实营收”、“商机数量”、“平台活跃订单”，更不读私有 Artifact 原文、后台数据库或客户联系方式。
- 浏览器内中文关键词搜索、分类筛选、实时结果计数、无结果状态、重置及键盘操作。无后台查询、Cookie、LocalStorage、外部 SDK 或用户输入上传。
- `site_footer` 和首页既有底部链接新增「内容发现」，不增加主导航项目，不恢复旧数据仪表盘。
- `scripts/release/f21_g2_discovery.py`：审计允许的 17 个 URL + 构建时实际页面存在性检查；链接缺失或指向非内容页直接中止构建。只在已有公共页面发布后生成目录。
- 唯一正式构建器 `scripts/release/p412_build_public.py` 生成 `web/dist/discover/index.html` 并更新 Sitemap。禁止直接手工改 `web/dist` 等生成产物。
- 新 `tests/test_f21_g2a_discovery.py`，包括真实 JS 执行的关键交互、URL 白名单、离线失败闭合、隐私与无网络输入约束。

## 验收与发布口径

G2-A 单项 PASS 需要：GitHub PR CI SUCCESS → main 正式构建 SUCCESS → Cloudflare Pages 当前部署及源 SHA 验证 → `https://jianshi-bua.pages.dev/discover/` 实际 HTTP 200 和 HTML/JS 交互验收。**CI 单独 SUCCESS 不能当成正式网站已上线。**

后续 G2-B 在这一入口基础上迭代内容专题质量、筛选信息架构及人工审核的内容扩展。不得把尚未验证或未经授权的产品、客户、课程数伪装成已开放功能。

## 冻结安全约束

- GitHub `JianShi Static Snapshot` 真实 `event=schedule`、claim、一天一采规范及原四个 UTC 时段 00:55/06:55/12:55/18:55：**零修改**。
- HN Algolia≤7、Fathom RSS≤1、GitHub REST≤2：**不增加来源请求**。
- Supabase 正式账号、CMS 编辑、撮合功能继续关闭；不改任何数据库、授权、生产密钥或私有审计文件。
- 匿名研究页本身包含历史模式/证据局限，目录用「匿名模式研究」标注，不把它们当作具名案例营收或新上架商机。

## 核验结果栏

- G2-A 提交/PR：待补
- 独立 CI：待补
- main 构建：待补
- Cloudflare 部署：待补
- 线上实测：待补
