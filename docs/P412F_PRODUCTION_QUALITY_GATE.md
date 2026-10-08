# P4.12F｜上线前质量门禁与未完成事项

状态：DEVELOPMENT_PASS / PRODUCTION_RELEASE_BLOCKED  
范围：`web/prototypes/p412e/index.html`，不修改正式 `web/build.py`

## 本次落实的质量修复

- 开屏、全屏菜单和灯箱打开时，使用 HTML `inert` 隔离背景焦点；关闭后恢复键盘交互与原滚动位置。
- 弹层的 Tab 焦点边界、Esc 关闭、左右方向键和触控滑动保持原交互，不更换视觉样式。
- 3D 环离开可视区域或页面切换到后台时停止 `requestAnimationFrame` 调度；重新可见时再启动，保留拖动惯性及自动缓慢旋转。
- 减少动态效果偏好下继续关闭自动动画。
- 前端视觉控制点不改变：纯黑背景、Playfair Display + Inter、8 张内嵌 WebP、开屏、3D 环、网格画廊及全屏灯箱。
- 按当前状态更新屏幕阅读器的前台序号，避免每帧重复写入 `aria-live` 内容。

## 验证范围

隔离环境已使用 Chromium 通过本地 HTML 注入方式检验：

- 桌面 1440×900：开屏结束、菜单/灯箱前台焦点隔离、搜素、过滤后单结果灯箱、对比、离开首屏停止动画、返回首屏恢复动画，无 JS 异常。
- 模拟手机 390×844、320×720、390×844 减少动态模式：图片载入、无横向溢出、菜单焦点隔离、搜索和 JS 错误检查通过。
- 模拟手机滚动到 y=1800 后打开/关闭菜单，滚动位置保持 y=1800。
- 单 HTML 的 JavaScript `node --check` 通过。
- CI 静态门禁：`tests/test_p412e_standalone_motion.py` 和 `tests/test_p412f_motion_quality.py`。

**不可混淆的限制：** 本轮环境阻止浏览器直接导航本地文件和本地 HTTP，因此采用 HTML 注入验证；这不等于实际部署后的链接/刷新/历史路由验收。真实 iPhone Safari 的动态地址栏及 safe-area 未经过真机测试。

## 正式发布的剩余阻断

1. **Cloudflare Pages 产物发布目录**：需要在管理后台把构建输出限定到安全的 `web/dist`；确认根目录文件不再可访问，并检查历史部署 URL、预览分支和缓存。此前设置了临时拦截，但不代表根本修复。
2. **上线集成**：当前新版仍在孤立预览，`web/build.py` 生产主页未替换。发布前需要审阅发布结构，不能把整个仓库当成静态公开目录。
3. **真机验收**：真实 Safari iPhone（顶部刘海、安全区、浏览器地址栏伸缩、键盘和灯箱手势）以及第二种桌面浏览器。
4. **资料与视觉审核**：8 张图片当前为**概念封面**，不能当成项目实景、商标或收入证据。具名案例不能宣称核实利润、销量或团队人数。
5. **联系邮箱**：尚未提供真实联系方式，独立预览明确暂不开放联系功能，不得填造邮箱。
6. **受控预览**：必须先经过固定预览域名的真实浏览器操作测试、隐私扫描和用户审阅，再申请正式站替换。

## 冻结结论

```text
P412F_SINGLE_FILE = PASS
P412F_CODE_SYNTAX = PASS
P412F_3D_PERFORMANCE_DESKTOP = PASS
P412F_DIALOG_FOCUS_DESKTOP = PASS
P412F_MOBILE_CHROMIUM_SMOKE = PASS
P412F_TRUE_IPHONE_SAFARI = PENDING
P412F_REAL_DEPLOYED_LINKS = PENDING
P412F_CLOUDFLARE_ROOT_DIRECTORY = PENDING
P412F_PRODUCTION_RELEASE = BLOCKED
```
