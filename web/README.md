# 见势 R5 静态站

P0/R5 为降低成本，不引入前端运行时服务器。

构建方式：
```
python web/build.py
```

默认使用 `web/fixtures/api.json`，CI 不依赖外部网络。
部署构建时设置：

```
JIANSHI_API_URL=https://<project>.supabase.co/functions/v1/public-feed
```

输出目录：`web/dist/`

设计原则：
- 静态 HTML，Cloudflare Pages 可直接托管
- 首页与机会详情可被搜索引擎抓取
- 不向浏览器暴露数据库 Service Role
- 只读取 R5 public-feed API
- “机会”与“单源观察”必须明确区分
