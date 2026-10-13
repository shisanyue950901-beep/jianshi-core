#!/usr/bin/env python3
"""Publish independently sourced *project-level* evidence, not industry inference.

Use vetted first-party editorial case JSON and the two original concept covers.
Never map private marketplace disclosures to named companies.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from collections import Counter
from p425_public_admission import eligible_cases
from p426_evidence_digest import derive_digest
from p440_decision_report import decision_data, render_decision_panel, render_founder_workbook
from p442_jianshi2_live_home import PROJECT_PREVIEWS
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "web/prototypes/p412e/index.html"
P413 = ROOT / "config/p413_public_project_library.json"
P415 = ROOT / "config/p415_public_case_growth.json"
RESEARCH = ROOT / "config/p424_project_research_evidence.json"
DEST = ROOT / "web/dist/projects"
SITE = "https://jianshi-bua.pages.dev"
LEVELS = {"regulatory_filing":4,"founder_historical":3,"platform_attribution":2,"first_party_offer":1}
LABELS = {4:"监管历史财务披露",3:"创始人／企业历史自述",2:"第三方平台旁证",1:"官网产品与收费依据"}

ORIGINAL_SOURCES = {
    "easlo": (
        "https://www.easlo.co/",
        "https://www.easlo.co/templates",
        "https://www.notion.com/templates/creators/easlo",
        "Notion 官方创作者页面可交叉核对模板与创作者关联；不证明销量。"),
    "louise": (
        "https://www.authorlouiselennox.com/",
        "https://www.authorlouiselennox.com/books",
        "https://www.aboutamazon.com/news/books-and-authors/how-these-authors-found-success-with-amazon-kindle-direct-publishing",
        "亚马逊早期作者专题可佐证 Kindle 直接出版经历；不能推断当前版税。"),
}
MODEL_LABELS = {
    "saas": "订阅软件", "digital": "数字产品", "content": "内容与推荐",
    "kdp": "图书出版", "fba": "实体产品", "agency": "专业服务",
}

# Reviewed audience labels only for the three source-admitted public cases.
# Do not conflate a product's readers/users with its actual commercial payers.
PAYING_PARTIES = {
    "carrd": "需要专业功能的个人或小商家（按年订阅）",
    "plausible": "购买网站统计订阅服务的站长或运营团队",
    "nerdwallet": "网站广告合作伙伴；读者不等于广告付款方",
}
CSS = """
:root{color-scheme:light;--bg:#f7f8fc;--ink:#1c2a44;--muted:#566581;--line:#dce3ee;--panel:#ffffff;--accent:#6254b9}
html[data-theme=dark]{color-scheme:dark;--bg:#0c1222;--ink:#f0f1fd;--muted:#b8bfd4;--line:#424b66;--panel:#161e31;--accent:#b7aaff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.8 Inter,-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
a{color:var(--accent);text-underline-offset:4px}a:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
header,main,footer{max-width:1050px;margin:auto;padding-inline:clamp(18px,4vw,52px)}
header{display:flex;align-items:center;justify-content:space-between;gap:15px;padding-block:23px;border-bottom:1px solid var(--line)}
.logo{font:500 27px Georgia,"Songti SC",serif;color:var(--ink);text-decoration:none}
header nav{display:flex;gap:16px;font-size:13px;align-items:center}header button{background:var(--panel);color:var(--ink);border:1px solid var(--line);font:inherit;padding:8px 12px;min-height:42px}main{padding-block:65px 90px}
.kicker{font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-size:12px}
h1,h2,h3{font-weight:500}h1{font:500 clamp(39px,5vw,68px)/1.18 Georgia,"Songti SC",serif;letter-spacing:-.03em;margin:16px 0 25px}
h2{font-size:25px;line-height:1.4}h3{font-size:17px;margin:0 0 7px}
.lead{font-size:17px;line-height:1.9;color:var(--muted);max-width:760px}
.notice{border-left:4px solid var(--accent);background:var(--panel);padding:15px 20px;margin:30px 0;font-size:14px}
.statusgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:35px 0}
.status{border:1px solid var(--line);background:var(--panel);padding:18px}.status b{display:block;font-size:16px;color:var(--ink)}.status small{display:block;color:var(--muted);margin-top:6px;font-size:12px}
.status.pending b{color:var(--muted)}
.section{border-top:1px solid var(--line);margin-top:45px;padding-top:23px}
.section p,.section li{font-size:15px}.section p{color:var(--muted)}.section ul{padding-left:23px}
.links{display:flex;flex-wrap:wrap;gap:12px}.links a{border:1px solid var(--line);background:var(--panel);padding:12px 16px;font-weight:600;font-size:13px}
.directory{display:grid;gap:12px;margin:24px 0}.directory a{display:block;color:var(--ink);background:var(--panel);border:1px solid var(--line);padding:18px 20px;text-decoration:none}
.directory a:hover,.directory a:focus-visible{border-color:var(--accent)}
.directory a strong{font-size:19px;display:block}.directory a small{color:var(--accent);font-weight:700;font-size:12px;display:block;margin-bottom:5px}.sort-controls{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0 8px}.sort-controls button{padding:11px 15px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:13px}.sort-controls button[aria-pressed=true]{border:2px solid var(--accent);background:color-mix(in srgb,var(--accent) 11%,var(--bg));font-weight:700}.directory a span{font-size:13px;color:var(--muted);display:block;margin-top:5px}
input[type=search]{width:100%;border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:14px;font:16px sans-serif;max-width:600px}
footer{padding-block:26px 45px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
@media(max-width:590px){.statusgrid{grid-template-columns:1fr}header nav{gap:8px}.lead{font-size:15px}.links{display:grid}}
.digest{border:1px solid var(--line);background:var(--panel);padding:clamp(18px,3vw,28px);margin:29px 0}
.digest h2{font:500 clamp(24px,3vw,30px)/1.35 Georgia,"Songti SC",serif;margin:0 0 18px}
.digestgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 22px}
.digestgrid p{margin:0;font-size:14px;line-height:1.75;color:var(--ink)}
.digestgrid b{display:block;font-size:12px;letter-spacing:.05em;color:var(--accent);margin-bottom:6px}
.digest-meta{margin:17px 0 0;color:var(--muted);font-size:12px}
.digest-proof{border-left:3px solid var(--accent);padding-left:12px}
.directory a .digestmini{display:block;margin:12px 0 0;border-top:1px solid var(--line);padding-top:12px}
.directory a .digestmini p{margin:6px 0;color:var(--ink);font-size:13px;line-height:1.65}
.directory a .digestmini b{color:var(--accent);font-weight:650}
.directory a .digestmini small{font-size:12px;color:var(--muted);margin-top:5px}
@media(max-width:600px){.digestgrid{grid-template-columns:1fr}.digest{padding:18px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
/* P4.40 static decision file: readable, no JS or external dependencies. */
.decision-report{border-top:3px solid var(--accent);background:var(--panel);border-inline:1px solid var(--line);border-bottom:1px solid var(--line);padding:clamp(18px,3.6vw,34px);margin:30px 0 37px;scroll-margin-top:90px}
.decision-eyebrow{font-size:11px;letter-spacing:.16em;color:var(--accent);font-weight:700}
.decision-report h2{font:500 clamp(24px,3vw,34px)/1.35 Georgia,"Songti SC",serif;margin:9px 0 11px}
.decision-intro{color:var(--muted);max-width:66ch;font-size:14px;line-height:1.75;margin:0 0 22px}
.decision-verdict{border-left:4px solid var(--accent);background:color-mix(in srgb,var(--accent) 7%,var(--bg));padding:16px 18px;margin:0 0 21px}
.decision-verdict__label{display:block;color:var(--muted);font-size:12px;margin-bottom:5px}
.decision-verdict strong{display:block;font-size:clamp(16px,2vw,21px);line-height:1.45}
.decision-verdict small{display:block;color:var(--muted);line-height:1.7;margin-top:6px;font-size:12px}
.decision-columns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.decision-columns article{min-width:0;border:1px solid var(--line);padding:17px}
.decision-columns h3,.decision-proof h3,.decision-action h3{margin:0 0 9px;color:var(--ink);font-size:17px}
.decision-columns article h3:not(:first-child){margin-top:20px}
.decision-columns p,.decision-proof p,.decision-action p{line-height:1.75;font-size:14px;margin:6px 0;color:var(--ink)}
.decision-columns small{display:block;color:var(--muted);line-height:1.7;margin-top:9px;font-size:12px}
.decision-proof,.decision-action{border-top:1px solid var(--line);margin-top:23px;padding-top:20px}
.decision-proof a{display:inline-flex;align-items:center;min-height:44px;font-size:14px;font-weight:650;margin-top:10px}
.decision-action ol{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;list-style-position:inside;padding:0;margin:12px 0 0}
.decision-action li{border:1px solid var(--line);padding:14px 15px;min-width:0;color:var(--ink)}
.decision-action li::marker{font-size:13px;color:var(--accent)}
.decision-action li b{font-size:14px}
.decision-action li p{font-size:13px;color:var(--muted)}
.decision-disclaimer{font-size:12px;line-height:1.75;color:var(--muted);margin:21px 0 0}
.directory a .decision-mini{display:block;border-top:1px solid var(--line);padding-top:11px;margin-top:11px;font-size:12px;line-height:1.8;color:var(--muted)}
.directory a .decision-mini b{color:var(--accent)}
.notice summary{cursor:pointer;font-size:14px;font-weight:700;min-height:38px;padding:6px 0}.notice[open] summary{margin-bottom:14px}.directory a .digestmini p{font-size:13px;color:var(--ink)}.directory a .decision-mini{font-size:12px}
.decision-report a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media(max-width:720px){.decision-action ol{grid-template-columns:1fr}.decision-columns{grid-template-columns:1fr}.decision-action li{padding:13px}}
@media(max-width:590px){.decision-report{margin:18px 0 28px}.decision-intro{font-size:13px}}
/* B1-A03: hand-fillable, print-friendly founder validation worksheet.
   Source reviewed, never captured in browser storage or sent to a server. */
.decision-workbook-link{display:inline-flex;margin-top:13px;align-items:center;min-height:44px;font-size:14px;font-weight:700}
.founder-workbook{scroll-margin-top:98px;border:2px solid var(--accent);background:var(--panel);padding:clamp(18px,3.3vw,32px);margin-top:45px}
.founder-workbook h2{margin:9px 0 14px;font-size:clamp(22px,2.7vw,31px)}
.workbook-intro,.workbook-fineprint{font-size:13px;line-height:1.8;color:var(--muted)}
.workbook-steps{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px;margin-top:23px}
.workbook-step{border:1px solid var(--line);background:var(--bg);padding:19px;min-width:0}
.workbook-step>span{display:block;color:var(--accent);font-size:11px;font-weight:750;letter-spacing:.08em}
.workbook-step h3{margin:9px 0 12px;font-size:18px;line-height:1.5}
.workbook-step p{font-size:13px;line-height:1.8;color:var(--ink)}
.workbook-blank{font-size:12px;font-weight:650;color:var(--ink);margin-top:15px;border-top:1px dashed var(--line);padding-top:12px}
.workbook-blank span{display:block;overflow-wrap:anywhere;color:var(--muted);letter-spacing:.08em;line-height:2.2}
@media(max-width:700px){.workbook-steps{grid-template-columns:1fr}.workbook-step{padding:16px}}
@media print{.founder-workbook{break-before:page;page-break-before:always;box-shadow:none;color:#111;background:#fff;border-color:#777}.workbook-steps{grid-template-columns:repeat(2,minmax(0,1fr))}.workbook-step{break-inside:avoid;page-break-inside:avoid;background:#fff}.workbook-blank span{line-height:3}.decision-workbook-link{display:none}}
/* Founder first: deep sources and long worksheets are voluntary reading. */
.decision-next{background:color-mix(in srgb,var(--accent) 6%,var(--panel));padding:15px 18px;border:1px solid var(--line);margin:0}
.decision-next strong{display:block;color:var(--accent);font-size:13px;margin-top:9px}
.decision-next strong:first-child{margin-top:0}
.decision-next p{margin:4px 0 12px;font-size:15px;line-height:1.65;color:var(--ink)}
.decision-report{margin:22px 0 28px;padding:clamp(16px,2.7vw,25px)}
.decision-verdict{margin:0 0 12px}
.decision-more,.dossier-more,.workbook-fold{border:1px solid var(--line);background:var(--panel);border-radius:12px;margin:18px 0;padding:0 18px 12px}
.decision-more summary,.dossier-more summary,.workbook-fold summary{cursor:pointer;padding:15px 4px;min-height:48px;font-size:15px;font-weight:700;color:var(--accent)}
.decision-more summary:focus-visible,.dossier-more summary:focus-visible,.workbook-fold summary:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.decision-more[open] summary,.dossier-more[open] summary,.workbook-fold[open] summary{border-bottom:1px solid var(--line);margin-bottom:15px}
.decision-more .decision-columns{margin-top:14px}
.dossier-more>.section:first-of-type{border-top:0;margin-top:5px}
.dossier-more .section{margin-top:25px}
.dossier-more .notice{margin:15px 0}
.dossier-more .statusgrid{margin:20px 0}
.workbook-fold .founder-workbook{margin:12px 0 4px;border:0;scroll-margin-top:80px;padding:12px 0}
.case-back{display:inline-flex;margin:0 0 5px;align-items:center;min-height:38px;text-decoration:none;font-size:13px;font-weight:700}
@media(max-width:590px){main{padding-block:26px 60px}h1{font-size:clamp(32px,7vw,45px);margin:10px 0 14px}.lead{font-size:14px;line-height:1.6}.digest{margin:14px 0;padding:15px}.digestgrid{gap:11px}.decision-report{margin:14px 0;padding:15px}.decision-more,.dossier-more,.workbook-fold{padding:0 12px 8px;margin:12px 0}.decision-next p{font-size:14px}.statusgrid{gap:8px}}
@media print{.dossier-more:not([open]),.workbook-fold:not([open]),.decision-more:not([open]){display:none}}

/* B1-P0: concise project cards using the original blue-violet palette. */
.directory{grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.directory a.case-card{display:flex;flex-direction:column;gap:11px;min-width:0;padding:21px;border-radius:16px}
.directory a.case-card strong{font-size:20px;line-height:1.4;overflow-wrap:anywhere}
.directory a.case-card small{margin:0;color:var(--accent);line-height:1.45}
.directory a .case-facts{display:grid;gap:10px;margin-top:4px}
.directory a .case-facts p{border-top:1px solid var(--line);padding-top:8px;margin:0;font-size:13px;line-height:1.6;color:var(--ink)}
.directory a .case-facts b{display:block;margin-bottom:2px;color:var(--accent);font-size:12px}
.directory a .case-action{margin-top:auto;padding:10px 13px;border-radius:10px;min-height:44px;background:color-mix(in srgb,var(--accent) 10%,var(--panel));color:var(--accent);font-weight:700}
.case-browse{margin:20px 0 12px;font-size:14px;font-weight:700}
.case-browse a{display:inline-flex;align-items:center;min-height:44px}
@media(max-width:900px){.directory{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:650px){header{flex-wrap:wrap;padding-block:14px}header nav{width:100%;flex-wrap:wrap;gap:8px 12px}.directory{grid-template-columns:1fr;margin-top:15px}.directory a.case-card{padding:18px}.case-browse{margin:10px 0}}


/* B1: company directory and evidence pages retain factual contents, update look. */
body{font-family:"PingFang SC","Microsoft YaHei",Inter,system-ui,sans-serif}
header{max-width:1180px;padding-block:17px;min-height:72px}
.logo{font:850 22px/1.4 "PingFang SC","Microsoft YaHei",Inter,system-ui,sans-serif;letter-spacing:-.04em}
header nav a{font-weight:700;text-decoration:none;font-size:13px;min-height:44px;display:inline-flex;align-items:center}
header nav a:hover{color:var(--accent)}header button{border-radius:11px;cursor:pointer}
main{padding-block:38px 85px}
h1,h2,h3{font-family:"PingFang SC","Microsoft YaHei",Inter,system-ui,sans-serif}
h1{font-size:clamp(35px,5vw,56px);font-weight:850;letter-spacing:-.048em;line-height:1.22}
h2{font-weight:800;letter-spacing:-.03em}
.case-directory-hero{position:relative;isolation:isolate;overflow:hidden;border-radius:24px;
 padding:36px clamp(23px,4vw,46px) 32px;margin:0 0 25px;
 background:radial-gradient(ellipse 50% 130% at 90% 7%,#6156ab65,transparent 72%),
 radial-gradient(ellipse 43% 105% at 4% 100%,#23689a55,transparent 80%),
 linear-gradient(130deg,#0b1528,#182849 70%,#231d49);
 box-shadow:0 19px 42px #1a32622a;color:#f3f6ff}
.case-directory-hero:before{content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;
 background-image:linear-gradient(#abc2ff0c 1px,transparent 1px),linear-gradient(90deg,#abc2ff0c 1px,transparent 1px);
 background-size:42px 42px;mask-image:linear-gradient(90deg,transparent,#000b)}
.case-directory-hero .kicker{color:#c6c8ff;background:#7e79ef26;border:1px solid #a4a7ff53;
 border-radius:50px;padding:5px 12px;display:inline-flex;font-size:11px}
.case-directory-hero h1{color:#fff;max-width:760px;font-size:clamp(34px,4.7vw,55px);margin:15px 0 14px}
.case-directory-hero .lead{color:#c7d3e8;font-size:15px;line-height:1.75;max-width:700px}
.case-directory-hero .case-browse{margin:13px 0 0}
.case-directory-hero .case-browse a{color:#fff;text-decoration:none;min-height:44px;border-radius:11px;
 background:linear-gradient(110deg,#8265e9,#5089ee);padding:10px 18px;box-shadow:0 7px 20px #4341ac51}
.case-directory-hero .case-browse a:hover{filter:brightness(1.09)}
.case-directory-proof{display:flex;gap:9px;flex-wrap:wrap;margin-top:19px}
.case-directory-proof span{display:inline-flex;align-items:center;min-height:31px;
 border:1px solid #a6b5e844;background:#f1f2ff11;color:#dce6fa;
 padding:5px 11px;border-radius:25px;font-size:11px}
.directory{gap:16px}
.directory a.case-card{border-radius:19px;border:1px solid var(--line);
 padding:23px;box-shadow:0 5px 22px #273f7210;
 background:var(--panel);transition:border-color .18s,transform .18s,box-shadow .18s}
.directory a.case-card:hover,.directory a.case-card:focus-visible{border-color:var(--accent);
 box-shadow:0 17px 36px #293f8020;transform:translateY(-3px)}
.directory a.case-card small{align-self:flex-start;border-radius:24px;
 padding:5px 10px;background:color-mix(in srgb,var(--accent) 11%,var(--panel));
 color:var(--accent);font-size:11px;font-weight:750}
.directory a.case-card strong{font-size:20px;line-height:1.4;letter-spacing:-.025em}
.directory a .case-facts{margin-top:7px;gap:8px}
.directory a .case-facts p{padding-top:8px;font-size:12px;line-height:1.6}
.directory a .case-facts b{font-size:11px}
.directory a .case-action{display:flex;align-items:center;justify-content:space-between;
 margin-top:auto;padding:11px 14px;border-radius:11px;
 background:color-mix(in srgb,var(--accent) 12%,var(--panel));
 color:var(--accent);font-size:13px;font-weight:800}
.case-detail-hero{border:1px solid var(--line);padding:27px clamp(20px,3.5vw,34px);
 border-radius:22px;background:linear-gradient(130deg,
 color-mix(in srgb,var(--accent) 9%,var(--panel)),var(--panel) 65%);margin:8px 0 19px}
.case-detail-hero .kicker{display:inline-block;margin:0;padding:4px 10px;
 border:1px solid color-mix(in srgb,var(--accent) 32%,var(--panel));border-radius:30px}
.case-detail-hero h1{margin:14px 0 10px;max-width:840px;
 font-size:clamp(32px,4.3vw,48px);font-weight:850}
.case-detail-hero .lead{font-size:15px;line-height:1.75;margin:0;max-width:750px}
.case-detail-proof{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.case-detail-proof span{display:inline-flex;min-height:30px;align-items:center;border:1px solid var(--line);
 border-radius:24px;padding:4px 10px;font-size:11px;color:var(--muted);background:var(--panel)}
.digest,.decision-report,.decision-more,.dossier-more,.workbook-fold{border-radius:17px}
.digest{box-shadow:0 6px 24px #2a3d7710}
.digest h2,.decision-report h2{font-family:"PingFang SC","Microsoft YaHei",Inter,system-ui,sans-serif;font-weight:800}
.digestgrid{gap:14px}
.digestgrid p{border:1px solid var(--line);border-radius:12px;padding:13px;min-width:0}
.digestgrid .digest-proof{border-left:3px solid var(--accent)}
.decision-report{box-shadow:0 5px 24px #2a3d7710}
@media(max-width:650px){
 header{min-height:60px}main{padding-block:24px 65px}
 .case-directory-hero{padding:25px 20px;margin-bottom:12px;border-radius:19px}
 .case-directory-hero h1{font-size:clamp(32px,8vw,44px)}
 .case-directory-hero .lead{font-size:13px;line-height:1.7}
 .case-directory-hero:before{background-size:32px 32px}
 .case-directory-proof{margin-top:12px}
 .directory a.case-card{padding:19px}
 .case-detail-hero{padding:20px;border-radius:17px}
 .case-detail-hero h1{font-size:clamp(29px,7.5vw,40px)}
 .case-detail-hero .lead{font-size:13px}
 .digestgrid p{padding:10px}
}
@media(prefers-reduced-motion:reduce){.directory a.case-card{transition:none;transform:none!important}}

"""

def txt(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)

def safe_url(url: object) -> str:
    if not isinstance(url, str) or any(ord(c) < 32 for c in url):
        raise ValueError("Unapproved public URL")
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise ValueError("Only HTTPS first-party URLs are allowed")
    return url

def parse_cases() -> list[dict]:
    # Cover items are editorial fields in original public HTML, not private data.
    source = SOURCE.read_text(encoding="utf-8")
    found = re.search(r"const ITEMS=(\[.*?\]);\s*ITEMS\.forEach", source, re.S)
    if not found:
        raise RuntimeError("Original cover registry changed")
    originals = json.loads(found.group(1))[:2]
    if {x.get("id") for x in originals} != set(ORIGINAL_SOURCES):
        raise RuntimeError("Unexpected original cover profiles")
    cases = []
    for item in originals:
        home, evidence, extra, note = ORIGINAL_SOURCES[item["id"]]
        if f"officialHomeUrl:'{home}',sourceUrl:'{evidence}'" not in source:
            raise RuntimeError("Public homepage source mismatches approved registry")
        cases.append({
            **{k: v for k, v in item.items() if k != "image"},
            "officialHomeUrl": home, "sourceUrl": evidence,
            "additionalEvidenceUrl": extra, "additionalEvidenceNote": note,
            "verifiedOn": "2026-10-08",
        })
    for path in [P413, P415]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("public_policy", {}).get("no_unverified_profit"):
            raise RuntimeError("Case batch cannot pass publication policy")
        cases.extend({**x, "verifiedOn": data["verified_on"]} for x in data["cases"])
    if len(cases) != 20 or len({x["id"] for x in cases}) != 20:
        raise RuntimeError("Expected exactly 20 distinct named research profiles")
    for x in cases:
        if not re.fullmatch(r"[a-z0-9-]{2,60}", x["id"]):
            raise RuntimeError("Unsafe project slug")
        if x.get("kind") != "case" or x.get("model") not in MODEL_LABELS:
            # First two are explicitly associated to models after page data.
            if x["id"] == "easlo":
                x["model"] = "digital"
            elif x["id"] == "louise":
                x["model"] = "kdp"
            else:
                raise RuntimeError("Unknown editorial classification")
        for key in ["officialHomeUrl", "sourceUrl"]:
            safe_url(x[key])
        if x.get("additionalEvidenceUrl"):
            safe_url(x["additionalEvidenceUrl"])
        for key in ["offer", "buyer", "revenue", "facts", "unknowns"]:
            if not x.get(key):
                raise RuntimeError("Missing required first-party or unknown evidence")
    evidence=json.loads(RESEARCH.read_text(encoding="utf-8"))
    if evidence.get("version")!="P4.24_RESEARCH_EVIDENCE_V1":
        raise RuntimeError("Unreviewed external evidence version")
    ids=set()
    for record in evidence["additional_evidence"]:
        case_id=record.get("id")
        if case_id in ids or case_id not in {c["id"] for c in cases}:
            raise RuntimeError("Duplicate or unknown named-company evidence")
        ids.add(case_id)
        if record.get("tier") not in LEVELS or record["tier"]=="first_party_offer":
            raise RuntimeError("Incorrect external attribution tier")
        safe_url(record["source_url"])
        for key in ("source_type","claim","period","financial_status","next_research"):
            if not isinstance(record.get(key),str) or len(record[key])<7:
                raise RuntimeError("Insufficient provenance for external finding")
        if record.get("published_on") is not None:
            import datetime
            datetime.date.fromisoformat(record["published_on"])
        match=next(x for x in cases if x["id"]==case_id)
        match["research_evidence"]=record
    for x in cases:
        record=x.get("research_evidence")
        x["evidence_level"]=LEVELS[record["tier"]] if record else 1
    return cases

THEME_JS = """<script>(()=>{'use strict';const html=document.documentElement,button=document.getElementById('themeToggle');let current='light';try{if(localStorage.getItem('jianshi-theme')==='dark')current='dark'}catch(_){}function apply(next,persist){current=next;html.dataset.theme=next;button.textContent=next==='light'?'深色模式':'浅色模式';button.setAttribute('aria-pressed',String(next==='dark'));if(persist)try{localStorage.setItem('jianshi-theme',next)}catch(_){}}apply(current,false);button.addEventListener('click',()=>apply(current==='light'?'dark':'light',true));})();</script>"""

def shell(title: str, desc: str, body: str, canonical: str) -> str:
    return f"""<!doctype html><html lang="zh-CN" data-theme="light"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="referrer" content="no-referrer"><meta name="description" content="{txt(desc)}">
<title>{txt(title)}｜见势 JIANSHI</title><link rel="canonical" href="{txt(SITE+canonical)}">
<style>{CSS}</style></head><body><header><a class="logo" href="/">见势 JIANSHI</a>
<nav aria-label="页面导航"><a href="/discover/">找项目</a><a href="/projects/">公司案例</a><a href="/">首页</a><button id="themeToggle" type="button" aria-pressed="false">深色模式</button></nav></header>
<main>{body}</main><footer>见势 · 商业研究信息，不构成财务审计、投资建议或收益承诺。<a href="/privacy/">隐私说明</a></footer>{THEME_JS}</body></html>"""

def paragraphs(items: list[str]) -> str:
    return "<ul>"+"".join(f"<li>{txt(x)}</li>" for x in items)+"</ul>"

def project_page(case: dict) -> str:
    slug, name = case["id"], case["title"]
    more = ""
    if case.get("additionalEvidenceUrl"):
        more = f'<a href="{txt(safe_url(case["additionalEvidenceUrl"]))}" target="_blank" rel="noopener noreferrer">官方第三方交叉依据 ↗</a>'
    audit = case.get("research_evidence")
    if audit:
        tier = case["evidence_level"]
        published = audit.get("published_on") or audit["period"]
        source = txt(safe_url(audit["source_url"]))
        audited_section = (
            '<section class="section"><h2>这家企业公开过哪些经营资料？</h2>'
            f'<p><b>资料来源：</b>{txt(LABELS[tier])}。'
            f'<b>资料时间：</b>{txt(published)}（不代表现在的经营情况）</p>'
            f'<p>{txt(audit["claim"])}</p>'
            f'<p><a href="{source}" target="_blank" rel="noopener noreferrer">查看可归属的原始经营证据 ↗</a></p>'
            f'<p><b>下一步主动核查：</b>{txt(audit["next_research"])}</p></section>'
        )
    else:
        audited_section = (
            '<section class="section"><h2>当前补证进度</h2><p>'
            '已整理项目官网及公开产品／收费说明，尚未取得可明确归属于该公司的'
            '监管申报、创始人经营披露或独立平台经营旁证。继续主动核实，'
            '暂不推断客户量和利润。</p></section>'
        )
    if audit and audit["tier"] == "regulatory_filing":
        finance_tile='<div class="status"><b>这家公司有历史财报</b><small>2025 年公开财报，不代表当前业绩或你能获得的利润</small></div>'
        findings_intro="存在可归属的历史监管申报财务，但不代表最新经营表现、单一产品利润或获客成本。"
        finance_boundary="可核实 2025 年公司合并财报的历史财务；当前业绩、业务线及可复制性仍需研究。"
    elif audit and audit["tier"] == "founder_historical":
        finance_tile='<div class="status pending"><b>企业曾公开谈过收入</b><small>这是企业自己的历史说法，未经过独立财务核实，也不是当前收入</small></div>'
        findings_intro="找到可归属的创始人或企业历史经营自述，但尚未独立财务审计，不能当成当前净利润。"
        finance_boundary="有历史公开收入自述，但未独立审计，不能计算当前净利润或投资回报。"
    else:
        finance_tile='<div class="status pending"><b>实际赚多少钱还不清楚</b><small>还没有可以独立核实的成本和利润资料</small></div>'
        findings_intro="项目公开展示产品／服务及收费说明，但交易、净利与获客表现仍缺独立核验。"
        finance_boundary="仍未取得该企业自身可独立核实的财务经营数据。"
    digest = derive_digest(case)
    decision_html = render_decision_panel(decision_data(case))
    workbook_html = render_founder_workbook(case)
    summary_box = (
        '<section class="digest" aria-label="项目概况"><h2>30 秒看懂这门生意</h2>'
        '<div class="digestgrid">'
        f'<p><b>做什么？</b>{txt(digest.offer)}</p>'
        f'<p><b>谁付钱？</b>{txt(PAYING_PARTIES[slug])}</p>'
        f'<p><b>怎么收费？</b>{txt(digest.revenue)}</p>'
        f'<p class="digest-proof"><b>什么还不确定？</b>{txt(digest.limitation)}</p>'
        '</div>'
        f'<p class="digest-meta">公开资料的时间：{txt(digest.period)} · '
        f'<a href="{txt(safe_url(digest.source_url))}" target="_blank" rel="noopener noreferrer">'
        '查看原始经营依据 ↗</a></p></section>'
    )
    body = f"""<a class="case-back" href="/projects/">← 返回项目列表</a>
<section class="case-detail-hero" aria-label="历史公司案例概览">
<span class="kicker">看看别人怎么做生意</span>
<h1>{txt(name)}</h1><p class="lead">{txt(case["desc"])}</p>
<div class="case-detail-proof" aria-label="研究资料边界"><span>历史经营资料</span>
<span>不等于创业收益预测</span><span>建议核查来源和成本</span></div></section>
{summary_box}
{decision_html}
<details class="dossier-more" id="case-details">
<summary>查看资料来源、成本和更多风险说明</summary>
<div class="notice"><b>先提醒：</b>{txt(findings_intro)} 这家企业以前的经营结果，不代表你照着做也能赚钱。</div>
<p><b>找到什么经营证据？</b>{txt(digest.evidence)}</p>
<p><b>还不能证明什么？</b>{txt(digest.limitation)}</p>
<div class="statusgrid" aria-label="项目商业验证状态">
<div class="status"><b>产品／服务：有官方依据</b><small>可进入对应官网或产品页核对公开供应</small></div>
<div class="status"><b>收费机制：有公开说明</b><small>标价或收费方案不代表已成交、已收到款项</small></div>
<div class="status pending"><b>真实交易／客户：待独立核实</b><small>没有可证明实际销量、续费率或成交规模的项目级证据</small></div>
{finance_tile}
</div>
<section class="section"><h2>卖什么产品或服务？</h2><p>{txt(case["offer"])}</p>
<h3>谁可能购买？</h3><p>{txt(case["buyer"])}</p>
<h3>公开描述的收费方式</h3><p>{txt(case["revenue"])}</p></section>
<section class="section"><h2>这些信息从哪里来？</h2>{paragraphs(case["facts"])}
<div class="links"><a href="{txt(safe_url(case["officialHomeUrl"]))}" target="_blank" rel="noopener noreferrer">打开项目官方网站 ↗</a>
<a href="{txt(safe_url(case["sourceUrl"]))}" target="_blank" rel="noopener noreferrer">打开产品／收费核对依据 ↗</a>{more}</div>
{f'<p>{txt(case["additionalEvidenceNote"])}</p>' if more else ''}
<p>依据类别：项目自身官网/公开说明；第三方平台资料如有则单独标注。证据页面只支持它明确展示的事实，不证明营业额。</p></section>
{audited_section}
<section class="section"><h2>需要做哪些事，会花哪些钱？</h2>
<h3>需要做什么</h3><p>{txt(case["process"])}</p>
<h3>可能发生哪些成本</h3><p>{txt(case["cost"])}</p>
<p>以上属于编辑性经营拆解，不代表已获得该企业内部成本表。</p></section>
<section class="section"><h2>哪些地方还不确定？</h2>{paragraphs(case["unknowns"])}
<p><b>独立客户需求：</b>尚无该项目可计入的需求实证；不能将行业级技术或商业证据视为这家企业的客户证据。</p>
<p><b>项目自身销售／利润：</b>{txt(finance_boundary)} 本站的排序仅代表资料层级，不是赚钱排名。</p></section>
<section class="section"><h2>下一步可以看看什么？</h2><p>{txt(case.get("learning") or "进一步独立核查真实购买需求、履约成本与客户留存。")}</p>
<p><a href="/validation/">查看资料有什么不确定 →</a> · <a href="/projects/">返回项目列表 →</a></p></section>
</details>
<details class="workbook-fold" id="founder-workbook-toggle">
<summary>想自己验证？打开四步工作单</summary>
{workbook_html}
</details>"""
    return shell(name, str(case["desc"]), body, f"/projects/{slug}/")

def index_page(cases: list[dict]) -> str:
    # Same founder-first reading order and reviewed short descriptions as home.
    # Historical evidence depth remains accessible on each dossier.
    case_by_id = {case["id"]: case for case in cases}
    order = ("carrd", "plausible", "nerdwallet")
    if set(case_by_id) != set(order) or set(PROJECT_PREVIEWS) != set(order):
        raise RuntimeError("Only source-admitted, reviewed cases enter the public directory")
    tiles = []
    for slug in order:
        item = case_by_id[slug]
        preview = PROJECT_PREVIEWS[slug]
        suitability = decision_data(item)
        if suitability["startup_ready"] is not False:
            raise RuntimeError("Historical case cannot claim verified startup readiness")
        classification = MODEL_LABELS[item["model"]]
        tiles.append(
            f'<a href="/projects/{txt(slug)}/" class="case-card" data-id="{txt(slug)}">'
            f'<small>{txt(classification)} · 历史公司案例</small>'
            f'<strong>{txt(item["title"])}</strong>'
            '<div class="case-facts" aria-label="案例生意概况">'
            f'<p><b>做什么：</b>{txt(preview["sub"])}</p>'
            f'<p><b>谁在用：</b>{txt(preview["buyer"])}</p>'
            f'<p><b>谁付钱：</b>{txt(PAYING_PARTIES[slug])}</p>'
            f'<p><b>怎么赚钱：</b>{txt(preview["revenue"])}</p>'
            f'<p><b>上手门槛：</b>{txt(preview["difficulty"])}</p>'
            '</div><span class="case-action">看详情和第一步 →</span></a>'
        )
    body = f"""<section class="case-directory-hero" aria-label="公司的历史商业案例">
<span class="kicker">创业案例</span>
<h1>{len(cases)} 家公司的生意，<br>看看它们怎么赚钱。</h1>
<p class="lead">先比较做什么、谁付钱、怎么收费、需要什么能力。这些是历史公司案例，不是已经验证可以照做赚钱的项目。</p>
<p class="case-browse"><a href="/discover/">想看更多生意方向？去找项目 →</a></p>
<div class="case-directory-proof" aria-label="研究证据边界"><span>3 个有历史经营资料的公司案例</span>
<span>0 个已确认可以直接复制盈利的项目</span></div></section>
<div class="directory" id="directory">{''.join(tiles)}</div>
<details class="notice"><summary>资料来源和风险说明</summary>
<p>公开定价不等于真实成交。公司历史经营结果也不等于新创业者的收入，当前没有已验证可直接盈利的创业项目。</p>
<p>这三家公司都有可追溯的历史经营资料，有些来自财报，有些来自公司或创始人过去的公开陈述；按此顺序阅读不是赚钱排名。</p>
<p>只找到官网或标价，还不足以说明生意做成了。每个详情页保留来源、报告时间、成本和未核实的风险。</p>
<p><a href="/validation/">更多关于资料的限制 →</a></p></details>"""
    return shell(f"{len(cases)} 个有经营证据的项目", "只展示有公开历史经营资料的公司案例，直观看谁付款、怎么收费、什么门槛", body, "/projects/")

def build() -> dict:
    all_cases = parse_cases()
    cases = eligible_cases(all_cases)
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST/"index.html").write_text(index_page(cases), encoding="utf-8")
    for item in cases:
        out=DEST/item["id"]/"index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(project_page(item), encoding="utf-8")
    paths = [p for p in DEST.rglob("index.html")]
    if len(paths) != len(cases) + 1:
        raise RuntimeError("Published profile count mismatches strict evidence admission")
    for path in paths:
        page=path.read_text(encoding="utf-8")
        for forbidden in ["Empire Flippers","listing_number","public_title","source_url","OPP_V0.2"]:
            if forbidden.lower() in page.lower():
                raise RuntimeError("Protected source term in dossier: "+str(path))
    return {"status":"PASS","cases":len(cases),"public_pages":len(paths),"held_for_research":len(all_cases)-len(cases)}

if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False))
