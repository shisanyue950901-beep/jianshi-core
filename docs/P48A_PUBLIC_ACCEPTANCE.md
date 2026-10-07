# P4.8A｜正式上线验收

日期：2026-10-07  
最终状态：PASS_USER_TEST_READY

## GitHub

```text
PR56 = MERGED
MERGE_SHA = 40c1d8e5272a13a88f208e8b1937695df933a5fb
PREMERGE_CI = PASS_RUN_202
POSTMERGE_CI = PASS_RUN_203
STATIC_SNAPSHOT = PASS_RUN_69
LATEST_STATIC_SNAPSHOT_SHA = 6454831ec6620badf7ea90bf22dc065e0e6a05db
```

PR #52 仍保持 OPEN / NOT_MERGED。

## 公开站验收

首页已经真实显示：

- 海外已验证项目 · 中文筛选
- 海外项目 → 商业证据 → 中国适配 → 低成本验证
- 首批 6 个具体项目研究
- 105 个直接商业样本
- 1 类商业来源
- 5 个优先研究项目

/opportunities/ 已分成：

1. 首批项目研究
2. 趋势方向 · 辅助观察

旧 OPP_V0.2 四维评分保留为趋势辅助层，没有删除、篡改或静默换分。

## 详情页验收

抽查：

- vertical-industry-saas
- amazon-fba-niche-brand
- digital-product-business

均确认：

- 页面可访问
- 中文研究内容正确
- robots = noindex,nofollow
- 返回首批项目入口存在
- “继续比较”模块已进入 Production 静态快照
- related project links 已实际生成

## 索引边界

正式线上：

```text
PROTOTYPE_IN_SITEMAP = FALSE
PROTOTYPE_IN_SEARCH_INDEX = FALSE
PROTOTYPE_ROBOTS = noindex,nofollow
```

sitemap.xml 仍只有旧正式索引页，不包含 6 个首批项目 slug。  
search-index.json 仍只包含旧趋势机会，不包含 6 个首批项目 slug。

## Production 数据

本阶段：

```text
PRODUCTION_SCHEMA_CHANGE = FALSE
PRODUCTION_DML_CHANGE = FALSE
AUTH_GATE_CHANGE = FALSE
PR52_MERGE = FALSE
```

仅执行行为事件只读查询。

## 正式用户测试 Epoch

上线及内部 QA 完成后，行为库仍保持：

```text
TOTAL_EVENTS = 68
UNIQUE_VISITORS = 2
UNIQUE_SESSIONS = 3
NEW_PROJECT_EVENTS = 0
```

因此正式测试 Epoch 冻结为：

```text
P48A_USER_TEST_EPOCH_START = 2026-10-07T15:49:06Z
```

从该时间点之后的数据才进入 P4.8B 真实用户报告。

## 最终冻结

```text
P48A_PUBLIC_PATH = PASS
P48A_HOME_ENTRY = PASS
P48A_CATALOG_ENTRY = PASS
P48A_DETAIL_CONTINUATION = PASS
P48A_NOINDEX_BOUNDARY = PASS
P48A_ANALYTICS_EPOCH = PASS
P48A_FINAL = PASS_USER_TEST_READY
```
