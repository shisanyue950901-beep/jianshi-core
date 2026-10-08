# P4.13｜首批海外商业资源库扩容

状态：CONTENT_REVIEW_READY / PUBLISH_ONLY_AFTER_CI  
资料复核：2026-10-09

## 为什么从两家扩展到十二家

见势此前只有 2 家具名海外项目 + 6 种商业模式。为了从展示页成为真正可用的项目信息产品，这轮新增 10 家有独立官方业务说明或商品目录的具名案例，扩充为 **12 家具名企业/创作者 + 6 类模式**。

**重要：这不是把匿名挂牌样本反推为特定企业，不是 12 家确认盈利的公司，更不是单人创业成功案例库。** 所有新资料均独立来自第一方官网。

## 新增与官方来源

| 分类 | 新增项目 | 第一方核对页面 | 可核实的范围 |
|---|---|---|---|
| SaaS | Carrd | https://carrd.com/docs/pro/plans | 一页网站工具、Pro 分级和提供的专业功能 |
| SaaS | Tally | https://tally.so/pricing | 表单产品、免费入口、Pro/Business 收费层级 |
| 数字产品 | Thomas Frank / Ultimate Brain | https://thomasjfrank.com/brain/ | Notion 模板商品、一次购买及售后支持 |
| 出版 | Joanna Penn | https://www.thecreativepenn.com/about/ | 作者本人官方介绍、图书与创作出版业务 |
| 内容与联盟营销 | NerdWallet | https://www.nerdwallet.com/our-partners | 广告合作与内容商业关系披露 |
| 内容与联盟营销 | The Points Guy | https://thepointsguy.com/about | 推荐佣金、旅行内容与赞助合作 |
| 电商 | Beardbrand | https://www.beardbrand.com/collections/all-products-collection | 男性护理商品目录及公开报价 |
| 电商 | Ugmonk | https://ugmonk.com/ | Analog 纸质效率产品与零售商品 |
| 专业服务 | Designjoy | https://www.designjoy.co/ | 设计订阅、服务范围与交付计划 |
| 专业服务 | ManyPixels | https://www.manypixels.co/pricing | 设计订阅套餐、需求队列和团队流程 |

补充第一方交叉核对：
- https://tally.so/features
- https://thomasjfrank.com/templates/
- https://www.thecreativepenn.com/
- https://thepointsguy.com/legal/advertising-policy
- https://ugmonk.com/pages/analog
- https://www.manypixels.co/help/how-manypixels-works

不得将目录标价换算为收入、团队人数或净利润；内容平台合作方支付广告费亦不能推导其某期实际佣金。

## 前端呈现

- 保留 **纯黑 + Playfair Display / Inter + 品牌开屏 + 3D 拖动环 8 张概念封面**，不把 18 张图片强行放入环中；
- 8 张精选概念图片仍只表示项目主题，非原公司产品截图；
- 10 份新增内容作为「继续探索真实的海外生意」图文编辑列表，无需下载新的外链图片；
- 搜索功能对全部 18 项内容生效；按具体项目筛选会展示 12 家，按商业模式筛选展示 6 类；
- 每份新增企业档案包括卖什么、买家是谁、如何收费、日常经营、成本、公开核实事实、未知事实、研究重点及直达官方页面的链接；
- 公开链接仅指向已研究的企业本人官网，没有包含受保护的内部挂牌供应渠道；
- 保留 hash #item-xxx 深链接、键盘、灯箱、手机布局和 reduced motion。

## 下一阶段

目前这一批是**官网级事实核对**，不等于经营财务审计。后续应该在 CMS 或受控编辑表中引入：
- 逐项可追溯的事实级证据链接和最后复核日期；
- 经营规模的真实性分级（公开报告、自述、无法确认）；
- 不同类目的可比较字段、更多真实交付实例及筛选；
- 用户自选收藏、同类更多项目的内容链路（先产品设计验证，不立即采集个人数据）。

生产发布以 GitHub 完整 CI、Cloudflare 预览 / 线上 smoke test 和回滚能力为门槛。
