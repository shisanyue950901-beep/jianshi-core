#!/usr/bin/env python3
"""P4.11 static disclosure scanner. Fails closed before any Pages snapshot is published."""
from __future__ import annotations
import re
import sys
from pathlib import Path

PATTERNS = {
    "named commercial provider": re.compile(r"empire[ -]?flippers|empireflippers\.com", re.I),
    "untranslated raw marketplace title": re.compile(
        r"\$[\d.,]+\s*[KMB]?\s+Per Month\s+(?:Amazon|SaaS|Digital|Agency|Affiliate)",re.I
    ),
    "original record field": re.compile(
        r"\b(?:listing_number|public_title|source_url|source_updated_at|homepage_url)\b",re.I
    ),
    "source operation label": re.compile(r"官方\s*API|源更新时间[:：]|来源分类（原文）|采集方式[:：]",re.I),
}

REQUIRED_DENY_RULES = [
    "/.github/*","/config/*","/db/*","/docs/*","/fixtures/*",
    "/ops/*","/scripts/*","/src/*","/supabase/*","/tests/*","/web/*",
]

def audit(directory: Path) -> list[str]:
    errors=[]
    for name in ("_headers","_redirects"):
        if not (directory/name).is_file():
            errors.append(f"MISSING:{name}")
    headers=(directory/"_headers").read_text(encoding="utf-8") if (directory/"_headers").is_file() else ""
    redirects=(directory/"_redirects").read_text(encoding="utf-8") if (directory/"_redirects").is_file() else ""
    if "Cache-Control: no-store" not in headers:
        errors.append("MISSING:NO_STORE_POLICY")
    for rule in REQUIRED_DENY_RULES:
        if not any(line.strip().startswith(rule+" ") for line in redirects.splitlines()):
            errors.append(f"MISSING:DENY_RULE:{rule}")
    for file in directory.rglob("*"):
        if not file.is_file() or file.suffix not in {".html",".json",".js"}:
            continue
        content=file.read_text(encoding="utf-8",errors="replace")
        for label,regex in PATTERNS.items():
            if regex.search(content):
                errors.append(f"LEAK:{file.relative_to(directory)}:{label}")
    return errors

def main() -> int:
    directory=Path(sys.argv[1] if len(sys.argv)>1 else "web/dist")
    if not directory.is_dir():
        print("FAIL: no output directory",file=sys.stderr)
        return 2
    failures=audit(directory)
    if failures:
        print("\n".join(failures),file=sys.stderr)
        return 1
    print("PASS: public artifact scanner / no source leak / deny rules and cache policy present")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
