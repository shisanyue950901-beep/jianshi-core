# P3.1 商业证据质量 Shadow 模型 Production 验收

日期：2026-10-07

## 结论

```
P31_CODE = PASS_MAIN
P31_PR = PASS_MERGED_36
P31_CI = PASS_RUN_99
P31_STAGING_MIGRATION = PASS
P31_STAGING_FAIL_CLOSED = PASS
P31_PRODUCTION_MIGRATION = PASS
P31_PRODUCTION_FAIL_CLOSED = PASS
P31_OPP_V02_UNCHANGED = PASS
P31_PUBLIC_READY_UNCHANGED = PASS
P31_FINAL = PASS_PRODUCTION_SHADOW
```

## 核心冻结

Quality 与 Legal Eligibility 分离：

- S/A/B 质量等级不授予自动采集权。
- Shadow 权重不进入 OPP_V0.2。
- 非 GREEN 来源 contribution = 0。
- Evidence Class 与 public_ready 规则未修改。

## 新增候选

- Quiet Light：S / YELLOW / auto_collect=false / redisplay_allowed=false
- StartupMKT：A / YELLOW / auto_collect=false / redisplay_allowed=false

两者都只进入授权研究队列，不进入 Production 数据采集。

## Production Shadow 实测

当前所有可用商业证据均只来自 `empire_flippers`：

- affiliate-content: 16 eligible commercial evidence / 1 GREEN source / quality weight 1.000
- creator-media: 33 / 1 / 1.000
- ecommerce-brands: 107 / 1 / 1.000
- solo-saas: 6 / 1 / 1.000
- ai-agent-tools: 0
- llm-tools: 0

`eligible_source_codes` 对存在商业证据的机会均仅为 `["empire_flippers"]`。

## OPP_V0.2 回归

Production 当前四维分数与 0044 上线前冻结值一致：

- affiliate-content: 51.76 / 71.99 / 59.56 / 81.60 / public_ready=true
- ai-agent-tools: 77.90 / 87.26 / 59.12 / 37.27 / public_ready=false
- creator-media: 75.89 / 84.95 / 78.05 / 80.18 / public_ready=true
- ecommerce-brands: 78.23 / 80.40 / 65.38 / 76.22 / public_ready=true
- llm-tools: 87.90 / 90.36 / 62.12 / 40.77 / public_ready=false
- solo-saas: 54.54 / 72.54 / 66.47 / 73.04 / public_ready=true

## GREEN 扫描

本轮没有发现第二个与 Empire Flippers 同级、且明确公开允许第三方 syndication 的高质量在线业务交易市场。

- Empire Flippers 仍是唯一明确 GREEN 基线。
- CatchBuys 虽提供 REST API，但上游包含 Flippa、Microns 等受限来源，继续受 provenance gate 阻断。
- Quiet Light 与 StartupMKT 都具有较高数据价值，但未验证第三方商业数据许可，因此保持 YELLOW。

## 安全

新增 `commercial_source_quality_rules` 为 service-role-only 内部表：
- RLS enabled
- no anon/authenticated policy
- Security Advisor 仅新增预期的 `rls_enabled_no_policy` INFO
- 未出现新的高严重级别安全错误
