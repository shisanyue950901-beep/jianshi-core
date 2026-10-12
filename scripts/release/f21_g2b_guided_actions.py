"""G2-B public-only interactive preparation guides (no account, CMS, network or storage).

Only editorial, locally rendered content. These checklists are learning and
preparation aids, NOT validation of user data or a public submission.
"""
from __future__ import annotations

from html import escape

CHECKLISTS = {
    "marketplace": (
        "能用一句话说明要解决的业务问题",
        "明确目标受众、使用渠道与交付成果",
        "列出真实拥有使用授权的资料",
        "说明预期完成时间和需要配合的人",
        "写清验收标准、修改范围与预算约束",
        "区分可公开内容与必须保密的信息",
    ),
    "talent": (
        "写清技能方向和本人实际负责的工作",
        "至少选择一项本人有权公开的作品",
        "说明作品目标、制作步骤与所用工具",
        "区分练习、概念稿和真实商业交付",
        "核对客户、品牌、人物及素材的授权",
        "能说清交付格式、修订范围与验收方法",
    ),
}
ACADEMY_PLANS = (
    ("visual", "AI 图像与电商设计",
     "适合对商品素材和营销画面感兴趣的人。准备有使用权的商品照片或自行制作的虚构样品。",
     ("写一份仅使用授权素材的视觉简报", "制作一张测试主图和一张详情页构图", "核对材质、文字、商标与导出尺寸")),
    ("video", "AI 视频与短片制作",
     "适合希望学习脚本、分镜和镜头一致性的人。准备自有或明确授权的图片、声音素材。",
     ("为虚构产品写一段 15 秒脚本", "拆分三个镜头并制作分镜草图", "检查音乐、人物、素材授权和镜头一致性")),
    ("agent", "AI Agent 与工作流",
     "适合想整理重复流程的人。使用完全合成的输入，不连接客户账户、真实订单或生产 API。",
     ("绘制输入、审批、执行、异常四个节点", "在离线沙盒模拟两条正常和一条失败路径", "写出人工接管、权限限制和停止条件")),
    ("global", "AI 出海内容表达",
     "适合多语言内容与海外传播准备。先明确地区、语言及真实产品资料。",
     ("为一段经核对的产品介绍建立术语表", "制作两种语言的对照草稿", "标记仍需母语审校与当地法规确认的内容")),
    ("research", "AI 商业机会研究",
     "适合学习判断商业模式的人。选一项公开产品，不采集私密经营数据或推断个人收入。",
     ("列出产品、目标用户和公开收入模式", "区分原始来源、推测和仍未知的事实", "写出三项可被证伪的可行性假设")),
)
SOLUTION_TRIALS = {
    "ecommerce-visual": ("一份经过授权的产品视觉练习", (
        "选一件自有或使用权清晰的产品，列出三条可核对事实。",
        "制作主图与详情页两种构图，人工核对材质、文字及商标。",
        "按平台尺寸导出，并记录授权范围和需要修改的地方。",
    )),
    "brand-video": ("15 秒概念短片的前期试做", (
        "以虚构品牌或自有产品为题，写明受众与传播目标。",
        "先完成脚本和三个镜头的分镜，再测试有限素材。",
        "按版权、肖像及误导性宣传风险复查，不冒充客户案例。",
    )),
    "automation": ("一个完全离线的流程沙盒", (
        "选一个不涉及真实客户信息的重复工作，画出人工原流程。",
        "用合成数据做一次正常执行与一次失败回退演示。",
        "记录权限、审批责任和手动停止方法，再判断是否值得开发。",
    )),
    "localization": ("两种语言的内容审校练习", (
        "选择真实可核对的产品介绍，整理目标国家和渠道要求。",
        "为两种目标语言制作草稿，对照术语、单位和事实来源。",
        "交由有语言能力的人员复核文化表达和当地合规事项。",
    )),
}

CSS = """
.g2b-panel{border:1px solid #dce4f2;border-radius:18px;background:#fff;padding:24px;box-shadow:0 12px 35px #14264609}
.g2b-panel h3{font-size:22px;margin:0 0 12px}
.g2b-subtitle{font-size:13px;color:#60728f;margin:0 0 20px;line-height:1.8}
.g2b-checklist fieldset{padding:0;border:0;margin:0;min-width:0}
.g2b-checklist legend{font-weight:800;font-size:14px;color:#263751;margin-bottom:14px}
.g2b-choices{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.g2b-choices label{display:flex;align-items:flex-start;gap:10px;border:1px solid #e2e8f2;background:#f8faff;border-radius:10px;padding:12px;cursor:pointer;color:#33465f;font-size:13px;line-height:1.6;min-width:0}
.g2b-choices label:has(input:checked){border-color:#9188e5;background:#f1efff}
.g2b-choices input{flex-shrink:0;width:17px;height:17px;accent-color:#6858bf;margin:2px 0 0}
.g2b-choices input:focus-visible{outline:3px solid #8275f0;outline-offset:3px}
.g2b-actions{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:17px}
.g2b-progress{color:#4a418c;font-weight:800;font-size:13px}
.g2b-reset{border:1px solid #ccd5e7;background:white;color:#344769;border-radius:9px;padding:8px 13px;cursor:pointer;font-size:13px}
.g2b-reset:focus-visible,.g2b-select:focus-visible{outline:3px solid #8d81e8;outline-offset:3px}
.g2b-note{margin:13px 0 0;color:#6b7b92;font-size:12px;line-height:1.75}
.g2b-select{width:100%;max-width:560px;min-height:46px;border:1px solid #aebcce;border-radius:10px;font:inherit;color:#1e304c;padding:8px 13px;background:#fff}
.g2b-learning{margin-top:20px}
.g2b-learning[hidden]{display:none}
.g2b-plan-intro{font-size:13px;color:#62728a;margin:0 0 15px}
.g2b-trial{border:1px solid #d7dfed;background:#f9fbff;border-radius:15px;padding:23px}
.g2b-trial h3{margin:0 0 12px}
.g2b-trial ol{padding-left:21px;margin:0}
.g2b-trial li{margin:8px 0;color:#536780;font-size:13px;line-height:1.8}
@media(max-width:700px){.g2b-choices{grid-template-columns:1fr}.g2b-panel,.g2b-trial{padding:18px}}
"""
JS = r"""(function(){
 'use strict';
 const forms=Array.from(document.querySelectorAll('[data-g2b-checklist]'));
 forms.forEach(form=>{
   const checks=Array.from(form.querySelectorAll('input[type="checkbox"]'));
   const report=form.querySelector('[data-g2b-progress]');
   const reset=form.querySelector('[data-g2b-reset]');
   const update=()=>{
     const count=checks.filter(c=>c.checked).length;
     report.textContent=count+' / '+checks.length+' 项已准备'+(count===checks.length?' · 已完成自查，不代表平台审核通过':' · 仅供自己核对');
   };
   checks.forEach(c=>c.addEventListener('change',update));
   reset.addEventListener('click',()=>{
     checks.forEach(c=>{c.checked=false;});
     update();
     checks[0].focus();
   });
   update();
 });
 const selector=document.getElementById('g2b-academy-choice');
 if(selector){
   const plans=Array.from(document.querySelectorAll('[data-g2b-plan]'));
   const update=()=>{
     plans.forEach(plan=>{plan.hidden=plan.dataset.g2bPlan!==selector.value;});
   };
   selector.addEventListener('change',update);
   update();
 }
})();"""


def e(value: str) -> str:
    return escape(value, quote=True)


def _checklist(items: tuple[str, ...], prefix: str, legend: str) -> str:
    if not items or len(set(items)) != len(items):
        raise ValueError("Invalid or duplicate checklist rows")
    choices = "".join(
        '<label for="' + prefix + '-' + str(i) + '"><input type="checkbox" id="'
        + prefix + '-' + str(i) + '"> <span>' + e(value) + '</span></label>'
        for i, value in enumerate(items, start=1)
    )
    return (
        '<div class="g2b-checklist" data-g2b-checklist><fieldset><legend>'
        + e(legend) + '</legend><div class="g2b-choices">' + choices
        + '</div></fieldset><div class="g2b-actions"><output data-g2b-progress role="status" aria-live="polite">'
        + '0 / ' + str(len(items)) + ' 项已准备</output>'
        + '<button class="g2b-reset" data-g2b-reset type="button">清空本次勾选</button></div></div>'
    )


def readiness(kind: str) -> str:
    """Interactive, transient readiness checklists for two public guide pages."""
    if kind not in CHECKLISTS:
        raise ValueError("Unapproved G2-B checklist kind")
    is_market = kind == "marketplace"
    title = "需求准备完整度自检" if is_market else "作品集公开前自检"
    paragraph = ("先检查是否具备明确成果、授权和审核边界；勾选结果不会提交，"
                 "即使全部完成也不代表能直接发布商单。" if is_market else
                 "准备作品时只核对你拥有公开权利的内容，"
                 "本工具不建立人才档案，也不代表平台已完成认证。")
    return (
        '<div class="g2b-panel"><h3>' + e(title) + '</h3>'
        '<p class="g2b-subtitle">' + e(paragraph) + '</p>'
        + _checklist(CHECKLISTS[kind], "g2b-" + kind, "逐项核对（仅限当前页面）")
        + '<p class="g2b-note">隐私说明：所有勾选仅存在当前页面内存；'
        '不存储、不登录、不发送给平台，刷新后重新开始。</p></div>'
    )


def learning_selector() -> str:
    if len(ACADEMY_PLANS) != 5:
        raise RuntimeError("Unexpected academy plan count")
    options = "".join('<option value="' + e(code) + '">' + e(title) + '</option>'
                      for code, title, _, _ in ACADEMY_PLANS)
    plans = "".join(
        '<section class="g2b-learning" data-g2b-plan="' + e(code) + '"'
        + (' hidden' if i else '') + ' aria-label="' + e(title) + '">'
        '<h3>' + e(title) + '</h3><p class="g2b-plan-intro">' + e(intro) + '</p>'
        + _checklist(tasks, "g2b-learning-" + code, "建议完成的三个练习")
        + '</section>'
        for i, (code, title, intro, tasks) in enumerate(ACADEMY_PLANS)
    )
    return (
        '<div class="g2b-panel"><h3>选一条适合自己的实践路线</h3>'
        '<p class="g2b-subtitle">选择一个方向，查看前置条件和可独立完成的练习。'
        '以下为开放的学习计划，不是已录制、可购买或已开班的课程。</p>'
        '<label for="g2b-academy-choice"><b>选择学习方向</b></label>'
        '<p><select id="g2b-academy-choice" class="g2b-select">' + options + '</select></p>'
        + plans + '<p class="g2b-note">练习状态不会保存、上传或作为学员成绩。'
        '没有视频、报名、购买或结业认证功能。</p></div>'
    )


def solution_trial(slug: str) -> str:
    if slug not in SOLUTION_TRIALS:
        raise ValueError("Unregistered G2-B solution detail")
    title, steps = SOLUTION_TRIALS[slug]
    return (
        '<div class="g2b-trial"><h3>' + e(title) + '</h3>'
        '<ol>' + "".join("<li>" + e(step) + "</li>" for step in steps) + '</ol>'
        '<p class="g2b-note">本练习只帮助判断实施准备度，不是已发生的客户合作、'
        '成交成果或平台服务报价。</p>'
        '<a class="btn primary" style="margin-top:16px" href="/marketplace/brief/">'
        '整理自己的需求草稿 ↗</a></div>'
    )
