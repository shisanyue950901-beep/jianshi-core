# P4.12E｜原摄影模板融合单文件站点（隔离预览）

状态：PREVIEW_ONLY / PRODUCTION_UNCHANGED

## 目标

将用户提供的 `ethan-vale-template.html` 视觉与交互套入见势当前已审阅内容。

**原模板约束：** 黑色 `#000`、Playfair Display + Inter 原 Google Fonts 链接、原样保留重要 CSS 变量、品牌开屏、菜单、3D 照片环、网格画廊、全屏灯箱、滚动淡入、偏好减少动画、iPhone viewport/safe-area/dvh。无框架、无第三方 JS、无需构建工具。

## 本轮完成

- `web/prototypes/p412e/index.html`：完整独立 HTML，单个 style/script，8 张内嵌商业概念封面，不需要目录图片；
- 两份具名案例（Easlo、Louise Lennox）与六类商业模式，严格分离身份；
- 拖动惯性、自动旋转、键盘、灯箱手机滑动、点击与拖动阈值；
- 搜索/筛选、两至三类商业模式对比、项目详细信息；
- 修复筛选点击误触：原选择器会将带 data-kind 的项目卡片也错误绑定为过滤按钮；已收窄至 `.find__filters [data-kind]`；
- 修复筛选后的灯箱：不再翻到隐藏内容；单条结果的左右箭头禁用；
- 首次打开灯箱同步填充当前图文，避免先空白等待；
- 详情页有独立 `#item-<id>` 地址和历史前进/后退恢复；
- 封面压缩并内嵌 WebP，便于独立文件分发；不使用真实企业照片冒充来源证明。

## 本地浏览器检查

Chromium + Playwright 自测：

- 桌面 1440px、iPhone 宽度 390px、320px；
- `prefers-reduced-motion` 模式；
- 搜索/恢复、灯箱前后切换、过滤后单项目边界、项目详情跳转、历史前进/后退、菜单 Esc、横向溢出、页面 JS 异常。

还未完成的检查：

- 真实 iPhone Safari 的动态地址栏和安全区（模拟器读到 safe-area=0，不可充作真机验证）；
- 生产 Cloudflare Pages 发布目录需要明确锁定静态输出，历史根目录泄漏及旧部署仍须清理；
- 概念封面替换成确认许可的项目视觉素材；
- 提供正式联系邮箱后才能展示真实联系入口；
- 项目内容目前 2 个具名例子并没有财务业绩核实，不得扩称为完整数据库；
- 与生产官网模板 `web/build.py` 的正式接入仍待用户视觉验收。

```text
P412E_SINGLE_HTML = PASS
P412E_BROWSER_CHROMIUM = PASS
P412E_TRUE_SAFARI = PENDING
P412E_DATA_PRIVACY = PASS_STATIC_AUDIT
P412E_CLOUDFLARE_OUTPUT_FIX = PENDING
P412E_PUBLICATION = FALSE
P412E_PR65 = PREVIEW_OPEN_NOT_MERGED
```
