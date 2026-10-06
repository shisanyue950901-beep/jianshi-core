# 见势 R5 稳定访问兜底｜2026-10-06

## 背景
Cloudflare Pages 的哈希预览部署已经可用，但固定项目域名仍出现 404。
TinyFish 浏览器分配多次卡在 Waiting for browser，因此不把浏览器自动化放在关键路径。

## 处理
新增 Supabase Edge Function：
- name: jianshi-web
- auth: public read-only
- data source: existing public-feed only
- no service-role key in browser
- cache: public max-age 120 / s-maxage 300

## Production
Stable URL:
https://dalfvgehosxfyxkptxwx.supabase.co/functions/v1/jianshi-web

Detail:
https://dalfvgehosxfyxkptxwx.supabase.co/functions/v1/jianshi-web?slug=solo-saas

## 验收
- 首页 HTTP/HTML: PASS
- 品牌“见势”: PASS
- 标语“看见正在发生的生意机会”: PASS
- 174 marketplace listings: PASS
- 195 GitHub repositories: PASS
- multi-source opportunity: PASS
- solo-saas detail: PASS

## 定位
这是稳定访问兜底，不替代 Cloudflare Pages 的最终 SEO 静态站。
Cloudflare 哈希预览仍用于静态站验收；固定 alias 后续独立修复。
