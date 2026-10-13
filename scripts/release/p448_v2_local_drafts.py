#!/usr/bin/env python3
"""P4.48: Browser-only, no-account V2 preparation tools.

These are NOT live enterprise orders, creator enrollment or CRM.
User text is NEVER POSTed, stored, logged, sent to third-party JavaScript,
serialized into site analytics or echoed into a remote endpoint.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from p446_content_hubs import CSS, SITE
from f21_design_tokens import render_css as render_design_css
from f21_components import site_header, site_footer

PAGES = ("marketplace/brief/", "talent/portfolio/")

# Field IDs/labels are fixed, generated offline and never accepted from URLs.
SPEC = {
    "marketplace/brief/": {
        "title": "写下你的企业需求",
        "kicker": "ENTERPRISE REQUEST / LOCAL DRAFT",
        "description": "把你想解决的问题、预算和交付内容写清楚。这里不会提交订单。",
        "back": "/marketplace/",
        "back_label": "返回商机大厅",
        "fields": (
            ("project", "项目名称（可使用代号）", "例如：电商新品视觉制作", 80),
            ("scene", "业务场景与当前问题", "你希望改变哪个实际流程？", 700),
            ("goal", "预期成果及使用场景", "希望拿到什么成果、用于哪些渠道？", 700),
            ("assets", "已有素材及授权情况", "仅描述素材种类；不要填写客户私密数据。", 500),
            ("delivery", "最终要交付什么？", "需要几张图、几个视频、什么格式，怎样才算完成？", 700),
            ("timeline", "时间安排与预算约束", "填写大致周期或预算范围即可。", 350),
            ("risk", "保密、合规及人工审核要求", "哪些材料不能对外公开？谁负责确认成果？", 500),
        ),
        "header": "见势 JIANSHI｜企业需求准备草稿（未提交）",
    },
    "talent/portfolio/": {
        "title": "整理你的作品介绍",
        "kicker": "CREATOR PORTFOLIO / LOCAL DRAFT",
        "description": "整理你会做什么、做过什么和想怎样合作。这不是入驻申请。",
        "back": "/talent/",
        "back_label": "返回人才与服务商",
        "fields": (
            ("skill", "技能方向与擅长场景", "例如：AI 电商视觉、AI 视频、Agent 工作流。", 200),
            ("sample", "代表作品或演示项目（可匿名）", "使用概念项目描述，不填写未授权客户信息。", 450),
            ("problem", "作品想解决的问题", "说明目标、使用场景或用户难点。", 450),
            ("contribution", "哪些部分是你自己做的？", "说清你自己完成的部分，以及哪些使用了 AI。", 500),
            ("outcome", "交付内容与演示结果", "例如：样片、图片组合、测试流程；不编造成交数据。", 450),
            ("permission", "版权、素材和隐私授权边界", "是否能公开、有哪些限制、是否仅为练习。", 450),
            ("method", "合作方式和验收说明", "可完成的工作、沟通节点及复核方式。", 350),
        ),
        "header": "见势 JIANSHI｜创作者作品集准备草稿（未提交）",
    },
}

# Keep inline browser logic constrained: no API connections, persistence,
# redirects, credential handling or client-side HTML interpolation.
SCRIPT = r"""
(function () {
  'use strict';
  const root = document.getElementById('draft-tool');
  if (!root) return;
  const inputs = Array.from(root.querySelectorAll('textarea[data-draft-field]'));
  const output = document.getElementById('draft-preview');
  const message = document.getElementById('draft-status');
  const generate = document.getElementById('draft-generate');
  const copy = document.getElementById('draft-copy');
  const clear = document.getElementById('draft-clear');
  const heading = root.getAttribute('data-heading') || '见势｜本地草稿';
  const progressBar = document.getElementById('draft-progress-bar');
  const update = function () {
    const entered = inputs.filter(function (item) { return item.value.trim().length > 0; });
    document.getElementById('draft-progress').textContent =
      String(entered.length) + ' / ' + String(inputs.length) + ' 项已填写';
    progressBar.style.width = String(Math.round(entered.length / inputs.length * 100)) + '%';
    return entered;
  };
  inputs.forEach(function (item) { item.addEventListener('input', update); });
  generate.addEventListener('click', function () {
    const entered = update();
    if (entered.length === 0) {
      message.textContent = '请至少填写一个项目内容，然后生成草稿。';
      output.textContent = '';
      copy.disabled = true;
      return;
    }
    const lines = [heading, '', '说明：此文档仅保存在当前浏览器页面；并未提交给见势平台。', ''];
    inputs.forEach(function (item) {
      lines.push('【' + item.getAttribute('data-label') + '】');
      lines.push(item.value.trim() || '（待补充）');
      lines.push('');
    });
    output.textContent = lines.join('\n');
    copy.disabled = false;
    message.textContent = '已在本页面生成草稿。离开或刷新页面后需要重新填写；请自行复制保存。';
  });
  copy.addEventListener('click', async function () {
    if (!output.textContent.trim()) return;
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(output.textContent);
      message.textContent = '草稿已复制到剪贴板。请存入你自己控制的安全位置。';
    } catch (_error) {
      message.textContent = '当前浏览器不支持自动复制，请手动选中下方草稿进行复制。';
    }
  });
  clear.addEventListener('click', function () {
    inputs.forEach(function (item) { item.value = ''; });
    output.textContent = '';
    copy.disabled = true;
    update();
    message.textContent = '页面输入已清空。';
    inputs[0].focus();
  });
  update();
}());
"""

CSS_EXTRA = """
.tool-layout{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:18px;align-items:start}
.tool-panel{padding:25px;border:1px solid #e0e7f3;border-radius:18px;background:white}
.tool-panel h2{font-size:24px;margin:0 0 8px}.tool-panel p{color:#64748b;font-size:13px;margin:0 0 22px}
.tool-field{margin:20px 0}.tool-field label{font-size:13px;color:#263653;font-weight:750;display:block;margin-bottom:6px}
.tool-field textarea{width:100%;min-height:92px;resize:vertical;border:1px solid #cbd5e6;border-radius:11px;font:14px/1.65 "PingFang SC","Microsoft YaHei",system-ui,sans-serif;padding:11px 12px;background:#fbfcff;color:#16243b}
.tool-field textarea:focus{outline:3px solid #aebcf9;border-color:#7c8ce5}
.tool-actions{display:flex;flex-wrap:wrap;gap:9px;margin:20px 0}
.tool-actions button{cursor:pointer;min-height:43px;border:1px solid #b2bfda;background:#fff;color:#334261;border-radius:10px;padding:10px 14px;font-size:13px;font-weight:750}
.tool-actions .primary{color:white;border-color:transparent;background:linear-gradient(110deg,#826bea,#4f8cfb)}
.tool-actions button:disabled{opacity:.46;cursor:not-allowed}
.tool-preview{white-space:pre-wrap;word-break:break-word;border:1px dashed #b9c6df;border-radius:12px;padding:18px;background:#f5f7fc;font-size:13px;line-height:1.8;min-height:210px;color:#283951}
.tool-status{font-size:12px!important;color:#575db2!important;min-height:20px}
.tool-help{font-size:12px;color:#74829d}
.tool-progress{display:inline-block;background:#edeaff;border-radius:99px;padding:4px 10px;font-size:11px;color:#6a5cbc;margin:0 0 12px}
@media(max-width:810px){.tool-layout{grid-template-columns:1fr}.tool-panel{padding:19px}}
"""



B1_DRAFT_VISUAL_CSS = """
.tool-hero{isolation:isolate;background:radial-gradient(ellipse 40% 120% at 91% 8%,#6753b361,transparent 80%),radial-gradient(ellipse 45% 100% at 2% 100%,#23649c5f,transparent 75%),linear-gradient(130deg,#0a1324,#142440 73%,#1b1f45)}
.tool-hero:after{content:"";position:absolute;inset:0;z-index:0;pointer-events:none;background:linear-gradient(#9cb8ff0d 1px,transparent 1px),linear-gradient(90deg,#9cb8ff0d 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(90deg,transparent,#0009)}
.tool-hero .wrap{position:relative;z-index:1;padding:34px 0 39px}
.tool-hero .kicker{margin-top:14px;background:#8984f126;border-color:#9b9ff15c}
.tool-hero h1{font-size:clamp(33px,4.5vw,52px);margin:14px 0 11px}
.tool-hero p{font-size:clamp(14px,1.55vw,17px);line-height:1.7;max-width:690px}
.tool-hero .hero-links{margin-top:22px}
.draft-hero-badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
.draft-hero-badges span{display:inline-flex;align-items:center;min-height:29px;border-radius:30px;padding:5px 11px;border:1px solid #aabaf554;background:#e0e5ff13;color:#d4dff5;font-size:11px}
.draft-content{padding-top:27px}
.draft-content #draft-privacy{border-left-color:#7869d5;background:linear-gradient(110deg,#f0edff,#ecf4ff);border-radius:14px;color:#4d5473;margin-bottom:20px}
.tool-layout{gap:21px;scroll-margin-top:91px;grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr)}
.tool-layout .tool-panel{border:1px solid #dfe6f3;background:linear-gradient(180deg,#fff,#fbfcff);border-radius:20px;padding:26px;box-shadow:0 8px 28px #273d7010;min-width:0}
.tool-panel h2{font-size:25px;letter-spacing:-.035em;color:#1a2b48}
.tool-panel>p{line-height:1.75}
.tool-panel .tool-progress{background:#f0ecff;color:#5d54b9;display:inline-flex;font-weight:800;padding:7px 12px}
.tool-progress-track{height:7px;border-radius:9px;background:#edf0f8;overflow:hidden;margin:0 0 27px}
.tool-progress-track span{display:block;width:0;height:100%;border-radius:9px;background:linear-gradient(90deg,#8162eb,#5f93f5);transition:width .25s}
.tool-fields{counter-reset:field}
.tool-fields .tool-field{counter-increment:field;margin:19px 0}
.tool-fields .tool-field label{font-size:13px;color:#283b5a;line-height:1.65}
.tool-fields .tool-field label:before{content:counter(field, decimal-leading-zero);display:inline-grid;place-items:center;min-width:26px;height:24px;padding:0 4px;border-radius:8px;background:#f0edff;color:#655ac5;font-size:10px;font-weight:850;margin-right:10px}
.tool-field textarea{background:#f9faff;border:1px solid #d4deef;border-radius:12px;min-height:102px;padding:13px 14px;font-size:14px;line-height:1.7;transition:background .2s,border-color .2s}
.tool-field textarea:focus{background:#fff;border-color:#8179e7;outline:3px solid #d6d0ff;outline-offset:1px}
.tool-field textarea::placeholder{color:#8b99af}
.tool-actions button{border-radius:11px;min-height:46px}
.tool-actions button:hover:not(:disabled){border-color:#8f82ed;box-shadow:0 6px 17px #4e5ab11e}
.tool-actions button:focus-visible{outline:3px solid #a79afd;outline-offset:3px}
.tool-actions .primary{box-shadow:0 9px 21px #7160ce23}
.tool-preview{background:repeating-linear-gradient(180deg,#f9fbff,#f9fbff 34px,#f3f6fd 35px);border:1px dashed #b8c7e6;min-height:280px;padding:21px;line-height:1.85;border-radius:15px;color:#243958}
.tool-preview:empty::before{content:attr(data-placeholder);color:#8493ac;display:block;text-align:center;white-space:pre-line;line-height:2;max-width:220px;margin:66px auto 0;font-size:13px}
.tool-status{padding:11px 13px;background:#f0effd;border-radius:11px;min-height:40px!important;line-height:1.65}
.tool-help{line-height:1.65}
@media(min-width:811px){.tool-layout>.tool-panel:last-child{position:sticky;top:88px}}
@media(max-width:810px){.tool-layout{grid-template-columns:1fr}.tool-layout>.tool-panel:last-child{position:static}.tool-layout .tool-panel{padding:21px}}
@media(max-width:650px){.tool-hero .wrap{padding:25px 0 29px}.tool-hero h1{font-size:clamp(31px,8vw,42px)}.tool-hero:after{background-size:33px 33px}.draft-content{padding-top:21px}.draft-hero-badges span{font-size:10px}.tool-layout .tool-panel{padding:19px}.tool-preview{min-height:235px}.tool-preview:empty::before{margin-top:42px}}
@media(prefers-reduced-motion:reduce){.tool-field textarea,.tool-progress-track span{transition:none}}
"""


def e(raw: str) -> str:
    return escape(raw, quote=True)


def render_one(route: str) -> str:
    if route not in SPEC:
        raise ValueError("Only two explicitly reviewed draft tools are public")
    d = SPEC[route]
    fields = "".join(
        '<div class="tool-field"><label for="draft-' + key + '">' + e(label)
        + '</label><textarea data-draft-field data-label="' + e(label)
        + '" id="draft-' + key + '" maxlength="' + str(length)
        + '" placeholder="' + e(hint) + '" aria-describedby="draft-privacy"></textarea></div>'
        for key, label, hint, length in d["fields"]
    )
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="index,follow">'
        '<title>' + e(d["title"]) + '｜见势 JIANSHI 2.0</title>'
        '<meta name="description" content="' + e(d["description"]) + '">'
        '<link rel="canonical" href="' + SITE + '/' + route + '">'
        '<meta name="referrer" content="no-referrer">'
        '<style>' + CSS + CSS_EXTRA + render_design_css() + B1_DRAFT_VISUAL_CSS + '</style></head><body>'
        + site_header("/" + route)
        + '<main><div class="hero tool-hero"><div class="wrap">'
        '<div class="crumb"><a href="/">见势首页</a> / <a href="' + d["back"] + '">'
        + e(d["back_label"]) + '</a> / 本地草稿工具</div>'
        '<span class="kicker">仅在当前页面整理</span>'
        '<h1>' + e(d["title"]) + '</h1><p>' + e(d["description"]) + '</p>'
        '<div class="draft-hero-badges" aria-label="本地工具数据说明">'
        '<span>不需注册</span><span>不上传数据</span><span>关闭页面即消失</span></div>'
        '<div class="hero-links"><a class="btn primary" href="#draft-tool">开始整理 ↗</a>'
        '<a class="btn" href="' + d["back"] + '">' + e(d["back_label"]) + ' ↗</a></div>'
        '</div></div><div class="wrap content draft-content">'
        '<div class="status" id="draft-privacy"><b>注意：</b>这里不会上传或保存你写的内容。'
        '关闭或刷新页面后内容会消失，请先复制保存。不要填写密码、客户隐私或商业秘密。'
        '目前还不能在这里发布订单或申请入驻。</div>'
        '<section class="tool-layout" id="draft-tool" data-heading="' + e(d["header"]) + '">'
        '<div class="tool-panel"><h2>整理关键内容</h2>'
        '<p>不要求提供企业真实名称或个人联系方式。可用匿名代号起草。</p>'
        '<div class="tool-progress" id="draft-progress" aria-live="polite">0 / '
        + str(len(d["fields"])) + ' 项已填写</div>'
        '<div class="tool-progress-track" aria-hidden="true"><span id="draft-progress-bar"></span></div>'
        '<div class="tool-fields">' + fields + '</div>'
        + '<div class="tool-actions"><button type="button" id="draft-generate" class="primary">生成本地草稿</button>'
        '<button type="button" id="draft-clear">清空内容</button></div></div>'
        '<div class="tool-panel"><h2>草稿预览</h2>'
        '<p>草稿只在当前页面生成。复制后请自行保存在可控的位置；没有上传或发布按钮。</p>'
        '<div class="tool-actions"><button type="button" id="draft-copy" disabled>复制草稿</button></div>'
        '<p id="draft-status" class="tool-status" role="status" aria-live="polite">填写后点击“生成本地草稿”。</p>'
        '<div class="tool-preview" id="draft-preview" aria-label="本地草稿预览"'
        ' data-placeholder="你的草稿会在这里呈现。&#10;填写后点击“生成本地草稿”。"></div>'
        '<p class="tool-help">此工具不是招聘、交易或电子签约系统，不产生任何平台订单记录。</p></div>'
        '</section></div></main>'
        + site_footer() + '<script>' + SCRIPT + '</script></body></html>\n'
    )


def publish(output: Path) -> int:
    for route in PAGES:
        html = render_one(route)
        if (html.count("<main>") != 1 or html.count("<script>") != 1
                or html.count('data-draft-field data-label=') != 7
                or "fetch(" in html or "localStorage" in html
                or "XMLHttpRequest" in html or "sendBeacon" in html
                or "WebSocket" in html or "action=" in html):
            raise RuntimeError("V2 local-only privacy or markup contract violated")
        target = output / route / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
    return len(PAGES)
