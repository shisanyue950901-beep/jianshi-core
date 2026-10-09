# P4.14｜官网入口与依据链接整改验收说明

核查日期：2026-10-09（北京时间）

## 问题与整改
- P4.13 的 Carrd 详情中，标题“访问项目官方网站”实际仅跳转到定价证明页面，无法一键访问企业主页。
- 所有 12 个具名项目采用两个独立、可见、语义准确的链接：**访问项目官方网站（首页）**、**查看核对依据（产品／定价页）**。
- 原 10 个编辑档案保留 `sourceUrl` 兼容字段，增加 `officialHomeUrl`。最初两份视觉案例在单文件脚本内补充对应字段；商业模式介绍不显示企业官网。
- 用 `URL` 对两种地址做 HTTPS、主机名、禁止凭据判定，失败则不渲染该链接；所有外链都使用 `target="_blank"`、`rel="noopener noreferrer"`。
- 保留黑色单 HTML、8 张 WebP 封面、3D 环、灯箱、搜索、`inert`、reduced-motion、移动视口适配及 Cloudflare 仅发布 `web/dist` 的约束。

## 官方首页与核对依据

| 具名项目 | 官方首页 | 原有或新增核对依据 |
|---|---|---|
| Easlo | https://www.easlo.co/ | https://www.easlo.co/templates |
| Louise Lennox | https://www.authorlouiselennox.com/ | https://www.authorlouiselennox.com/books |
| Carrd | https://carrd.com/ | https://carrd.com/docs/pro/plans |
| Tally | https://tally.so/ | https://tally.so/pricing |
| Thomas Frank | https://thomasjfrank.com/ | https://thomasjfrank.com/brain/ |
| Joanna Penn | https://www.thecreativepenn.com/ | https://www.thecreativepenn.com/about/ |
| NerdWallet | https://www.nerdwallet.com/ | https://www.nerdwallet.com/our-partners |
| The Points Guy | https://thepointsguy.com/ | https://thepointsguy.com/about |
| Beardbrand | https://www.beardbrand.com/ | https://www.beardbrand.com/collections/all-products-collection |
| Ugmonk | https://ugmonk.com/ | https://ugmonk.com/ |
| Designjoy | https://www.designjoy.co/ | https://www.designjoy.co/ |
| ManyPixels | https://www.manypixels.co/ | https://www.manypixels.co/pricing |

本轮对 12 个官方首页做了在线读取，均返回对应业务的公开主页。保留原 10 个证据链接的业务判断；商品在售或出现公开定价不等于销量、营收、净利润、团队规模获得独立审计。

## 验收边界
- 本分支不会单独证明 Cloudflare 控制台当前构建设置未改变；合并之前须另行核查 Pages 输出仍是 `web/dist`。
- 主站安全路径与新版功能仍需合并后线上回归。
- 真实 iPhone Safari、历史 Pages 预览部署、真实财务验证仍未完成，不填写 PASS。
- PR #52 和 Supabase Production/Auth 完全不在本次修改范围。
