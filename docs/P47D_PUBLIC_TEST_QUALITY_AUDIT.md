# P4.7D｜PR #53 真实用户测试质量审计

日期：2026-10-07  
状态：PASS_PUBLIC_TEST_READY

## 本阶段目标

只审计 PR #53 的 6 个“海外已验证项目中文详情样板”是否达到真实中文用户测试质量。

本阶段不做：
- 新数据源扩展
- Production 数据库迁移
- 推荐算法扩展
- 渠道矩阵
- PR #52 合并
- PR #53 合并

## 远端基线复核

开始审计前已重新核对：

- main 最新静态快照：`5d7b8627f811e476e30e4a213755102a6c980370`
- PR #52：OPEN，Production 未应用 P4.5B-D
- PR #53：OPEN
- Supabase Staging / Production：ACTIVE_HEALTHY
- Staging migrations：已包含 0055–0059
- Production migrations：仍止于 0052
- Production auth.users：0
- Production auth_launch_gates：8 项全部 FALSE
- 当前公开网站仍以历史 6 个母赛道为主

## 审计范围

逐项检查：

1. 六个页面中文表达
2. 用户可见工程英文残留
3. 页面信息层级
4. 移动端布局
5. 推荐档位是否与候选池一致
6. 商业样本口径是否与 Production 严格口径一致
7. 海外验证证据是否直观
8. 是否存在过度承诺或把样本数误当来源数
9. 是否继续保持 noindex / 无 sitemap / 无站内搜索索引

## 发现并修复的问题

### 1. FBA 样本口径漂移

旧 Prototype：
- 直接商业样本：77
- 细分类目：34
- 口径：monetization 包含 Amazon FBA

重新按 Production 严格主标题口径复算：

- 亚马逊物流（FBA）细分品牌：69
- 严格样本中的不同细分类目：33
- 识别规则：公开主标题明确归类为 Amazon FBA Business
- 按挂牌项目去重

已修正为：
- `direct_samples = 69`
- `observed_niche_count = 33`

### 2. 用户可见内部英文

发现页面内容会直接显示：
- Production
- active listing
- listing
- 部分来源内部业务类型英文
- 英文 niche 分类

已改为中文用户可读表达，仅保留确有识别价值的品牌名 / 行业缩写，例如：
- SaaS
- FBA
- KDP
- SEO

所有展示用细分类目已中文化。

### 3. SaaS 推荐档位与 main 候选池不一致

main 候选池冻结：
- 垂直行业软件订阅服务（SaaS）
- 推荐：优先研究
- 一人 / 小团队适配：高

旧 Prototype：
- 推荐：值得研究
- 一人适配：中高

已对齐为：
- 推荐：优先研究
- 一人 / 小团队适配：高

## Production 严格样本复算

```text
垂直行业软件订阅服务（SaaS） = 4
亚马逊物流（FBA）细分品牌 = 69
数字产品业务 = 9
联盟营销 / 内容站 = 11
亚马逊 KDP 数字出版 = 8
垂直服务型业务 = 4
```

六项现已与 main 候选池一致。

## 页面结构与移动端

统一保持六问：

1. 见势推荐
2. 这个项目是什么
3. 海外真实验证
4. 对中国用户有没有参考价值
5. 第一轮怎么验证
6. 风险与未知

移动端现有 CSS：
- 900px 以下详情页双栏改为单栏
- 800px 以下证据卡改为单栏
- 移动端侧栏取消 sticky
- 未发现横向表格依赖

结论：无移动端发布阻断项。

## 回归保护

测试已新增：

- 六个详情页严格样本数锁定
- FBA 69 / 33 锁定
- 六个推荐档位锁定
- 用户可见内部英文拦截
- 展示分类必须包含中文
- FBA 构建页验证 69
- noindex / 无站内搜索索引继续保留

## CI

审计修复 head：

```text
ac770abc62cae34dbd641cebbc35153a12da48aa
```

GitHub Actions：

```text
JianShi CI #197 = PASS
```

## 发布 Gate

```text
P47D_COPY_AUDIT = PASS
P47D_EVIDENCE_ALIGNMENT = PASS
P47D_CHINESE_FIRST = PASS
P47D_MOBILE_LAYOUT = PASS
P47D_RECOMMENDATION_ALIGNMENT = PASS
P47D_REGRESSION_TESTS = PASS
P47D_CI = PASS_RUN_197

P47D_PUBLIC_TEST_QUALITY = PASS
P47D_PUBLICATION_GATE = READY_FOR_PUBLIC_TEST

PRODUCTION_DATA_CHANGE = FALSE
PR52_MERGE = FALSE
PR53_MERGE = FALSE

P47D_FINAL = PASS_PUBLIC_TEST_READY
```

## 冻结结论

PR #53 当前已经达到进入真实公开用户测试的内容质量门槛。

但按照“小阶段完成即冻结”的执行规则，本阶段只完成审计、修正、CI 与发布 Gate 判定，**不在本阶段自动合并 PR #53**。

下一小阶段如继续：

```text
MERGE PR53
→ 生成 / 核对最新静态快照
→ 公开站点验收
→ 开始真实中文用户测试
```
