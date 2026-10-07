# P3.2 中国个人创业者机会解释层

日期：2026-10-07

## 产品定位

见势当前验证的不是“中国版交易平台”，而是：

> 获取国外真实商业机会与趋势，为中国个人创业者提供更好的项目发现、创业判断和行动咨询。

因此当前阶段只做**信息解释与决策支持**，不做用户画像工程、不做个人信息体系重构，也不为了中国本地部署或跨境数据问题打断产品验证。

## 当前明确后置

以下工作后置到产品验证成立、准备正式扩大账号/订阅能力时再处理：

- 中国用户个人信息体系
- 中国大陆本地化部署
- 跨境个人信息专项设计
- ICP / 大陆服务器方案
- 大规模用户画像和推荐系统

现有 Auth 仍保持关闭；Newsletter 仍保持 fail-closed / WAITLIST 策略。

## 当前主线

国外真实信息
→ 技术趋势 / 商业交易 / 产品需求 / 市场变化
→ 证据交叉
→ 中国个人创业者解释层
→ 这个项目值不值得关注？
→ 中国人能不能做？
→ 更适合国内还是出海？
→ 一个人能不能做？
→ 第一步应该怎么验证？

## 解释层字段

P3.2 建立内部字段，但不自动编造内容：

- recommended_market：更适合中国 / 全球 / 两边 / 未知
- opportunity_translation：把海外机会翻译成中国创业者语言
- why_it_matters_for_china_founder：为什么值得中国个人创业者关注
- domestic_execution_path：国内路径
- global_execution_path：出海路径
- capital_intensity：资金强度
- mvp_complexity：MVP 复杂度
- acquisition_difficulty：获客难度
- localization_needs：本地化需求
- execution_steps：建议验证步骤
- risk_notes：风险提示
- evidence_refs：支撑这些判断的证据引用
- confidence：置信度
- review_status：DRAFT / REVIEWED / PUBLISHED

## 关键规则

1. 不因为“面向中国创业者”而修改 OPP_V0.2 四维评分。
2. 不因为编辑判断而改变 public_ready。
3. 不用主观推断填充成本、周期、收入等数字。
4. 任何对外解释必须能回到可审计证据。
5. DRAFT 默认不公开。
6. 只有明确 PUBLISHED + reviewed_at 才能进入未来公共投影。
7. P3.2 不采集任何用户个人信息。

## 当前状态

本轮只搭解释层的数据契约和 fail-closed 公共投影，不批量生成创业建议，不改变现有网站排名和机会状态。

下一阶段先选 1～2 个机会做人工高质量样板，再决定是否把“中国创业者解读”模块正式放到机会详情页。