#!/usr/bin/env python3
"""B1 founder self-service: offline editorial decision card, not a money ranking.

Only the six already-published, reviewed Chinese business-model descriptions
may enter this tool. Three anonymous select choices are used in memory only.
Nothing posts, stores, collects user identifiers or makes remote recommendations.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

from f21_components import site_header, site_footer
from f21_design_tokens import render_css
from p446_content_hubs import CSS as SHARED_CSS
from p449_plain_business_models import MODEL_SUMMARIES

ROUTE = "start/"
SITE = "https://jianshi-bua.pages.dev"
ALLOWED_MODELS = (
    "vertical-industry-saas", "amazon-fba-niche-brand",
    "digital-product-business", "affiliate-content-site",
    "amazon-kdp-publishing", "agency-business",
)
WARNINGS = {
    "vertical-industry-saas": "软件需要持续维护、服务与支持；先核实真实客户问题，再评估开发量。",
    "amazon-fba-niche-brand": "先核算货款、平台费、仓储、物流和退货；不要因为匹配就先囤货。",
    "digital-product-business": "先核实有人需要小样及素材版权，不能把浏览或点赞当成成交。",
    "affiliate-content-site": "内容流量、分发渠道和推广政策都有不确定性；先验证真实读者问题。",
    "amazon-kdp-publishing": "版权、内容质量、读者需求和平台规则需要逐项核对；不保证销量。",
    "agency-business": "服务需要获客、交付和反复沟通；潜在客户认可不等于真实付款。",
}
# These are transparent editorial sorting preferences, NOT trained inference,
# investment signals, objective suitability or income/return predictions.
SKILL_ORDER = {
    "creative": ("agency-business", "digital-product-business", "affiliate-content-site",
                 "amazon-kdp-publishing", "vertical-industry-saas", "amazon-fba-niche-brand"),
    "technical": ("vertical-industry-saas", "digital-product-business", "agency-business",
                  "affiliate-content-site", "amazon-kdp-publishing", "amazon-fba-niche-brand"),
    "writing": ("affiliate-content-site", "amazon-kdp-publishing", "digital-product-business",
                "agency-business", "vertical-industry-saas", "amazon-fba-niche-brand"),
    "sales": ("agency-business", "amazon-fba-niche-brand", "affiliate-content-site",
              "digital-product-business", "vertical-industry-saas", "amazon-kdp-publishing"),
    "unsure": ("digital-product-business", "agency-business", "affiliate-content-site",
               "amazon-kdp-publishing", "vertical-industry-saas", "amazon-fba-niche-brand"),
}
PREFERENCE_MODELS = {
    "service": ("agency-business", "vertical-industry-saas"),
    "digital": ("digital-product-business", "vertical-industry-saas"),
    "goods": ("amazon-fba-niche-brand", "digital-product-business"),
    "content": ("affiliate-content-site", "amazon-kdp-publishing"),
    "unsure": (),
}
SKILL_LABELS = {
    "creative": "会做设计、视频或数字内容",
    "technical": "会编程或搭建工具",
    "writing": "擅长写作、表达和内容研究",
    "sales": "擅长销售、沟通与选品",
    "unsure": "暂时不清楚自己的优势",
}
PREFERENCE_LABELS = {
    "service": "帮助客户完成具体工作",
    "digital": "制作能重复销售的数字商品",
    "goods": "研究实体商品销售",
    "content": "写内容、做知识或图书",
    "unsure": "还没有确定",
}
RESOURCE_LABELS = {
    "low": "希望先不备货、少花钱验证",
    "some": "愿意先做少量有边界的试验",
    "unsure": "目前不清楚能投入多少",
}
CSS = """
:root{color-scheme:light}
.service-hero{isolation:isolate;background:radial-gradient(ellipse 38% 105% at 93% 5%,#6152b463,transparent 78%),radial-gradient(ellipse 44% 95% at 2% 100%,#2761a866,transparent 78%),linear-gradient(135deg,#091326,#152746 72%,#221e48)}
.service-hero:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(#a4bbff0d 1px,transparent 1px),linear-gradient(90deg,#a4bbff0d 1px,transparent 1px);background-size:46px 46px;mask-image:linear-gradient(90deg,transparent,#0009)}
.service-hero .wrap{position:relative;z-index:1;padding:42px 0 46px}
.service-hero .eyebrow{display:inline-flex;border:1px solid #a9adf45e;background:#7f82ee28;color:#d7d4ff;padding:6px 12px;border-radius:40px;font-size:11px;font-weight:800;letter-spacing:.08em}
.service-hero h1{font-size:clamp(35px,5vw,57px);letter-spacing:-.052em;line-height:1.17;margin:20px 0 16px;color:#fff}
.service-hero h1 em{font-style:normal;background:linear-gradient(100deg,#ceb1ff,#8be0ff);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.service-hero p{font-size:clamp(14px,1.6vw,17px);color:#cdd9ed;max-width:690px;line-height:1.8}
.service-tags{display:flex;gap:9px;flex-wrap:wrap;margin-top:23px}
.service-tags span{border:1px solid #b6c5ee48;background:#e9e8ff0d;color:#d8e5fa;border-radius:30px;padding:6px 12px;font-size:11px}
.service-body{padding:28px 0 75px}
.service-privacy{font-size:13px;padding:15px 18px;border:1px solid #d8def3;border-radius:14px;background:#f0effe;color:#4e567b;line-height:1.8;margin:0 0 19px}
.service-workspace{display:grid;grid-template-columns:minmax(0,.93fr) minmax(0,1.07fr);gap:19px;align-items:start;scroll-margin-top:91px}
.service-form,.service-results{border-radius:21px;background:#fff;border:1px solid #dee6f4;box-shadow:0 8px 30px #263d7510;padding:26px;min-width:0}
.service-form h2,.service-results h2{font-size:clamp(22px,2.7vw,29px);color:#1d2e4c;line-height:1.3;letter-spacing:-.035em;margin:0 0 9px}
.service-subtitle{font-size:13px;line-height:1.7;color:#6c7c98;margin:0 0 24px}
.service-question{margin:19px 0}
.service-question label{display:block;color:#213450;font-weight:800;font-size:13px;margin-bottom:9px}
.service-question label b{display:inline-grid;place-items:center;width:28px;height:26px;background:#edeaff;border-radius:9px;color:#6557c6;font-size:11px;margin-right:8px}
.service-question select{width:100%;border:1px solid #cbd8eb;border-radius:12px;background:#f9fbff;color:#1c3455;min-height:49px;padding:11px 13px;font:14px/1.5 "PingFang SC","Microsoft YaHei",system-ui,sans-serif}
.service-question select:focus-visible{outline:3px solid #bdb4ff;outline-offset:2px}
.service-buttons{display:flex;flex-wrap:wrap;gap:9px;margin:24px 0 0}
.service-buttons button{min-height:45px;padding:10px 17px;font-size:13px;font-weight:800;cursor:pointer;border:1px solid #c5cee4;border-radius:11px;background:#fff;color:#435774}
.service-buttons button.primary{border:0;color:#fff;background:linear-gradient(110deg,#8164eb,#518df1);box-shadow:0 9px 20px #675bd536}
.service-buttons button:hover{filter:brightness(.97)}
.service-buttons button:focus-visible,.service-links a:focus-visible{outline:3px solid #a798fa;outline-offset:3px}
.service-buttons button:disabled{opacity:.43;cursor:not-allowed}
.service-message{color:#6554b6;font-size:12px;line-height:1.7;min-height:20px;margin:14px 0 0}
.service-results{background:linear-gradient(180deg,#fff,#fbfcff)}
.service-empty{min-height:225px;display:grid;place-items:center;text-align:center;padding:20px;color:#7888a2;background:#f6f8ff;border:1px dashed #c5d0e9;border-radius:15px}
.service-empty strong{font-size:16px;color:#374c6c;display:block;margin-bottom:8px}
.service-result[hidden],.service-empty[hidden]{display:none!important}
.service-answer-caption{font-size:12px;font-weight:750;color:#6155be;margin:4px 0 15px}
.service-picks{display:grid;gap:12px}
.service-pick{padding:17px;border:1px solid #e0e5f3;border-radius:15px;background:#fff;min-width:0}
.service-pick header{display:flex;gap:12px;align-items:baseline;margin:0 0 10px}
.service-pick header span{color:#7766d0;font-size:11px;font-weight:800}
.service-pick h3{font-size:19px;color:#1b2b48;margin:0;line-height:1.4}
.service-pick p{font-size:13px;line-height:1.7;color:#51647f;margin:6px 0}
.service-pick p b{color:#273e60}
.service-pick .caution{background:#f5f2ff;border-left:3px solid #9180df;padding:9px 12px;border-radius:0 9px 9px 0;margin-top:13px}
.service-pick a{display:inline-flex;align-items:center;min-height:44px;margin-top:9px;color:#5448bc;font-size:13px;font-weight:800;text-decoration:underline;text-underline-offset:3px}
.service-plan{margin:22px 0 0;padding:17px;background:#f1f4fc;border:1px solid #dce5f3;border-radius:14px}
.service-plan h3{margin:0 0 10px;color:#243953;font-size:18px}
.service-plan ol{padding-left:21px;margin:0}
.service-plan li{font-size:13px;line-height:1.75;margin:8px 0;color:#435774}
.service-warning{font-size:12px;color:#6a7389;line-height:1.8;margin:17px 0}
.service-links{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}
.service-links a{border:1px solid #cfd7ea;background:#fff;border-radius:10px;font-size:12px;padding:10px 13px;color:#574dba;font-weight:800;min-height:43px}
.service-copy{margin-top:18px}
.service-copy button{border:0;border-radius:10px;background:#eae8ff;color:#5746ba;font-size:13px;font-weight:800;padding:12px 16px;cursor:pointer;min-height:44px}
.service-copy button:focus-visible{outline:3px solid #9988ec;outline-offset:3px}
.service-footer-note{font-size:13px;color:#63738c;line-height:1.8;margin:23px 0 0}
@media(max-width:850px){.service-workspace{grid-template-columns:1fr}.service-form,.service-results{padding:21px}}
@media(max-width:650px){.service-hero .wrap{padding:28px 0 31px}.service-hero h1{font-size:clamp(32px,8vw,43px)}.service-hero:after{background-size:33px 33px}.service-body{padding-top:19px}.service-tags{gap:6px}.service-form,.service-results{padding:18px}.service-question{margin:16px 0}.service-empty{min-height:155px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

SCRIPT = r"""
(function () {
'use strict';
const root=document.getElementById('service-workspace');
const output=document.getElementById('service-result');
const empty=document.getElementById('service-empty');
const picks=document.getElementById('service-picks');
const plan=document.getElementById('service-plan');
const message=document.getElementById('service-message');
const selects=['skill','preference','resource'].map(function(key){return document.getElementById('service-'+key);});
const copy=document.getElementById('service-copy');
const data=JSON.parse(document.getElementById('service-models').textContent);
let report='';
function node(tag,text,cls){
 const el=document.createElement(tag);
 if(cls)el.className=cls;
 if(text!==null && text!==undefined)el.textContent=text;
 return el;
}
function para(label,content,cls){
 const p=node('p',null,cls);
 p.appendChild(node('b',label));
 p.appendChild(document.createTextNode(content));
 return p;
}
function state(){
 return {skill:selects[0].value,preference:selects[1].value,resource:selects[2].value};
}
function rank(s){
 const order=data.skill_order[s.skill];
 const prefs=data.preferences[s.preference];
 return order.map(function(id,index){
   let score=(6-index)*3;
   if(prefs.indexOf(id)>=0)score+=prefs[0]===id?14:7;
   if(s.resource==='low'&&id==='amazon-fba-niche-brand')score-=20;
   return {id:id,score:score,index:index};
 }).sort(function(a,b){return b.score-a.score||a.index-b.index;}).slice(0,2);
}
function setResultVisible(visible){
 output.hidden=!visible;
 empty.hidden=visible;
 copy.disabled=!visible;
}
function render(s){
 const order=rank(s);
 const reasons=[
  '你目前的优势：'+data.skill_labels[s.skill]+'。',
  '你的倾向：'+data.preference_labels[s.preference]+'。',
  '试验资源：'+data.resource_labels[s.resource]+'。'
 ];
 picks.replaceChildren();
 const reportLines=['见势｜我的创业方向研究卡（本地生成，未保存）','',
  '这不是盈利预测，也不是投资或创业适合度评估。',
  ...reasons,'',
  '以下顺序仅按已公布的编辑性规则整理，必须单独核验需求和成本。',''];
 order.forEach(function(row,i){
   const d=data.models[row.id];
   const card=node('article',null,'service-pick');
   const header=node('header');
   header.appendChild(node('span','方向 '+String(i+1).padStart(2,'0')));
   header.appendChild(node('h3',d.title));
   card.appendChild(header);
   card.appendChild(para('为什么先看：','根据你的技能与产品偏好，将这类生意放到研究清单前面。'));
   card.appendChild(para('谁付钱：',d.payer));
   card.appendChild(para('怎么收费：',d.charge));
   card.appendChild(para('第一步：',d.first));
   card.appendChild(para('重点风险：',d.warning,'caution'));
   const a=node('a','查看这类生意的公开研究 →');
   a.href='/research/'+row.id+'/';
   card.appendChild(a);
   picks.appendChild(card);
   reportLines.push('方向 '+(i+1)+'：'+d.title,'谁付钱：'+d.payer,'怎么收费：'+d.charge,
                    '第一步：'+d.first,'重点风险：'+d.warning,
                    '资料：'+location.origin+'/research/'+row.id+'/','');
 });
 const first=data.models[order[0].id];
 const checks=[
  '第 1 天：把“谁付钱、解决什么问题”写成一句话，找出明确的目标使用者。',
  '第 2–3 天：向真实潜在使用者核查需求和现有替代方案；仅记录经同意的非敏感反馈。',
  '第 4–5 天：按照“'+first.first+'”做最小成本验证，并列出版权、交付和实际费用。',
  '第 6–7 天：回看证据，区分真实行动、口头兴趣和付款；没有证据时保持“待验证”，可停止投入。'
 ];
 plan.replaceChildren(node('h3','未来 7 天可以做的四件事'));
 const ol=node('ol');
 checks.forEach(function(line){ol.appendChild(node('li',line));});
 plan.appendChild(ol);
 reportLines.push('未来 7 天的验证计划：',...checks,'',
  '停下来的信号：找不到清楚的付费人群、合法来源或基本成本边界时，不要加大投入。');
 report=reportLines.join('\n');
 document.getElementById('service-why').textContent='根据你的回答，先研究这两种方向（并非收益、可行性或成功率排名）。';
 setResultVisible(true);
 message.textContent='研究卡已在当前页面生成。可打开资料核实，也可以复制留作自己的待办。';
}
document.getElementById('service-generate').addEventListener('click',function(){
 const s=state();
 if(!s.skill||!s.preference||!s.resource){
  message.textContent='请先选择三个问题的答案，或点击“体验一个示例”。';
  const first=selects.find(function(el){return !el.value;});
  if(first)first.focus();
  return;
 }
 render(s);
});
document.getElementById('service-demo').addEventListener('click',function(){
 selects[0].value='creative';selects[1].value='service';selects[2].value='low';
 render(state());
 message.textContent='示例：会做设计／内容、想先做服务、希望低投入验证。示例不是对真实用户的调查。';
});
document.getElementById('service-reset').addEventListener('click',function(){
 selects.forEach(function(el){el.selectedIndex=0;});
 report='';picks.replaceChildren();plan.replaceChildren();setResultVisible(false);
 message.textContent='已重置，本页没有保存之前的选择或研究卡。';
 selects[0].focus();
});
copy.addEventListener('click',async function(){
 if(!report)return;
 try{
   if(!navigator.clipboard||!navigator.clipboard.writeText)throw new Error('unsupported');
   await navigator.clipboard.writeText(report);
   message.textContent='研究卡已复制；请自行保存到安全位置。';
 }catch(_){
   message.textContent='无法自动复制。可根据页面内容手动记录，也可以在浏览器中打印当前页面。';
 }
});
setResultVisible(false);
}());
"""


def e(value: str) -> str:
    return escape(value, quote=True)


def model_payload() -> str:
    if set(MODEL_SUMMARIES) != set(ALLOWED_MODELS) or set(WARNINGS) != set(ALLOWED_MODELS):
        raise RuntimeError("Founding research models drifted from six source-approved modes")
    for ids in SKILL_ORDER.values():
        if len(ids) != 6 or set(ids) != set(ALLOWED_MODELS):
            raise RuntimeError("Editorial sorting changed unexpectedly")
    if set(SKILL_ORDER) != set(SKILL_LABELS) or set(PREFERENCE_MODELS) != set(PREFERENCE_LABELS):
        raise RuntimeError("Decision input label mismatch")
    obj = {
        "models": {k: {**MODEL_SUMMARIES[k], "warning": WARNINGS[k]} for k in ALLOWED_MODELS},
        "skill_order": SKILL_ORDER,
        "preferences": PREFERENCE_MODELS,
        "skill_labels": SKILL_LABELS,
        "preference_labels": PREFERENCE_LABELS,
        "resource_labels": RESOURCE_LABELS,
    }
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def select(name: str, label: str, values: dict[str, str], index: int) -> str:
    opts = ''.join('<option value="' + e(k) + '">' + e(v) + '</option>'
                   for k, v in values.items())
    return ('<div class="service-question"><label for="service-' + name
            + '"><b>' + str(index).zfill(2) + '</b>' + e(label) + '</label>'
            '<select id="service-' + name + '"><option value="">请选择一个答案</option>'
            + opts + '</select></div>')


def render() -> str:
    body=(
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="referrer" content="no-referrer"><meta name="robots" content="index,follow">'
        '<title>3 个问题，生成创业方向研究卡｜见势</title>'
        '<meta name="description" content="用三个不涉及隐私的问题整理你的创业研究起点，查看六种公开生意模式、收费方式、风险与一周验证计划。不提供盈利预测。">'
        '<link rel="canonical" href="' + SITE + '/start/">'
        '<style>' + SHARED_CSS + render_css() + CSS + '</style></head><body>'
        + site_header('/start/')
        + '<main><section class="hero service-hero"><div class="wrap">'
        '<div class="crumb"><a href="/">见势首页</a> / 研究方向诊断</div>'
        '<span class="eyebrow">JIANSHI / FIRST RESEARCH STEP</span>'
        '<h1>不确定做什么生意？<br><em>从三个问题开始。</em></h1>'
        '<p>不用注册、不用留下联系方式。根据你的优势、偏好和试验资源，'
        '从六类公开商业模式中整理两个值得先研究的方向，再拿到一份 7 天验证清单。</p>'
        '<div class="service-tags"><span>不需登录</span><span>不上传答案</span>'
        '<span>不是 AI 收益预测</span></div></div></section>'
        '<div class="wrap service-body">'
        '<p class="service-privacy"><b>这项服务现在能做什么：</b>帮你理清研究起点、'
        '看谁付钱以及下一步怎么核查。结果按预设的公开编辑规则排序，不是经过真实创业数据验证的“最优项目”。'
        '浏览器不会保存你的选择，也不会发送到服务器。</p>'
        '<section class="service-workspace" id="service-workspace" aria-label="创业方向研究服务">'
        '<div class="service-form"><h2>先说说你想怎么开始</h2>'
        '<p class="service-subtitle">只选三个问题，不必填写姓名、预算金额或个人资料。</p>'
        + select("skill", "你当前最有把握的能力？", SKILL_LABELS, 1)
        + select("preference", "你更想尝试哪种生意？", PREFERENCE_LABELS, 2)
        + select("resource", "你现在如何看待起步投入？", RESOURCE_LABELS, 3)
        + '<div class="service-buttons"><button id="service-generate" class="primary" type="button">生成我的研究卡 →</button>'
        '<button id="service-demo" type="button">体验一个示例</button>'
        '<button id="service-reset" type="button">重新选择</button></div>'
        '<p class="service-message" id="service-message" role="status" aria-live="polite"></p></div>'
        '<div class="service-results"><h2>你的研究方向卡</h2>'
        '<p class="service-subtitle">这里给你真实可读的研究路径，而不是虚构赚钱项目。</p>'
        '<div class="service-empty" id="service-empty"><div><strong>你的研究卡会出现在这里</strong>'
        '选择三个答案，或点击“体验一个示例”看看整个服务流程。</div></div>'
        '<div class="service-result" id="service-result" hidden>'
        '<p id="service-why" class="service-answer-caption"></p>'
        '<div id="service-picks" class="service-picks" aria-label="待研究的两个方向"></div>'
        '<div id="service-plan" class="service-plan" aria-label="七天验证计划"></div>'
        '<p class="service-warning">这些是常见商业模式的研究建议，不是现成加盟或投资机会。'
        '没有验证客户需求、交付成本、现金流与相关法律规则之前，不应据此投入资金。</p>'
        '<div class="service-links"><a href="/projects/">对照 3 家真实公司案例 ↗</a>'
        '<a href="/research/">比较全部 6 种生意 ↗</a>'
        '<a href="/sources/">看看资料来源 ↗</a></div>'
        '<div class="service-copy"><button type="button" id="service-copy" disabled>复制这份研究卡</button></div>'
        '</div></div></section>'
        '<p class="service-footer-note">如果你已有明确创业方向，也可以直接'
        '<a href="/discover/">搜索项目与生意模式</a>，查看公开来源再决定要不要进一步验证。</p>'
        '</div></main>'
        + site_footer()
        + '<script type="application/json" id="service-models">' + model_payload() + '</script>'
        + '<script>' + SCRIPT + '</script></body></html>\n'
    )
    if (body.count("<main>")!=1 or body.count("</main>")!=1
            or body.count('<script>')!=1 or body.count('type="application/json"')!=1
            or len(body.encode("utf-8"))>95000):
        raise RuntimeError("Founder service publication contract invalid")
    forbidden=("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "localStorage",
               "sessionStorage", "indexedDB", "<form", 'type="email"', "data-auth-email-form")
    if any(part in body for part in forbidden):
        raise RuntimeError("Service tool must not transmit or persist user choices")
    return body


def publish(output: Path) -> int:
    dest=output/ROUTE/"index.html"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(render(),encoding="utf-8")
    return 1
