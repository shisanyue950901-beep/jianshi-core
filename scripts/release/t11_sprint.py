#!/usr/bin/env python3
"""T11 public 30-day sprint handbook. Static HTML only; zero account or form data."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://jianshi-bua.pages.dev"
CHECKED = "2026-10-18"
OLD_PROMISE_WORDS = ("保证", "月入", "躺赚")

PROVIDERS = (
    {
        "name": "Creem",
        "individual": "支持个人注册；所在地须符合平台准入",
        "payout": "银行账户 / USDC 钱包（视账户及地区资格）",
        "fee": "标准 3.9% + $0.40 / 笔",
        "review": "身份或企业 KYC；产品及网站审核后方可正式收款",
        "sources": (
            ("官网费率", "https://www.creem.io/pricing"),
            ("个人注册和审核", "https://www.creem.io/"),
            ("商户条款", "https://www.creem.io/terms"),
        ),
        "detail": "官网价格页明确银行或USDC钱包提现；实际到账费、换汇及风控需以账户条款为准。",
    },
    {
        "name": "Dodo Payments",
        "individual": "个人注册资格因国家/地区及主体审核而异；统一准入范围未公开",
        "payout": "银行结算 / USD SWIFT（适用时）",
        "fee": "标准 4% + $0.40 / 笔；国际支付 +1.5%，订阅 +0.5%（适用时）",
        "review": "商户身份和业务准入审核；具体材料视注册地区和产品",
        "sources": (
            ("中文官网价格", "https://dodopayments.com/zh/pricing"),
            ("平台官网", "https://dodopayments.com/"),
        ),
        "detail": "官网价格页注明：常规结算免费；单次提现低于$1,000收$5；非美国商家USD SWIFT结算$25。均视适用条件而定。",
    },
    {
        "name": "Waffo Pancake",
        "individual": "支持个人开发者申请（No LLC Required）；国家/地区及产品须审查",
        "payout": "银行转账 / 支付宝（依地区及审核资格）",
        "fee": "标准 3.9% + $0.50 / 笔",
        "review": "商店信息、邮箱与 KYC、收款方式分步核验；本番使用另须获批",
        "sources": (
            ("官网费率", "https://www.waffo.ai/pricing"),
            ("提现与核验", "https://www.waffo.ai/en/features/finance"),
            ("日本审核声明", "https://www.waffo.jp/developers"),
        ),
        "detail": "官网可见 Bank / Alipay 及个人开发者路径；是否可在您的所在地启用及结算周期需个别审核。",
    },
)

WEEKS = (
    ("week0", "第 0 步 · 项目分诊", (
        "逐个填完五列分诊表，列出所有现有项目",
        "按五条淘汰规则完成筛选并保留第二名",
        "只选择一个项目，记下首批用户聚集地",
    )),
    ("week1", "第 1 周 · 能收钱", (
        "落地页六要素齐全：价值、功能、价格、条款、隐私、邮箱",
        "配置一条收款路径和备用申请，确认地区与审核资格",
        "沙盒测试支付成功一笔；正式收款须通过平台审核",
    )),
    ("week23", "第 2–3 周 · 找 20 个真人", (
        "记录目标用户社区、具体子版块或群名",
        "写并发布不硬推销、先给方法的价值帖",
        "联系 50 位匹配用户，目标取得 20 次真实对话",
        "每次直接给出产品购买链接或创始价",
        "对话记录去标识化，仅保留必要研究要点",
    )),
    ("week4", "第 4 周 · 收入可验证", (
        "在收款平台和 TrustMRR 官方后台完成只读/限权连接",
        "核对公开收入验证页是否真的可访问；未通过不得声称已验证",
        "完成选题、定价、渠道、转化与踩坑复盘",
    )),
)

def _escape(v: object) -> str:
    return html.escape(str(v), quote=True)

def _form_url(config_file: Path) -> str:
    if not config_file.is_file():
        raise ValueError("Missing required config/site.json")
    data = json.loads(config_file.read_text(encoding="utf-8"))
    value = data.get("diagnose_form_url", "")
    if not isinstance(value, str):
        raise ValueError("diagnose_form_url must be a string")
    value = value.strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    allowed = ("feishu.cn", "feishu.com", "larksuite.com")
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or not host or not any(host == suffix or host.endswith("." + suffix) for suffix in allowed)):
        raise ValueError("diagnose_form_url must be an HTTPS Feishu/Lark form URL")
    return value

def render_sprint(form_url: str, analytics_endpoint: str = "") -> str:
    if not isinstance(form_url, str):
        raise TypeError("form_url must be a string")
    form_url = form_url.strip()
    if form_url:
        # Defense-in-depth for direct render callers as well as JSON config.
        host = (urlsplit(form_url).hostname or "").lower()
        if urlsplit(form_url).scheme != "https" or not any(
                host == x or host.endswith("." + x)
                for x in ("feishu.cn", "feishu.com", "larksuite.com")):
            raise ValueError("Unsafe form URL")
        cta = (f'<a class="t11-btn t11-btn-primary" data-t11-diagnose '
               f'href="{_escape(form_url)}" target="_blank" rel="noopener noreferrer">'
               '提交我的项目诊断 ↗</a>')
    else:
        cta = '<button class="t11-btn t11-btn-disabled" type="button" disabled aria-disabled="true">表单即将开放</button>'
    checklist = []
    for key, name, items in WEEKS:
        labels = "".join(
            f'<label class="t11-task"><input type="checkbox" data-t11-check="{key}-{i}" '
            f'aria-label="{_escape(item)}"><span>{_escape(item)}</span></label>'
            for i, item in enumerate(items, 1)
        )
        checklist.append(
            f'<section class="t11-checkgroup"><h3>{_escape(name)}</h3>{labels}</section>'
        )
    providers = []
    for item in PROVIDERS:
        anchors = "<br>".join(
            f'<a target="_blank" rel="noopener noreferrer" href="{_escape(url)}">{_escape(label)} ↗</a>'
            for label, url in item["sources"]
        )
        providers.append(
            f'<tr data-t11-provider="{_escape(item["name"])}">'
            f'<th scope="row">{_escape(item["name"])}</th>'
            f'<td>{_escape(item["individual"])}</td>'
            f'<td>{_escape(item["payout"])}</td>'
            f'<td>{_escape(item["fee"])}</td>'
            f'<td>{_escape(item["review"])}</td>'
            f'<td>{anchors}<small>{_escape(item["detail"])}</small></td>'
            f'<td><time datetime="{CHECKED}">{CHECKED}</time></td></tr>'
        )
    analytics_url = str(analytics_endpoint or "").strip()
    if analytics_url and (urlsplit(analytics_url).scheme != "https" or "<" in analytics_url):
        analytics_url = ""
    analytics_json = json.dumps(
        {"enabled": bool(analytics_url), "endpoint": analytics_url},
        ensure_ascii=False, separators=(",", ":")
    ).replace("<", "\\u003c")
    style = r"""
:root{--s-ink:#162338;--s-muted:#586779;--s-line:#dfe5ed;--s-violet:#6257d4}
body{background:#f7f9fc} .t11{color:var(--s-ink)}
.t11-wrap{max-width:1140px;margin:auto;padding:0 22px}
.t11-top{background:#101c32;color:#eef2fb;border-bottom:1px solid #273652;position:sticky;z-index:10;top:0}
.t11-bar{display:flex;align-items:center;justify-content:space-between;gap:20px;min-height:66px}
.t11-brand{font-size:25px;font-weight:900;color:white}
.t11-brand span{font-size:11px;font-weight:600;letter-spacing:.15em;margin-left:9px;color:#b7c2d9}
.t11-nav{display:flex;align-items:center;gap:21px;font-size:13px;color:#d1d9ea}
.t11-nav a{color:inherit}.t11-nav a:hover{color:white}
.t11-hero{background:radial-gradient(circle at 90% 18%,#26376c 0,transparent 44%),linear-gradient(145deg,#111d34,#0b1426);color:white;padding:84px 0 72px}
.t11-kicker{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#a4b6ff;font-weight:800}
.t11-hero h1{font-size:clamp(42px,6vw,78px);line-height:1.09;letter-spacing:-.07em;max-width:900px;margin:18px 0 20px;color:#fff}
.t11-hero h1 em{font-style:normal;color:#b4adff}
.t11-goal{font-size:20px;line-height:1.8;max-width:800px;color:#dce5f5}
.t11-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:32px;align-items:center}
.t11-btn{min-height:46px;padding:12px 22px;border-radius:10px;border:1px solid #a2a9c6;display:inline-flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;cursor:pointer}
.t11-btn-primary{color:#17163b;background:#b9afff;border-color:#b9afff}
.t11-btn-secondary{color:white;border-color:#56627e}
.t11-btn-disabled{color:#b6c4dc;background:#34425c;border-color:#46536a;cursor:not-allowed;opacity:.9}
.t11-note{font-size:12px;color:#b6c4d8;margin-top:15px}
.t11-layout{display:grid;grid-template-columns:minmax(0,1fr) 245px;gap:40px;padding-top:55px;padding-bottom:70px}
.t11-main{min-width:0}.t11-side{align-self:start;position:sticky;top:88px}
.t11-toc{border:1px solid var(--s-line);border-radius:14px;padding:20px;background:white}
.t11-toc b{font-size:12px;letter-spacing:.08em;color:var(--s-muted)}
.t11-toc a{display:block;padding:11px 0;border-bottom:1px solid #eef1f5;font-size:13px;color:#42526c}
.t11-toc a:last-child{border-bottom:0}
.t11-panel{margin:0 0 34px;padding:32px 32px 35px;background:#fff;border:1px solid var(--s-line);border-radius:18px;box-shadow:0 9px 22px rgba(25,37,57,.035)}
.t11-step{font-size:12px;color:var(--s-violet);font-weight:900;letter-spacing:.06em}
.t11-panel h2{font-size:29px;letter-spacing:-.04em;line-height:1.26;margin:9px 0 15px}
.t11-panel h3{font-size:17px;margin:26px 0 10px}
.t11-panel p,.t11-panel li{font-size:15px;line-height:1.86;color:#3f4f62}
.t11-panel ul,.t11-panel ol{padding-left:23px}
.t11-panel li{margin-bottom:8px}
.t11-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:20px}
.t11-mini{padding:18px;border-radius:12px;background:#f2f5fa}
.t11-mini strong{display:block;font-size:15px;margin-bottom:6px}
.t11-mini p{margin:0;font-size:13px}
.t11-scroll{overflow-x:auto;border:1px solid var(--s-line);border-radius:12px;margin:20px 0}
.t11-table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.65;text-align:left}
.t11-table th,.t11-table td{padding:15px 12px;border-bottom:1px solid #e8edf3;vertical-align:top;min-width:105px}
.t11-table thead th{background:#edf1f9;font-size:12px;color:#33465e}
.t11-table tbody tr:last-child td,.t11-table tbody tr:last-child th{border-bottom:0}
.t11-table th[scope=row]{color:#293d59;white-space:nowrap}
.t11-payment{min-width:965px}.t11-diagnosis{min-width:750px}
.t11-table a{color:#5148b2;text-decoration:underline;text-underline-offset:3px;font-weight:650}
.t11-table small{display:block;margin-top:9px;color:#6b7586;font-size:11px}
.t11-callout{padding:18px 19px;border-left:3px solid #7d73dc;background:#f1f0ff;border-radius:0 10px 10px 0;color:#34405d;font-size:14px;line-height:1.75;margin:21px 0}
.t11-checkgroup{border:1px solid #e5e9f1;border-radius:12px;padding:20px;margin:13px 0;background:#fbfcfe}
.t11-checkgroup h3{margin:0 0 13px}
.t11-task{display:flex;align-items:flex-start;gap:12px;padding:9px 0;cursor:pointer;font-size:14px;color:#344358}
.t11-task input{flex:none;width:18px;height:18px;accent-color:#6156cb;margin-top:3px}
.t11-task input:checked+span{color:#79869a;text-decoration:line-through}
.t11-progress{display:block;margin-bottom:16px;font-size:13px;font-weight:750;color:#6256bb}
.t11-footer{border-top:1px solid #dce2ec;padding:30px 0 45px;color:#566376;font-size:12px}
.t11-footer a{color:#5247af}
@media(max-width:900px){.t11-layout{display:block}.t11-side{display:none}.t11-hero{padding:56px 0}.t11-panel{padding:25px}.t11-cards{grid-template-columns:1fr}}
@media(max-width:520px){.t11-wrap{padding:0 17px}.t11-bar{min-height:60px}.t11-brand{font-size:22px}.t11-brand span{display:none}.t11-nav{gap:12px;font-size:12px}.t11-nav a:nth-child(2){display:none}.t11-hero h1{font-size:44px}.t11-goal{font-size:17px}.t11-panel{padding:21px 18px;margin-bottom:19px}.t11-panel h2{font-size:25px}.t11-btn{width:100%}.t11-actions{display:grid;grid-template-columns:1fr;width:100%}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""
    markup = f"""<!doctype html><html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>30 天变现冲刺手册｜见势 JIANSHI</title>
<meta name="description" content="为有项目但尚未获得第一笔可验证收入的独立开发者提供四周行动手册、收款平台核对资料和本地检查清单。">
<link rel="canonical" href="{SITE}/sprint/"><meta name="robots" content="index,follow">
<link rel="stylesheet" href="/styles.css"><style>{style}</style></head><body>
<div class="t11"><header class="t11-top"><div class="t11-wrap t11-bar">
<a class="t11-brand" href="/">见势<span>JIANSHI</span></a>
<nav class="t11-nav" aria-label="站点导航"><a href="/projects/">项目库</a><a href="/sprint/" aria-current="page">30 天冲刺</a><a href="/#j2-opportunities">回到首页</a></nav>
</div></header>
<main><section class="t11-hero"><div class="t11-wrap">
<div class="t11-kicker">FIELD GUIDE / 30 DAYS / 免费公开版</div>
<h1>别再收藏方法。<br><em>用 30 天推进第一笔收入。</em></h1>
<p class="t11-goal"><strong>冲刺目标 = 30 天内拿到第一笔可被第三方验证的收入。</strong> 这是行动目标，不是收入预测，也不代表每个人都能在规定时间内完成。</p>
<div class="t11-actions">{cta}<a class="t11-btn t11-btn-secondary" href="#step0">阅读完整冲刺步骤 ↓</a></div>
<p class="t11-note">诊断仅通过外部飞书表单接收；见势本页不采集项目资料或联系方式。</p>
</div></section>
<div class="t11-wrap t11-layout"><div class="t11-main">
<section class="t11-panel" id="step0"><span class="t11-step">STEP 00 · 选题先于开发</span><h2>项目分诊：先淘汰，再投入</h2>
<p>把手头全部项目放进同一张表；空白不是评分，填不出来就先找证据。表格是填写模板，不会在见势网站保存输入。</p>
<div class="t11-scroll"><table class="t11-table t11-diagnosis" aria-label="五列项目分诊表"><thead><tr>
<th>项目名</th><th>给谁省什么</th><th>进度</th><th>海外同类付费证据链接</th><th>第一批用户在哪</th>
</tr></thead><tbody><tr><td>待填写</td><td>目标人群 / 可验证节省</td><td>想法 / demo / 可用 / 已上线</td><td>优先 A/B 级公开原始证据</td><td>具体社群、话题、论坛</td></tr></tbody></table></div>
<h3>按顺序执行的五条淘汰规则</h3><ol>
<li>说不清“给谁省什么” → <strong>冻结</strong>。</li>
<li>核心功能无法在两周内跑通 → <strong>冻结</strong>。</li>
<li>找不到海外同类 A/B 级付费证据 → <strong>降级</strong>，继续核查。</li>
<li>找不到能接触的第一批 20 个真人 → <strong>降级</strong>。</li>
<li>对剩余项目按五维可执行性评分取第一名；第二名作为备选，其余冻结，不删除。</li>
</ol><div class="t11-callout">产出：一份选题决策记录，解释为什么选它，以及为什么暂时不做其他项目。</div></section>

<section class="t11-panel" id="week1"><span class="t11-step">WEEK 01 · 把支付路径做通</span><h2>先做到能收钱</h2>
<p>落地页只需六要素：<strong>一句话价值、三个核心功能点、价格、服务条款、隐私政策、联系邮箱</strong>。把产品谁来买、买后会得到什么写清楚。</p>
<div class="t11-cards"><div class="t11-mini"><strong>订阅定价</strong><p>标准参考下限 ≥ $9 / 月，可另设透明、限量的创始用户价格。</p></div>
<div class="t11-mini"><strong>一次性定价</strong><p>标准参考下限 ≥ $29，写明交付内容、售后及退款条件。</p></div></div>
<p>先申请 Creem，再准备 Dodo Payments 作为备用；也可以核对 Waffo Pancake 的地区准入。不要把“可以注册”当成“已通过正式收款审核”。</p>
<div class="t11-callout">本周验收：落地页可访问，测试环境完成一笔模拟支付且状态正确。测试单不是收入，不可计入真实营业额。</div>
</section>

<section class="t11-panel" id="week23"><span class="t11-step">WEEK 02–03 · 去用户出现的地方</span><h2>找到 20 个真人，而不是 20 个点赞</h2>
<p>先列聚集地：<strong>即刻具体话题、小红书搜索词及评论区、V2EX 对应节点、独立开发者社区、目标行业微信群、Product Hunt 同类讨论区</strong>。每处至少写出一个具体频道或关键词。</p>
<ol><li>发布非广告式价值帖：先说遇到的问题、做过的尝试、可免费用的方法，再邀请目标用户讨论。</li>
<li>礼貌且有针对性地私信 <strong>50 人</strong>，不群发骚扰，不收集无关私人信息。</li>
<li>目标完成 <strong>20 次真实对话</strong>，询问最近一次怎么处理问题、花了什么成本。</li>
<li>若痛点吻合，直接给出清晰付费链接或创始用户价，而不是只问“你觉得这个想法如何”。</li>
<li>每天公开可验证的工作进展；用户对话只记录去标识化的共性与拒绝理由。</li></ol>
<div class="t11-callout">验收：至少 20 条去标识化的真实对话记录。数量是执行指标，不代表购买转化。</div>
</section>

<section class="t11-panel" id="week4"><span class="t11-step">WEEK 04 · 让来源说话</span><h2>收入可验证，然后写复盘</h2>
<p>如有真实支付，在收款平台的官方后台申请只读或限定读取权限的凭证，并仅在 <a href="https://trustmrr.com/faq" target="_blank" rel="noopener noreferrer">TrustMRR 官方页面 ↗</a> 按指引连接支持的 Creem / Dodo Payments。密钥不填入见势页面、不提交到 GitHub，不提供给陌生第三方。</p>
<p>完成验证后，检查公开页面确实显示对应产品与验证方；尚未生成公开页、仍在审核或只有测试支付时，只标“未完成验证”。不要把真实收入、MRR、累计收入混为一谈。</p>
<div class="t11-callout">复盘五件事：选题为什么留下、价格如何定、用户从哪来、真实转化是什么、哪里失败以及下轮做什么。</div>
</section>

<section class="t11-panel" id="fallback"><span class="t11-step">PLAN B · 允许失败，留下证据</span><h2>冲刺结束，怎么决策</h2>
<ul><li>第 30 天收入仍为 0：公开匿名化的失败复盘，从分诊第二名项目重新进行下一轮冲刺。</li>
<li>收款平台注册或正式收款审核被拒：先弄清具体原因，改用已确认符合当地要求的备用平台（Dodo / Waffo Pancake），不绕过平台风控。</li>
<li>只产生测试支付、退款或不可核对的转账：不得写成已验证收入。</li></ul></section>

<section class="t11-panel" id="payments"><span class="t11-step">PAYMENT OPTIONS · 官网事实核对</span><h2>收款平台对照表</h2>
<p>仅记录 2026-10-18 查阅的官方公开资料；费率为标示条件下的基础收费，具体地区、币种、订阅、提现和风险审核可能不同。请在注册前核对链接的最新版本。</p>
<div class="t11-scroll"><table class="t11-table t11-payment" aria-label="三家收款平台核对表"><thead><tr>
<th>平台</th><th>个人可否注册</th><th>提现方式</th><th>费率</th><th>审核要求</th><th>来源链接</th><th>核对日期</th>
</tr></thead><tbody>{''.join(providers)}</tbody></table></div>
<p>公开价格不能推导净收益。平台是否可用于中国大陆、日本或其他地区，请按官方最新资格和 KYC 规则逐案核实，不要使用虚假地区或主体资料。</p></section>

<section class="t11-panel" id="checklist"><span class="t11-step">CHECKLIST · 本地保存</span><h2>一周一组，勾掉做过的事</h2>
<p>勾选状态只储存在当前浏览器的 <code>localStorage</code>，刷新后保留；见势不上传你的勾选记录。换设备、清理站点数据或关闭浏览器存储后可能丢失。</p>
<output class="t11-progress" data-t11-progress role="status" aria-live="polite">已完成 0 项</output>
{''.join(checklist)}
</section>
<section class="t11-panel" id="case0"><span class="t11-step">CASE 00 · 创始人观察日志</span><h2>真实执行，持续记录</h2>
<p>见势创始人正在用这套方法推自己的项目，进度日志 /log 即将上线。</p><p>这里不提前展示尚未核验的业绩、天数或销售结果。</p></section>
</div><aside class="t11-side"><nav class="t11-toc" aria-label="页面章节"><b>冲刺路线</b>
<a href="#step0">00　项目分诊</a><a href="#week1">01　能收钱</a><a href="#week23">02–03　找真人</a><a href="#week4">04　收入可验证</a>
<a href="#fallback">失败预案</a><a href="#payments">收款平台比较</a><a href="#checklist">每周检查清单</a><a href="#case0">创始人案例</a>
</nav></aside></div></main><footer class="t11-footer"><div class="t11-wrap">见势 JIANSHI · 方法手册仅供独立项目研究与执行，不构成经营或收益承诺。 <a href="/">首页</a> · <a href="/privacy/">隐私说明</a></div></footer></div>
<script>window.JIANSHI_ANALYTICS_CONFIG={analytics_json};</script><script src="/analytics.js" defer></script>
<script src="/sprint.js" defer></script></body></html>"""
    if any(word in markup for word in OLD_PROMISE_WORDS):
        raise ValueError("T11 page contains disallowed income-promise vocabulary")
    return markup

def publish(output: Path = ROOT / "web" / "dist", *, config_file: Path = ROOT / "config" / "site.json") -> Path:
    html_body = render_sprint(_form_url(config_file), os.getenv("JIANSHI_ANALYTICS_URL", ""))
    target = output / "sprint" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_body, encoding="utf-8")
    return target

if __name__ == "__main__":
    print(publish())
