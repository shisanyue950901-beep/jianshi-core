#!/usr/bin/env python3
"""P4.25: strictly admit named commercial cases with attributable operating evidence.

L1 product URLs and L2 creator/platform attribution remain *internal research*.
No unadmitted named company may be published into the official case catalogue,
the public home source, or a project dossier.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "config/p424_project_research_evidence.json"
ELIGIBLE = {
    "regulatory_filing": ("US_SEC_10K_AUDITED_CONSOLIDATED", "HISTORICAL_REGULATORY_FILING"),
    "founder_historical": ("FOUNDER_PUBLIC_INTERVIEW", "HISTORICAL_FOUNDER_SELF_REPORT"),
    "founder_historical_company": ("COMPANY_SELF_DISCLOSURE", "HISTORICAL_COMPANY_SELF_REPORT"),
}
# Explicit permitted source kinds, not manually curated ranking orders.
ALLOWED_SOURCE_TYPES = {
    ("regulatory_filing", "US_SEC_10K_AUDITED_CONSOLIDATED", "HISTORICAL_REGULATORY_FILING"),
    ("founder_historical", "FOUNDER_PUBLIC_INTERVIEW", "HISTORICAL_FOUNDER_SELF_REPORT"),
    ("founder_historical", "COMPANY_SELF_DISCLOSURE", "HISTORICAL_COMPANY_SELF_REPORT"),
}


def admitted_ids() -> set[str]:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    if data.get("version") != "P4.24_RESEARCH_EVIDENCE_V1":
        raise RuntimeError("Unrecognized source-ledger contract")
    permitted: set[str] = set()
    for item in data.get("additional_evidence", []):
        triple = (item.get("tier"), item.get("source_type"), item.get("financial_status"))
        if triple not in ALLOWED_SOURCE_TYPES:
            continue
        slug, link, claim = item.get("id"), item.get("source_url"), item.get("claim")
        parsed = urlsplit(link if isinstance(link, str) else "")
        if (not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9-]{2,60}", slug)
                or not isinstance(claim, str) or len(claim) < 50
                or not parsed.hostname or parsed.scheme != "https"
                or parsed.username or parsed.password):
            raise RuntimeError("A candidate business case has insufficient attribution")
        if slug in permitted:
            raise RuntimeError("Duplicate independently attributable candidate")
        permitted.add(slug)
    if not permitted:
        raise RuntimeError("No case clears the strict company-level operating-evidence gate")
    return permitted


def eligible_cases(cases: list[dict]) -> list[dict]:
    admitted = admitted_ids()
    if not admitted.issubset({case["id"] for case in cases}):
        raise RuntimeError("Admitted ID missing from the reviewed case registry")
    return [case for case in cases if case["id"] in admitted]


def public_home(source: str, cases: list[dict]) -> str:
    approved = {case["id"] for case in cases}
    if approved != admitted_ids():
        raise RuntimeError("Inconsistent public home admission decision")
    # Keep the existing CSS, light/dark theme, 8-WebP gallery and 3D motion,
    # but never ship the 17 non-admitted named case records in its JS payload.
    cover_rx = r"(const ITEMS=)(\[.*?\])(;ITEMS\.forEach)"
    cover = re.search(cover_rx, source, re.S)
    if not cover:
        raise RuntimeError("Missing exact featured-cover data")
    images = json.loads(cover.group(2))
    if len(images) != 8 or {x["id"] for x in images[:2]} != {"easlo", "louise"}:
        raise RuntimeError("Eight-photo visual contract unexpectedly changed")
    for i in range(2):
        original = images[i]
        # Illustrative artwork is not a recommended or verified project.
        images[i] = {
            "id": "study-visual-" + str(i + 1), "kind": "illustration",
            "group": original["group"],
            "title": "商业模式研究视觉 " + str(i + 1),
            "tag": "视觉示意 · 非收录项目",
            "meta": "仅展示商业研究主题，与具名公司经营结果无关",
            "desc": "这是概念性配图，不代表任何企业已被商业验证。",
            "buyer": "不适用：视觉示意图。",
            "revenue": "不适用：视觉示意图。",
            "offer": "商业研究主题概念图。",
            "process": "无具体企业运营核验。",
            "cost": "不提供经营数据。",
            "facts": ["概念配图不是具名项目的证据。"],
            "unknowns": ["不可依据视觉推断销量或净利润。"],
            "number": original["number"],
            "art": original.get("art", ""),
            "image": original["image"],
        }
    source = re.sub(
        cover_rx, lambda m: m.group(1) + json.dumps(images, ensure_ascii=False, separators=(",", ":")) + m.group(3),
        source, count=1, flags=re.S
    )
    # The old editorial research records remain in private repo config, not
    # in production public JS and not in the official leaderboard.
    for key in ("EXTRA_CASES", "P415_CASES"):
        rx = rf"(const {key}=)(\[.*?\])(;)"
        match = re.search(rx, source, re.S)
        if not match:
            raise RuntimeError(f"Missing {key} array")
        data = json.loads(match.group(2))
        kept = [x for x in data if x["id"] in approved]
        source = re.sub(
            rx, lambda m, arr=kept: m.group(1) + json.dumps(arr, ensure_ascii=False, separators=(",", ":")) + m.group(3),
            source, count=1, flags=re.S
        )
    # Remove hardcoded original 2 project links applied after initial arrays.
    source = re.sub(r"Object\.assign\(ITEMS\[[01]\],\{officialHomeUrl:'https://[^']+',sourceUrl:'https://[^']+'\}\);", "", source)
    # Replace misleading hero/section copy with strict project gate.
    patches = {
        "20 个具名项目 · 6 类商业模式": f"{len(approved)} 个有经营证据的项目 · 6 类商业模式",
        "20 个可核对的具名项目与 6 种商业模式。先从产品、客户和收费机制了解一门生意；实际营收与利润仍待独立核实。":
            f"正式仅收录 {len(approved)} 个有项目级经营披露的案例。其余项目仍在内部补证，不把官网或价格页冒充经营验证。",
        "按资料核验日期排序，不是热度或盈利榜。信息依据为项目官方网页与产品定价页；首次发现渠道尚未逐项记录。首批 18 项于 10 月 9 日核验，另 2 项日期待补。":
            "正式商业案例须有可归属经营披露。监管财报与创始人历史自述分别注明，不表示当前收益，不以商品售价代替成交。",
        "最近核验榜。": "有商业证据的项目榜。",
        "JIANSHI RESEARCH / 研究榜": "JIANSHI RESEARCH / 严格收录",
        "资料来源：项目官方网页": "资料依据：项目官方网页",
        "这是编辑核验更新榜，不代表项目热度。": "正式案例须有经营披露，非赚钱排名。",
        "本期核验 ": "本期公开经营证据项目 ",
        "不是项目热度或收益排名": "不是利润排行",
    }
    for old, new in patches.items():
        if old not in source:
            raise RuntimeError("Homepage copy / data contract changed: " + old[:60])
        source = source.replace(old, new)
    # Escape any unintended unapproved titles, names, references (not CSS
    # or generic educational model names).
    raw_title_ids = {"easlo", "louise"}
    for key in ("EXTRA_CASES", "P415_CASES"):
        pass
    if any(name in source for name in ["Easlo｜", "Louise Lennox", "Tally｜", "Bellroy｜", "Gumroad｜"]):
        raise RuntimeError("Non-admitted project detail leaked into public HTML")
    return source
