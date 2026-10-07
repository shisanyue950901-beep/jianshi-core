# 见势 R8.7｜证据类别 Gate

## 为什么升级
当前主要证据只有 GitHub 与 Empire Flippers，因此早期的 source_count>=2 基本等价于：
技术趋势 + 商业市场。

未来新增 Hacker News、Product Hunt、App Store、搜索趋势或其他 API 后，这个等价关系会失效。

例如：
GitHub + Hacker News
虽然是两个来源，但都不能证明真实商业价值。

## 新规则
公开“已验证机会”必须同时满足：
1. TECHNICAL_SUPPLY > 0
2. COMMERCIAL_PROOF > 0
3. active evidence_count >= 5

当前映射：
- GITHUB_REPOSITORY → TECHNICAL_SUPPLY
- MARKETPLACE_LISTING → COMMERCIAL_PROOF

未来新增证据类型必须显式登记 evidence_class_rules。
没有登记不会自动满足验证 Gate。

## 新字段
- technical_evidence_count
- commercial_evidence_count
- demand_evidence_count
- validation_class_count
- validation_class

validation_class：
- TECH_PLUS_COMMERCIAL
- COMMERCIAL_ONLY
- TECHNICAL_ONLY
- INSUFFICIENT

## 兼容
resonance_status 继续保留：
- MULTI_SOURCE：同时有技术 + 商业
- SINGLE_SOURCE：否则

这是为了不破坏已有 UI/API，但真正 public_ready 已不再依赖简单 source_count>=2。

## 产品表达
用户界面不再强调“两个来源”，改为：
“技术供给证据与真实商业证据同时支持。”

## 后续意义
之后可以安全接更多趋势/需求信号：
- Hacker News
- Product Hunt
- App Store
- 搜索趋势
- 授权交易市场 API

这些来源可以影响热度、内容价值、需求判断，但不能单独绕过 COMMERCIAL_PROOF Gate。
