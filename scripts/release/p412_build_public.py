#!/usr/bin/env python3
"""Create a fail-closed, public-only JianShi P4.12 release artifact.

Run *after* web/build.py. Never point Cloudflare Pages at repository root.
Only web/dist is a valid deploy output. This script does not deploy itself.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from p423_build_project_proofs import build as build_project_proofs, parse_cases
from p425_public_admission import admitted_ids, eligible_cases, public_home
from p429_build_source_atlas import build as build_source_atlas

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "web" / "dist"
SOURCE = ROOT / "web" / "prototypes" / "p412e" / "index.html"
EVIDENCE = ROOT / "web" / "prototypes" / "p422" / "evidence.html"
SITE = "https://jianshi-bua.pages.dev"
SLUGS = {
    "vertical-industry-saas": "saas",
    "digital-product-business": "digital",
    "affiliate-content-site": "content",
    "amazon-kdp-publishing": "kdp",
    "amazon-fba-niche-brand": "fba",
    "agency-business": "agency",
    "solo-saas": "saas",
    "ecommerce-brands": "fba",
    "ai-agent-tools": "saas",
}

# Avoid falsely making an unsupported technical signal equal to a concrete
# business model. It has a generic home destination rather than a made-up case.
SLUGS["ai-agent-tools"] = ""

def safe_redirect(destination: str, page_title: str = "见势｜页面已更新") -> str:
    assert destination.startswith("/") and all(x not in destination for x in ["<", ">", '"', "'", "\\"])
    target = html.escape(destination, quote=True)
    title = html.escape(page_title, quote=True)
    return (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta name='robots' content='noindex,follow'>"
        f"<meta http-equiv='refresh' content='0;url={target}'>"
        f"<title>{title}</title></head><body>"
        f"<p>页面已更新，正在前往新版见势。<a href='{target}'>点击继续访问</a>。</p>"
        f"<script>location.replace({json.dumps(destination,ensure_ascii=False)})</script>"
        "</body></html>\n"
    )

def assert_safe_source(markup: str, *, source_prototype: bool = True) -> None:
    required = [
        "见势", "Playfair+Display", "family=Inter", "--bg:#000",
        "id=\"ring\"", "id=\"lb\"", "id=\"grid\"",
        "prefers-reduced-motion", "viewport-fit=cover", "100dvh",
    ]
    if source_prototype:
        required += ["Easlo", "Louise Lennox"]
    for marker in required:
        if marker not in markup:
            raise RuntimeError(f"Missing expected public design contract: {marker}")
    if markup.count("<script>") != 1 or markup.count("<style>") != 1:
        raise RuntimeError("Unexpected external or multiple script/style sections")
    if markup.count("data:image/webp;base64,") != 8:
        raise RuntimeError("Expected 8 inline concept-cover images")
    banned = [
        "Empire Flippers", "empireflippers", "listing_number", "source_url",
        "source_ref_ids", "OPP_V0.2", "EASLO_OWN_SITE_01",
        "LENNOX_AMAZON_02", "OFFICIAL_API", "预计利润率",
    ]
    for token in banned:
        if token.lower() in markup.lower():
            raise RuntimeError("Source-protection check failed")
    if len(markup.encode("utf-8")) > 400_000:
        raise RuntimeError("Single HTML unexpectedly large")


# Publish a *separate* evidence-only appendix. Never replace the editorial,
# source-governed home page or resurrect the deprecated /opportunities route.
# web/build.py retains a pre-release mirror here; web/dist is intentionally
# rewritten by the release step and must not be used for rerunnable inputs.
RESEARCH_SOURCE = ROOT / "dist"
RESEARCH_SLUGS = (
    "vertical-industry-saas",
    "amazon-fba-niche-brand",
    "digital-product-business",
    "affiliate-content-site",
    "amazon-kdp-publishing",
    "agency-business",
)

def publish_public_research_appendix() -> int:
    source_index=RESEARCH_SOURCE/"opportunities"/"index.html"
    if not source_index.is_file():
        raise RuntimeError("Base business research index missing")
    candidates=[(source_index,OUTPUT/"research"/"index.html",True)]
    for slug in RESEARCH_SLUGS:
        src=RESEARCH_SOURCE/"opportunity"/slug/"index.html"
        if not src.is_file():
            raise RuntimeError("Missing approved anonymous study: "+slug)
        candidates.append((src,OUTPUT/"research"/slug/"index.html",False))
    forbidden=(
        "empire flippers","empireflippers","listing_number","public_title",
        "source_updated_at","source_url","source_ref_ids",
        "china_screening","first_validation","editorial_judgement",
    )
    for src,target,is_index in candidates:
        markup=src.read_text(encoding="utf-8")
        if any(token in markup.lower() for token in forbidden):
            raise RuntimeError("Protected source marker in research appendix")
        if is_index:
            if markup.count('id="category-comparison"')!=1:
                raise RuntimeError("Evidence-backed six-category comparison missing")
            if '<meta name="robots" content="index,follow">' not in markup:
                raise RuntimeError("Unexpected research index robots rule")
            markup=markup.replace(
                '<meta name="robots" content="index,follow">',
                '<meta name="robots" content="noindex,follow">',1)
        elif ("noindex,nofollow" not in markup
              or 'id="sample-metrics"' not in markup
              or 'class="data-freshness-v2"' not in markup):
            raise RuntimeError("Anonymized detail is missing noindex or research transparency sections")
        markup=markup.replace(
            f'{SITE}/opportunities/',f'{SITE}/research/')
        markup=markup.replace(
            'href="/opportunities/', 'href="/research/')
        markup=markup.replace(
            'href="/opportunity/', 'href="/research/')
        # Detailed canonical/OG references must point at this appendix,
        # not the intentionally redirected legacy opportunity pages.
        for slug in RESEARCH_SLUGS:
            markup=markup.replace(
                f'{SITE}/opportunity/{slug}/',
                f'{SITE}/research/{slug}/')
        if '/opportunity/' in markup and ('href="/opportunity/' in markup or f'{SITE}/opportunity/' in markup):
            raise RuntimeError("Research appendix still links to legacy redirects")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(markup,encoding="utf-8")
    return len(RESEARCH_SLUGS)


def build_release() -> dict:
    if not OUTPUT.is_dir() or not (OUTPUT / "_redirects").is_file() or not (OUTPUT / "_headers").is_file():
        raise RuntimeError("web/build.py must create web/dist and security controls first")
    markup = SOURCE.read_text(encoding="utf-8")
    assert_safe_source(markup)
    # This is now a website, not an internal file-based prototype.
    markup = markup.replace("此文件为独立网站预览，不收集访客信息。", "本站暂不提供在线留言功能，也不会通过本页面收集访客信息。")
    markup = markup.replace('© 2026 见势 JIANSHI</span><a href="#top">', '© 2026 见势 JIANSHI</span><a href="/privacy/">隐私说明</a><a href="#top">')
    markup = markup.replace("</head>", f'<link rel="canonical" href="{SITE}/">\n</head>', 1)
    # Strict editorial gate: only projects with attributable operating evidence.
    approved = eligible_cases(parse_cases())
    markup = public_home(markup, approved)
    # Keep the established one-page user journey and motion design; offer an
    # explicit, evidence-only research appendix instead of replacing the hero.
    model_marker='<div class="model-list" id="modelList"></div>'
    if markup.count(model_marker)!=1:
        raise RuntimeError("Business-model section anchor changed")
    research_action=(
        '<p class="models__intro">'
        '<a class="proof-action" href="/research/">'
        '查看六类商业项目的匿名统计、领域分布和案例区间'
        ' <span aria-hidden="true">↗</span></a></p>'
    )
    markup=markup.replace(model_marker,model_marker+research_action,1)
    assert_safe_source(markup, source_prototype=False)
    (OUTPUT / "index.html").write_text(markup, encoding="utf-8")
    # Separate public-only evidence dashboard. Never embed raw marketplace data
    # or copy source directories, and do not change any production data pipeline.
    evidence = EVIDENCE.read_text(encoding="utf-8")
    if (evidence.count("<style>") != 1 or evidence.count("<script>") != 1
            or "id=\"evidenceList\"" not in evidence or "商业证据" not in evidence):
        raise RuntimeError("Invalid evidence dashboard contract")
    for banned in ("Empire Flippers", "empireflippers", "listing_number",
                   "source_url", "public_title", "source_ref_ids", "OPP_V0.2"):
        if banned.lower() in evidence.lower():
            raise RuntimeError("Evidence dashboard contains protected source identifiers")
    proof = OUTPUT / "validation" / "index.html"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text(evidence, encoding="utf-8")
    # Publish only strictly admitted named company dossiers; never infer
    # any company's revenue from anonymous industry-level observations.
    project_result = build_project_proofs()
    if project_result["cases"] != len(approved) or project_result["public_pages"] != len(approved) + 1:
        raise RuntimeError("Strict company-level evidence admission failed")

    # Curated market research: links/independent interpretation only; license-gated
    # marketplace listing feeds remain disabled with no network scraping.
    market_sources = build_source_atlas()
    if market_sources["sources"] != 6 or market_sources["editorial_reports"] != 4 or market_sources["listing_import_enabled"]:
        raise RuntimeError("Unapproved market source import detected")

    # The old paths remain redirects; expose aggregate research only at a
    # distinct and explicitly linked /research/ URL.
    anonymous_studies=publish_public_research_appendix()
    # Old bookmark paths must not lead users back to an engineering dashboard.
    destinations = {
        "opportunities": "/#archive",
        "today": "/",
        "rising": "/",
        "build": "/",
        "content": "/",
        "account": "/",
    }
    for name, target in destinations.items():
        out = OUTPUT / name / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(safe_redirect(target), encoding="utf-8")

    item_dir = OUTPUT / "opportunity"
    if item_dir.is_dir():
        for out in item_dir.glob("*/index.html"):
            slug = out.parent.name
            anchor = SLUGS.get(slug, "")
            out.write_text(safe_redirect("/#item-" + anchor if anchor else "/"), encoding="utf-8")

    # New public index has its own client-only search. Remove unused,
    # potentially stale search data from the release artifact.
    stale = OUTPUT / "search-index.json"
    if stale.exists():
        stale.unlink()

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{SITE}/</loc></url>"
        f"<url><loc>{SITE}/privacy/</loc></url>"
        f"<url><loc>{SITE}/validation/</loc></url>"
        f"<url><loc>{SITE}/sources/</loc></url>"
        f"<url><loc>{SITE}/projects/</loc></url>"
        + "".join(f"<url><loc>{SITE}/projects/{p.name}/</loc></url>" for p in sorted((OUTPUT/"projects").iterdir()) if p.is_dir())
        +         '</urlset>\n'
    )
    (OUTPUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUTPUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n",
        encoding="utf-8",
    )
    # Fail closed if root-level repository artifacts sneak into deploy folder.
    prohibited = [
        "config", ".github", "scripts", "src", "docs", "db",
        "supabase", "tests", "fixtures", ".env", "README_CN.md",
    ]
    for rel in prohibited:
        if (OUTPUT / rel).exists():
            raise RuntimeError("Forbidden internal path in Cloudflare deploy output")
    return {
        "status": "PASS",
        "release": "P4.12",
        "output": "web/dist",
        "inline_covers": 8,
        "evidence_dashboard": "validation/index.html",
        "named_project_dossiers": len(approved),
        "curated_market_sources": market_sources["sources"],
        "anonymous_studies": anonymous_studies,
        "legacy_redirects": len(destinations),
        "slug_rewrites": len(list(item_dir.glob("*/index.html"))) if item_dir.is_dir() else 0,
        "production_deployed": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true", help="Not supported: use integration tests after building")
    args = parser.parse_args()
    if args.verify_only:
        raise RuntimeError("Run full offline build followed by tests instead")
    print(json.dumps(build_release(), ensure_ascii=False))

if __name__ == "__main__":
    main()
