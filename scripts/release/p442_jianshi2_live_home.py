"""JIANSHI 2.0: release-time portal, built only from admitted case evidence.

Keeps the P4.12E interactive research experience, strict named-case admission,
privacy, public research appendix and static-only deployment intact.
Never fetches network data or writes private source records.
"""
from __future__ import annotations

import base64
import re
from html import escape
from pathlib import Path

from p438_public_ux_contract import public_metrics
from t08_project_selection import featured_projects, usd

ROOT = Path(__file__).resolve().parents[2]
VISUAL_SOURCE = ROOT / "web/prototypes/jianshi2-v1/index.html"

STYLE = """
/* JIANSHI 2.0 portal: scoped to the release-only homepage. */
#j2{--j2-ink:#101d30;--j2-muted:#66758d;--j2-edge:#e5eaf3;--j2-blue:#538dff;--j2-violet:#9975ff;color:var(--j2-ink);background:#f7f9fd;font:15px/1.67 "PingFang SC","Microsoft YaHei",Inter,system-ui,sans-serif;isolation:isolate}
#j2,#j2 *{box-sizing:border-box}#j2 a{text-decoration:none}#j2 .j2-wrap{width:min(1260px,calc(100% - 56px));margin-inline:auto}
#j2 .j2-mast{position:relative;overflow:hidden;background:#07101e;color:#fff}
#j2 .j2-mast:before{content:"";position:absolute;inset:-40% -30% auto 30%;height:700px;background:radial-gradient(ellipse,rgba(99,79,242,.28),transparent 65%);pointer-events:none}
#j2 .j2-hero{position:relative;display:grid;grid-template-columns:1.1fr 1fr;align-items:center;gap:24px;padding-top:70px;padding-bottom:90px;min-height:530px}
#j2 .j2-kicker{display:inline-flex;align-items:center;padding:6px 13px;border:1px solid #536487;border-radius:40px;background:#182844;color:#d6ddff;font-size:12px;letter-spacing:.05em}
#j2 h1{font-size:clamp(42px,4.7vw,70px);line-height:1.18;font-weight:850;letter-spacing:-.05em;color:#fff;margin:24px 0 20px}
#j2 h1 em{font-style:normal;color:#a9a0ff;background:linear-gradient(100deg,#b3a0ff,#52bbff);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}
#j2 .j2-lead{font-size:clamp(15px,1.55vw,19px);line-height:1.8;color:#c2cede;max-width:600px;margin:0 0 30px}
#j2 .j2-actions{display:flex;gap:12px;flex-wrap:wrap}
#j2 .j2-button{display:inline-flex;justify-content:center;align-items:center;gap:8px;min-height:47px;padding:11px 21px;border-radius:12px;font-weight:750;font-size:14px;transition:transform .24s,box-shadow .24s;border:1px solid #64718a;color:#eff5ff}
#j2 .j2-button:hover,#j2 .j2-button:focus-visible{transform:translateY(-3px)}
#j2 .j2-button--primary{border:0;background:linear-gradient(110deg,#936aff,#418efb);box-shadow:0 12px 30px #383fbc55;color:white}
#j2 .j2-proofnote{margin-top:23px;font-size:12px;line-height:1.7;color:#a1b0c8;max-width:575px}
#j2 .j2-visual{position:relative}
#j2 .j2-visual:before{content:"";position:absolute;inset:10% 4%;border-radius:50%;background:#6e7bff60;filter:blur(70px)}
#j2 .j2-visual img{position:relative;display:block;width:100%;height:auto;max-height:430px;object-fit:contain;filter:drop-shadow(0 28px 38px #0008);border-radius:18px;animation:j2Float 7s ease-in-out infinite}
@keyframes j2Float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
#j2 .j2-metrics{background:#101c30;border:1px solid #34405a;border-radius:18px;position:relative;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;transform:translateY(-31px);margin-bottom:-31px;box-shadow:0 18px 35px #121e3533}
#j2 .j2-metric{padding:18px 25px;border-right:1px solid #34405a;color:#fff}#j2 .j2-metric:last-child{border:0}
#j2 .j2-metric strong{display:block;font-size:31px;line-height:1.2;font-weight:800}#j2 .j2-metric span{display:block;color:#c6d1e3;font-size:12px;margin-top:7px}
#j2 .j2-content{padding:58px 0 82px}#j2 .j2-intro{display:flex;justify-content:space-between;align-items:end;gap:25px;margin-bottom:25px}
#j2 .j2-overline{font-size:11px;font-weight:800;letter-spacing:.14em;color:#6855d2}
#j2 h2{font-size:clamp(27px,3.1vw,42px);line-height:1.25;letter-spacing:-.035em;margin:9px 0 8px;font-weight:780;color:#172338}
#j2 .j2-intro p,#j2 .j2-muted{color:#66758d;font-size:14px;margin:0}
#j2 .j2-shortcuts{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-bottom:70px}
#j2 .j2-shortcut{display:flex;min-width:0;min-height:145px;flex-direction:column;justify-content:space-between;border:1px solid #e3e9f4;background:#fff;border-radius:17px;padding:20px;transition:transform .25s,box-shadow .25s,border-color .25s}
#j2 .j2-shortcut:hover,#j2 .j2-shortcut:focus-visible{transform:translateY(-6px);border-color:#b5bcfa;box-shadow:0 19px 42px #303d7815}
#j2 .j2-shortcut i{font-size:25px;font-style:normal}#j2 .j2-shortcut strong{font-size:15px;color:#14253c}
#j2 .j2-shortcut small{display:block;color:#718097;font-size:11px;margin-top:3px}#j2 .j2-shortcut .j2-arrow{align-self:flex-end;color:#7e70df;font-weight:bold}
#j2 .j2-study-paths{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin:0 0 42px}
#j2 .j2-study-path{display:flex;flex-direction:column;gap:7px;border:1px solid #dce6f4;background:white;border-radius:16px;padding:22px;color:#172a45;min-height:145px}
#j2 .j2-study-path:hover,#j2 .j2-study-path:focus-visible{border-color:#8972e7;box-shadow:0 12px 28px #303d7815}
#j2 .j2-study-path strong{font-size:16px}#j2 .j2-study-path span{font-size:13px;line-height:1.7;color:#64748b}
#j2 .j2-study-path small{font-size:12px;font-weight:750;color:#6252bf;margin-top:auto}
#j2 .j2-research-check{background:#f7f9fe;border-left:3px solid #a69af4;padding:13px 14px;display:flex;flex-direction:column;gap:5px}
#j2 .j2-research-check dt{font-size:12px;font-weight:800;color:#33486c}#j2 .j2-research-check dd{font-size:12px;line-height:1.65;color:#66758d;margin:0}
#j2 .j2-section{margin-top:70px;scroll-margin-top:92px}
#j2 .j2-sectionhead{display:flex;align-items:end;justify-content:space-between;gap:18px;margin-bottom:23px}
#j2 .j2-sectionhead .j2-plainlink{color:#4753c9;text-decoration:underline;text-underline-offset:5px;white-space:nowrap;font-size:13px}
#j2 .j2-projects{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px}
#j2 .j2-project{background:white;border:1px solid var(--j2-edge);border-radius:17px;padding:25px;min-width:0;display:flex;flex-direction:column;gap:13px;transition:transform .22s,box-shadow .22s}
#j2 .j2-project:hover{transform:translateY(-4px);box-shadow:0 16px 35px #34477a16}
#j2 .j2-project .j2-case-type{color:#655ad8;font-size:11px;letter-spacing:.04em;font-weight:800}
#j2 .j2-project h3{font-size:22px;line-height:1.35;margin:0;color:#172238}
#j2 .j2-project p{margin:0;color:#61708a;font-size:13px;line-height:1.8;flex-grow:1}
#j2 .j2-project a{color:#525bc9;font-size:13px;font-weight:780}
#j2 .j2-solutions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}
#j2 .j2-solution{overflow:hidden;background:white;border:1px solid var(--j2-edge);border-radius:16px;min-width:0}
#j2 .j2-solution-body a{display:inline-block;margin-top:14px;color:#5853c4;font-size:12px;font-weight:800}
#j2 .j2-art{height:144px;display:flex;align-items:center;justify-content:center;font-size:58px;position:relative;color:white;overflow:hidden}
#j2 .j2-art::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 65% 30%,#ffffff49,transparent 58%)}
#j2 .j2-solution:nth-child(1) .j2-art{background:linear-gradient(135deg,#d999e5,#6452a8)}
#j2 .j2-solution:nth-child(2) .j2-art{background:linear-gradient(135deg,#292b50,#638bdc)}
#j2 .j2-solution:nth-child(3) .j2-art{background:linear-gradient(135deg,#266a9d,#3dcaaf)}
#j2 .j2-solution:nth-child(4) .j2-art{background:linear-gradient(135deg,#142d4b,#777cff)}
#j2 .j2-solution-body{padding:18px 20px 21px}
#j2 .j2-solution h3{font-size:17px;font-weight:780;color:#1b2841;margin:0 0 7px}
#j2 .j2-solution p{font-size:13px;color:#65748d;margin:0;min-height:60px}
#j2 .j2-solution small{color:#7b6cc5;display:block;margin-top:15px;font-size:11px}
#j2 .j2-two{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:70px}
#j2 .j2-panel{border:1px solid #e1e8f4;background:white;border-radius:19px;padding:32px;scroll-margin-top:100px}
#j2 .j2-panel--dark{background:linear-gradient(130deg,#101a2d,#222e51);color:#fff;border-color:#303c5a}
#j2 .j2-panel--dark h2{color:#fff}#j2 .j2-panel--dark .j2-muted{color:#c0cbe1}
#j2 .j2-panel .j2-status{display:inline-flex;border-radius:100px;padding:4px 11px;background:#f0edff;color:#6752b8;font-size:11px;font-weight:800}
#j2 .j2-panel--dark .j2-status{background:#364266;color:#ebe4ff}
#j2 .j2-panel a{display:inline-block;margin-top:22px;font-weight:760;font-size:13px;color:#5c59c8;text-decoration:underline;text-underline-offset:4px}
#j2 .j2-panel--dark a{color:#c9bcff}
#j2 .j2-academy{background:linear-gradient(112deg,#0b1530,#2a2560);color:white;border-radius:22px;padding:37px;margin-top:19px;scroll-margin-top:90px}
#j2 .j2-academy h2{color:white;margin-top:13px}#j2 .j2-academy p{font-size:14px;color:#c4ceef;max-width:770px}
#j2 .j2-tags{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}#j2 .j2-tags span{border:1px solid #53638a;border-radius:90px;font-size:12px;padding:7px 12px}
#j2 a:focus-visible{outline:3px solid #74b4ff;outline-offset:4px}
body:has(#j2) .top{background:#07101e;border-bottom:1px solid #273549;color:#f1f5ff}
body:has(#j2) .top .mark,body:has(#j2) .top .mark em{color:#f1f5ff}
body:has(#j2) .top .menu-btn,body:has(#j2) .top .theme-toggle{color:#eff5ff;border-color:#516078}
body:has(#j2) #splash{display:none!important}
@media(max-width:1050px){#j2 .j2-shortcuts{grid-template-columns:repeat(3,minmax(0,1fr))}#j2 .j2-solutions{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){#j2 .j2-wrap{width:calc(100% - 36px)}#j2 .j2-hero{grid-template-columns:1fr;padding-top:52px;padding-bottom:85px;gap:15px;min-height:0}#j2 .j2-visual img{max-height:310px}#j2 h1{font-size:clamp(36px,8.9vw,53px)}#j2 .j2-actions .j2-button{min-height:45px}#j2 .j2-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}#j2 .j2-metric{padding:14px 11px}#j2 .j2-metric strong{font-size:clamp(22px,6vw,31px)}#j2 .j2-metric span{font-size:10px}#j2 .j2-content{padding-top:41px}#j2 .j2-shortcuts{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}#j2 .j2-study-paths{grid-template-columns:1fr;gap:10px}#j2 .j2-projects{grid-template-columns:1fr}#j2 .j2-two{grid-template-columns:1fr}#j2 .j2-section{margin-top:52px}#j2 .j2-sectionhead{align-items:start;flex-direction:column;gap:8px}#j2 .j2-panel{padding:25px}#j2 .j2-academy{padding:27px 23px}}
@media(max-width:450px){#j2 .j2-solutions{grid-template-columns:1fr}#j2 .j2-intro{display:block}#j2 .j2-shortcut{min-height:115px;padding:15px}}
@media(prefers-reduced-motion:reduce){#j2 .j2-visual img{animation:none}#j2 .j2-button,#j2 .j2-project,#j2 .j2-shortcut{transition:none;transform:none!important}}

/* B1-A04: Show real projects immediately, remove wall-of-jargon UI. */
#j2 .j2-hero{min-height:0;grid-template-columns:minmax(0,1fr) 210px;padding-top:36px;padding-bottom:44px;gap:18px}
#j2 .j2-kicker{font-size:11px}
#j2 h1{font-size:clamp(36px,4vw,58px);margin:14px 0 10px;line-height:1.18}
#j2 .j2-lead{font-size:16px;line-height:1.65;margin:0 0 18px;max-width:700px}
#j2 .j2-visual img{max-height:185px;animation:none;filter:none}
#j2 .j2-visual:before{display:none}
#j2 .j2-button{min-height:43px}
#j2 .j2-proofnote{margin-top:13px;max-width:730px}
#j2 .j2-content{padding-top:26px}
#j2 .j2-section{margin-top:0}
#j2 .j2-intro{margin-bottom:16px}
#j2 .j2-project{gap:10px;padding:21px}
#j2 .j2-project .j2-case-type{color:#5b46ad}
#j2 .j2-project h3{font-size:21px}
#j2 .j2-project p{flex-grow:0;line-height:1.55}
#j2 .j2-project-facts{margin:5px 0 0;display:grid;gap:8px}
#j2 .j2-project-facts div{border-top:1px solid #edf0f8;padding-top:8px}
#j2 .j2-project-facts dt{font-size:11px;color:#69788f;font-weight:650}
#j2 .j2-project-facts dd{font-size:14px;color:#1b2b42;margin:3px 0 0;font-weight:600;line-height:1.45}
#j2 .j2-project-action{margin-top:auto;display:inline-flex;align-items:center;justify-content:center;background:#f1edff;border-radius:10px;min-height:42px;padding:10px 12px}
#j2 .j2-simple-notice{font-size:12px;color:#65728a;margin:14px 0 0;line-height:1.65}
#j2 .j2-after-projects{margin-top:34px;padding-top:26px;border-top:1px solid #e1e6ef}
#j2 .j2-after-projects h2{font-size:26px}
#j2 .j2-study-paths{margin:16px 0 16px}
#j2 .j2-study-path{min-height:105px;padding:16px}
#j2 .j2-study-path span{font-size:12px}
#j2 .j2-shortcuts{margin-bottom:34px}
#j2 .j2-shortcut{min-height:95px;padding:14px}
#j2 .j2-solutions{margin-top:18px}
#j2 .j2-metrics{transform:none;margin:18px 0 0;box-shadow:none;background:#182840;border-radius:12px}
#j2 .j2-metric{padding:13px}
#j2 .j2-metric strong{font-size:24px}
#j2 .j2-metric span{font-size:11px}
@media(max-width:760px){
 #j2 .j2-hero{grid-template-columns:1fr;padding-top:20px;padding-bottom:26px}
 #j2 .j2-visual{display:none}
 #j2 h1{font-size:clamp(34px,8vw,45px)}
 #j2 .j2-lead{font-size:14px;line-height:1.55}
 #j2 .j2-content{padding-top:22px}
 #j2 .j2-projects{grid-template-columns:1fr}
 #j2 .j2-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}
 #j2 .j2-shortcuts{grid-template-columns:repeat(2,minmax(0,1fr))}
}

/* B1 visual polish: editorial research first, motion second. No external assets. */
#j2 .j2-mast{background:
 radial-gradient(ellipse 45% 85% at 88% 22%,#453c8545,transparent 83%),
 radial-gradient(ellipse 50% 140% at 9% 140%,#1e57995c,transparent 70%),
 linear-gradient(130deg,#080f1f 8%,#101b35 67%,#101935)}
#j2 .j2-mast:after{content:"";position:absolute;inset:0;
 background-image:linear-gradient(#91aaff0c 1px,transparent 1px),linear-gradient(90deg,#91aaff0c 1px,transparent 1px);
 background-size:46px 46px;mask-image:linear-gradient(90deg,transparent,#0009);pointer-events:none}
#j2 .j2-mast:before{z-index:0;filter:blur(28px)}
#j2 .j2-hero{z-index:1;grid-template-columns:minmax(0,1fr) 275px;gap:30px;padding-top:44px;padding-bottom:48px}
#j2 .j2-kicker{gap:9px;border:1px solid #788cc960;color:#dde3ff;background:#5e64d619;
 box-shadow:inset 0 1px #ffffff1c;letter-spacing:.08em}
#j2 .j2-kicker:before{content:"";display:block;width:7px;height:7px;border-radius:50%;background:#86d8fd;box-shadow:0 0 0 4px #86d8fd1d,0 0 18px #73b5ff}
#j2 h1{font-size:clamp(38px,4.1vw,59px);letter-spacing:-.052em;margin:17px 0 15px;text-wrap:balance}
#j2 h1 em{background-image:linear-gradient(100deg,#c1a5ff,#7eacff 50%,#80e6ff)}
#j2 .j2-lead{max-width:625px;color:#c8d3e9}
#j2 .j2-button{border-radius:13px;min-height:47px;padding:12px 19px}
#j2 .j2-button--primary{background:linear-gradient(110deg,#8f6bff,#538cfa);box-shadow:0 10px 30px #7768ff38}
#j2 .j2-journey{display:flex;align-items:center;gap:11px;flex-wrap:wrap;margin-top:21px;
 color:#b6c9e7;font-size:12px}
#j2 .j2-journey span:not(.j2-journey-arrow){display:flex;align-items:center;gap:8px}
#j2 .j2-journey b{display:grid;place-items:center;width:25px;height:25px;border-radius:9px;border:1px solid #6d83b878;
 color:#bdc9ff;background:#6c78e421;font-size:10px}
#j2 .j2-journey-arrow{color:#758cb9}
#j2 .j2-first-service{display:inline-flex;align-items:center;min-height:43px;color:#e2d8ff;
 border-bottom:1px solid #b1a6ff80;font-size:13px;font-weight:800;line-height:1.5;
 margin-top:11px;text-decoration:none}
#j2 .j2-first-service:hover,#j2 .j2-first-service:focus-visible{color:#fff;border-bottom-color:#fff}
#j2 .j2-first-service:focus-visible{outline:3px solid #bcaeff;outline-offset:3px}
#j2 .j2-proofnote{margin-top:16px;color:#a7b9d5}
#j2 .j2-visual{min-height:222px;display:grid;place-items:center}
#j2 .j2-visual img{max-height:170px;max-width:183px;position:absolute;bottom:4px;right:3px;
 filter:drop-shadow(0 16px 25px #040a179a);border-radius:20px}
#j2 .j2-visual-panel{position:relative;width:100%;height:218px;border:1px solid #899fd058;border-radius:23px;
 background:linear-gradient(158deg,#ffffff16,#849df307 42%,#231a4b4d 98%);box-shadow:0 24px 60px #030b1c85,inset 0 1px #ffffff21;
 overflow:hidden;backdrop-filter:blur(5px)}
#j2 .j2-visual-panel:after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 68% 65%,#866fff45,transparent 49%);pointer-events:none}
#j2 .j2-visual-top{display:flex;align-items:center;gap:9px;border-bottom:1px solid #8196be3c;padding:15px;
 font-size:9px;letter-spacing:.11em;color:#b3c2e1}
#j2 .j2-visual-top span:last-child{margin-left:auto;color:#c4b1ff;font-size:14px}
#j2 .j2-visual-led{width:7px;height:7px;border-radius:50%;background:#81d9f5;box-shadow:0 0 13px #81d9f58b}
#j2 .j2-visual-caption{position:relative;z-index:1;padding:24px 18px}
#j2 .j2-visual-caption strong{display:block;color:#f6f7ff;font-size:23px;line-height:1.45;letter-spacing:-.04em}
#j2 .j2-visual-caption small{display:block;color:#b1c1df;font-size:10px;margin-top:15px;letter-spacing:.06em}
#j2 .j2-project{border:1px solid #e0e7f7;border-radius:19px;box-shadow:0 7px 25px #273c6710;
 background:linear-gradient(180deg,#fff,#fcfdff)}
#j2 .j2-project:hover,#j2 .j2-project:focus-within{border-color:#9caefa;box-shadow:0 19px 44px #303ca521}
#j2 .j2-project-action{background:linear-gradient(90deg,#f1edff,#eaf3ff);color:#534cc4;font-weight:850}
#j2 .j2-project-action:hover,#j2 .j2-project-action:focus-visible{background:#e4e3ff}
#j2 .j2-study-path,#j2 .j2-shortcut{box-shadow:0 5px 25px #2c3d670a}
#j2 .j2-after-projects{border-top-color:#e0e7f5}
@media(max-width:760px){
 #j2 .j2-hero{grid-template-columns:1fr;padding-top:27px;padding-bottom:31px;gap:15px}
 #j2 .j2-visual{display:none}
 #j2 .j2-journey{gap:7px 9px;margin-top:17px;font-size:11px}
 #j2 .j2-journey b{width:23px;height:23px}
 #j2 .j2-journey-arrow{font-size:10px}
 #j2 .j2-mast:after{background-size:34px 34px}
}
@media(max-width:360px){#j2 .j2-journey{gap:6px;font-size:10px}}
@media(prefers-reduced-motion:reduce){#j2 .j2-visual img,#j2 .j2-project{transition:none;animation:none}}

"""


CASES = {
    "carrd": ("轻量建站与数字服务", "从小范围客户需求出发，研究如何以单页网站和数字产品提供服务。"),
    "plausible": ("隐私友好型网站分析", "研究订阅软件、技术维护和企业用户付费模式，不默认适合零基础直接创业。"),
    "nerdwallet": ("内容与产品比较平台", "研究成熟信息平台的内容、信任和流量模式；不将历史财报当成个人可复制收益。"),
}

# Editorial research prompts, not company-specific business facts or verified
# recommendations. Fixed, reviewed copy; independent of private listings.
RESEARCH_QUESTIONS = {
    "carrd": (
        "哪些细分客户愿意为单页网站和后续维护付费？",
        "目标客户的实际采购预算、获客渠道及交付时间仍未知。",
        "先访谈少量目标客户，核实是否存在可重复的付费需求。"
    ),
    "plausible": (
        "订阅分析工具解决什么问题，客户为何持续付费？",
        "对新进入者的开发、运维、获客门槛尚无独立验证。",
        "先比较现有工具与客户切换成本，不以原公司收入推导个人收益。"
    ),
    "nerdwallet": (
        "成熟内容比较平台如何通过信任与用户需求提供价值？",
        "获客规模、合规成本及个人复制可能性均缺乏直接证据。",
        "以经营与信任机制为研究对象，不将其列为新手启动推荐。"
    ),
}

SOLUTION_SLUGS = ("ecommerce-visual", "brand-video", "automation", "localization")

SOLUTIONS = (
    ("✦", "AI 电商视觉", "商品图片、品牌海报、视觉素材与批量内容制作。"),
    ("▣", "AI 视频与品牌短片", "短视频、品牌宣传与视频创意工作流。"),
    ("⌘", "AI 企业自动化", "知识库、智能客服与内部流程协作。"),
    ("◎", "AI 出海内容", "多语言创作、品牌内容本地化及海外营销素材。"),
)


def _get_visual() -> str:
    source = VISUAL_SOURCE.read_text(encoding="utf-8")
    hits = re.findall(r'<img src="(data:image/webp;base64,[A-Za-z0-9+/=]+)"', source)
    if len(hits) != 1:
        raise RuntimeError("F1 concept artwork not uniquely found")
    data = base64.b64decode(hits[0].split(",", 1)[1], validate=True)
    if not (data.startswith(b"RIFF") and data[8:12] == b"WEBP"
            and 1_000 < len(data) <= 100_000):
        raise RuntimeError("Unexpected F1 artwork payload")
    return hits[0]


# Clear, source-constrained preview copy, never an audited profit/fit forecast.
# These are short editorial summaries of the existing allowed dossier data.
PROJECT_PREVIEWS = {
    "carrd": {
        "headline": "做单页网站",
        "sub": "帮个人和小商家快速建立展示页面",
        "buyer": "创作者、自由职业者、小商家",
        "revenue": "基础免费，高级功能按年订阅",
        "difficulty": "可以从小范围建站服务试单；不是复制 Carrd",
        "label": "可研究低成本服务",
    },
    "plausible": {
        "headline": "网站数据分析工具",
        "sub": "帮站长看流量、来源和转化",
        "buyer": "站长、网站运营团队",
        "revenue": "按网站流量和功能收订阅费",
        "difficulty": "需要开发、运维与隐私保护能力",
        "label": "技术门槛较高",
    },
    "nerdwallet": {
        "headline": "金融产品比较网站",
        "sub": "帮消费者理解和比较金融产品",
        "buyer": "用户看内容；广告合作伙伴付费",
        "revenue": "广告和商业合作，不代表每笔成交都收佣金",
        "difficulty": "大型平台模式，不建议一人直接照搬",
        "label": "学习商业模式",
    },
}


def render_portal(cases: list[dict]) -> str:
    metrics = public_metrics(cases)
    if {case["id"] for case in cases} != set(PROJECT_PREVIEWS) or len(cases) != 3:
        raise RuntimeError("Only source-admitted cases can enter JIANSHI2 homepage")
    # T08: only these 3 cards change; their content and destination are built
    # deterministically from the same JSON as /projects/. Other homepage
    # modules/metrics/editorial copy remain frozen.
    projects = []
    for project in featured_projects():
        ident = escape(project["id"], quote=True)
        name = escape(project["name"], quote=True)
        summary = escape(project["one_liner_cn"], quote=True)
        amount = escape(usd(project["revenue"]["last_30d"]), quote=True)
        verdict = escape(project["verdict"], quote=True)
        score = escape(str(project["total_score"]), quote=True)
        projects.append(
            '<article class="j2-project" data-t08-id="' + ident + '">'
            '<span class="j2-case-type">' + verdict + ' · 支付API收入样本</span>'
            '<h3>' + name + '</h3><p>' + summary + '</p>'
            '<dl class="j2-project-facts">'
            '<div><dt>近30天收入</dt><dd>' + amount + '</dd></div>'
            '<div><dt>研究结论</dt><dd>' + verdict + '</dd></div>'
            '<div><dt>总分</dt><dd>' + score + '/25</dd></div>'
            '</dl><a class="j2-project-action" href="/projects/'
            + ident + '/">看项目详情 →</a></article>'
        )
    solution_rows = "".join(
        '<article class="j2-solution"><div class="j2-art" aria-hidden="true">'
        + escape(icon) + '</div><div class="j2-solution-body"><h3>'
        + escape(title) + "</h3><p>" + escape(desc)
        + '</p><small>仅供了解方向，尚无平台已交付案例</small>'
        + '<a href="/solutions/' + slug + '/">了解这个方向 →</a></div></article>'
        for (icon, title, desc), slug in zip(SOLUTIONS, SOLUTION_SLUGS)
    )
    shortcut_data = (
        ("◈", "找创业项目", "看商业案例和赚钱方式", "j2-opportunities"),
        ("▤", "企业用 AI", "了解企业可用的方案", "j2-solutions"),
        ("◇", "找业务需求", "尚未开放真实商单", "j2-marketplace"),
        ("♙", "找合作伙伴", "尚未开放入驻", "j2-talent"),
        ("✧", "学 AI 技能", "课程还在筹备", "j2-academy"),
    )
    shortcuts = "".join(
        '<a class="j2-shortcut" href="#' + anchor + '"><i aria-hidden="true">'
        + escape(icon) + "</i><span><strong>" + escape(title)
        + "</strong><small>" + escape(detail)
        + '</small></span><span class="j2-arrow" aria-hidden="true">↗</span></a>'
        for icon, title, detail, anchor in shortcut_data
    )
    image = _get_visual()
    return (
        '<section id="j2" aria-label="见势 2.0 商业机会与解决方案门户">'
        '<div class="j2-mast"><div class="j2-wrap j2-hero">'
        '<div><span class="j2-kicker">JIANSHI · 帮你找创业项目</span>'
        '<h1>发现值得研究的<br><em>商业机会。</em></h1>'
        '<p class="j2-lead">想找个项目做？先看看别人做什么、卖给谁、怎么赚钱。'
        '不仅研究 AI，也关注电商、内容、数字产品和服务等商业模式。</p>'
        '<div class="j2-actions">'
        '<a class="j2-button j2-button--primary" href="#j2-opportunities">直接看项目 ↓</a>'
        '<a class="j2-button" href="/discover/">按方向找项目 →</a></div>'
        '<div class="j2-journey" aria-label="见势三步研究路径">'
        '<span><b>01</b> 发现方向</span><span class="j2-journey-arrow" aria-hidden="true">→</span>'
        '<span><b>02</b> 核查依据</span><span class="j2-journey-arrow" aria-hidden="true">→</span>'
        '<span><b>03</b> 决定下一步</span></div>'
        '<a class="j2-first-service" href="/start/">不知道从哪个方向开始？用 3 个问题生成研究卡 →</a>'
        '<p class="j2-proofnote">先看模式，再看风险。历史案例不代表照着做就能赚钱；概念配图不是项目证明。</p></div>'
        '<div class="j2-visual"><div class="j2-visual-panel" aria-hidden="true"><div class="j2-visual-top">'
        '<span class="j2-visual-led"></span><span>JIANSHI / RESEARCH</span><span>✦</span></div>'
        '<div class="j2-visual-caption"><strong>让每一个想法<br>都有依据。</strong>'
        '<small>Discover · Verify · Decide</small></div></div>'
        '<img width="800" height="650" fetchpriority="high"'
        ' decoding="async" alt="AI 生成的见势 2.0 概念主视觉，非真实项目案例或企业客户"'
        ' src="' + image + '"></div></div></div>'
        '<div class="j2-wrap j2-content">'
        '<section class="j2-section" id="j2-opportunities">'
        '<div class="j2-sectionhead"><div>'
        '<span class="j2-overline">先看项目 · 再做决定</span>'
        '<h2>现在可以看的创业案例</h2>'
        '<p class="j2-muted">直接比较做什么、谁付费、怎么赚钱、要什么能力。</p></div>'
        '<a class="j2-plainlink" href="/projects/">全部案例 →</a></div>'
        '<div class="j2-projects">' + "".join(projects) + '</div>'
        '<p class="j2-simple-notice">目前只展示已有历史经营资料的 3 个案例，'
        '并不代表任何一个可以直接复制盈利。更多项目需要继续核实。</p>'
        '</section>'
        '<div class="j2-after-projects">'
        '<h2>还想看看其他方向？</h2>'
        '<nav class="j2-study-paths" aria-label="创业机会三条研究路径">'
        '<a class="j2-study-path" href="/projects/"><strong>找真实案例</strong>'
        '<span>三个有经营资料的公开案例。</span><small>看案例 →</small></a>'
        '<a class="j2-study-path" href="/research/"><strong>比较商业模式</strong>'
        '<span>看看不同生意一般怎么运作。</span><small>了解六类模式 →</small></a>'
        '<a class="j2-study-path" href="/discover/"><strong>按主题探索</strong>'
        '<span>根据感兴趣的领域浏览内容。</span><small>按方向找 →</small></a>'
        '</nav>'
        '<div class="j2-metrics" aria-label="当前公开研究数量">'
        '<div class="j2-metric"><strong>' + str(metrics["approved_cases"]) + '</strong><span>有历史经营证据的具名案例</span></div>'
        '<div class="j2-metric"><strong>' + str(metrics["verified_launch"]) + '</strong><span>已验证可直接启动的项目</span></div>'
        '<div class="j2-metric"><strong>' + str(metrics["business_models"]) + '</strong><span>已整理的商业模式</span></div>'
        '</div></div>'
        '<div class="j2-after-projects">'
        '<div class="j2-intro"><div><span class="j2-overline">见势的其他板块</span>'
        '<h2>企业 AI 方案、合作与学习</h2>'
        '<p>先放在这里，需要的时候再看。未开放的服务会明确标注。</p></div></div>'
        '<nav class="j2-shortcuts" aria-label="见势 2.0 五大业务入口">' + shortcuts + '</nav>'
        '</div>'
        '<section class="j2-section" id="j2-solutions"><div class="j2-sectionhead">'
        '<div><span class="j2-overline">企业 AI 服务</span><h2>企业想用 AI，可以从哪做起？</h2>'
        '<p class="j2-muted">目前提供四类场景介绍，尚未开放真实服务采购或报价。</p></div>'
        '<a class="j2-plainlink" href="/solutions/">查看企业方案 →</a></div>'
        '<div class="j2-solutions">' + solution_rows + '</div></section>'
        '<div class="j2-two">'
        '<section class="j2-panel" id="j2-marketplace"><span class="j2-status">商机大厅 · 建设中</span>'
        '<h2>以后可以在这里找客户需求。</h2>'
        '<p class="j2-muted">尚未开放真实商单。当前不展示虚构企业、订单和报价。</p>'
        '<a href="/marketplace/">了解企业需求应该怎么写 →</a></section>'
        '<section class="j2-panel j2-panel--dark" id="j2-talent">'
        '<span class="j2-status">合作伙伴 · 建设中</span>'
        '<h2>以后可以在这里找合作团队。</h2>'
        '<p class="j2-muted">目前未开放真实入驻、自动匹配或项目投递。</p>'
        '<a href="/talent/">准备自己的作品介绍 →</a></section>'
        '</div><section class="j2-academy" id="j2-academy">'
        '<span class="j2-overline" style="color:#bdb2ff">AI 技能学习 · 筹备中</span>'
        '<h2>想学 AI？先了解可以做什么。</h2>'
        '<p>课程由团队后续自主制作并上传，目前只展示学习路线，暂时没有上线课程。</p>'
        '<div class="j2-tags"><span>电商图片</span><span>AI 视频</span>'
        '<span>企业自动化</span><span>做产品</span><span>测试创业想法</span></div>'
        '<a class="j2-button" style="margin-top:22px" href="/academy/">查看学习方向 →</a></section>'
        '</div></section>'
    )



def integrate(portal_ready_html: str, admitted_cases: list[dict]) -> str:
    if (portal_ready_html.count('<main id="top">') != 1
            or portal_ready_html.count("</style>") != 1
            or portal_ready_html.count('id="recommendations"') != 1
            or portal_ready_html.count('id="ring"') != 1
            or portal_ready_html.count('id="lb"') != 1
            or portal_ready_html.count('id="grid"') != 1
            or 'id="j2"' in portal_ready_html):
        raise RuntimeError("Cannot safely integrate V2 portal into production research home")
    integrated = portal_ready_html.replace("</style>", STYLE + "</style>", 1)
    integrated = integrated.replace('<main id="top">', '<main id="top">' + render_portal(admitted_cases), 1)
    # Preserve older 3D, gallery, archival research and themes, but don't force
    # users to dismiss the original editorial splash before using the new site.
    if integrated.count('<body class="locked">') != 1:
        raise RuntimeError("Legacy splash body contract changed")
    integrated = integrated.replace('<body class="locked">', '<body>', 1)
    # Replace legacy three-entry overlay navigation only *after* P4.39's
    # independent gate has checked it in public_home().
    start = '<nav aria-label="主要导航">'
    if integrated.count(start) != 1:
        raise RuntimeError("Legacy navigation lost before V2 link integration")
    a = integrated.index(start) + len(start)
    b = integrated.index("</nav>", a)
    navigation = (
        '<a href="#j2-opportunities">商业机会</a>'
        '<a href="#j2-solutions">企业解决方案</a>'
        '<a href="#j2-marketplace">商机大厅</a>'
        '<a href="#j2-talent">人才与服务商</a>'
        '<a href="#j2-academy">AI 学院</a>'
        '<a href="#recommendations">项目研究建议</a>'
        '<a href="#models">商业模式</a>'
        '<a href="/sources/">数据来源</a>'
    )
    integrated = integrated[:a] + navigation + integrated[b:]
    # The production homepage's document metadata must describe JIANSHI 2.0,
    # not the earlier research-only portal. Keep the reviewed source unchanged.
    old_title = "<title>见势 JIANSHI｜发现海外项目，看懂一门生意</title>"
    old_description = ('<meta name="description" content="探索海外真实项目和商业模式，'
                       '了解它们提供什么、向谁收费、如何运作，以及哪些经营事实还需要进一步核实。">')
    title = "见势｜找创业项目，看懂怎么赚钱"
    description = ("直接看创业案例：做什么、谁付钱、怎么赚钱、需要什么能力。"
                   "所有案例仅供参考，不承诺盈利；也有中小企业 AI 应用方向。")
    if integrated.count(old_title) != 1 or integrated.count(old_description) != 1:
        raise RuntimeError("Homepage metadata source contract changed")
    integrated = integrated.replace(old_title, "<title>" + escape(title) + "</title>", 1)
    integrated = integrated.replace(
        old_description,
        '<meta name="description" content="' + escape(description, quote=True) + '">',
        1,
    )
    if integrated.count("</head>") != 1:
        raise RuntimeError("Invalid main document head")
    social = (
        '<meta property="og:type" content="website">'
        '<meta property="og:title" content="' + escape(title, quote=True) + '">'
        '<meta property="og:description" content="' + escape(description, quote=True) + '">'
        '<meta property="og:url" content="https://jianshi-bua.pages.dev/">'
        '<meta name="twitter:card" content="summary">'
    )
    integrated = integrated.replace("</head>", social + "</head>", 1)
    return integrated
