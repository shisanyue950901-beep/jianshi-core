"""T08: project-library ranking and strict review-only preview gate.

Data/project numbers exist ONLY in data/projects.json. New, as-yet-unapproved
records are allowed in feature previews so Hark can inspect them, but fail
closed in main/production until reviewed_by_hark and PUBLIC are granted.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "projects.json"
REVIEW_PREVIEW_BRANCHES = {"feat/t08", "feat/t10-new-projects"}


def review_preview() -> bool:
    names = (os.getenv("CF_PAGES_BRANCH", ""), os.getenv("GITHUB_HEAD_REF", ""),
             os.getenv("GITHUB_REF_NAME", ""))
    if any(name in REVIEW_PREVIEW_BRANCHES for name in names):
        return True
    # Offline developer tests on the checked-out feature branch, not CI or production.
    if not os.getenv("CI") and not os.getenv("CF_PAGES") and not os.getenv("GITHUB_ACTIONS"):
        head = ROOT / ".git" / "HEAD"
        if head.is_file() and head.read_text(encoding="utf-8").strip() in {"ref: refs/heads/" + branch for branch in REVIEW_PREVIEW_BRANCHES}:
            return True
    return False


def projects() -> list[dict]:
    items = json.loads(DATA.read_text(encoding="utf-8"))
    if len({p["id"] for p in items}) != len(items):
        raise ValueError("Duplicate project IDs")
    pending = [p["id"] for p in items if not (
        p.get("reviewed_by_hark") is True and p.get("publication_status") == "PUBLIC")]
    if pending:
        if not review_preview():
            raise ValueError("Unapproved project records cannot publish to main: " + ", ".join(pending))
        for p in items:
            if p["id"] in pending and (p.get("reviewed_by_hark") is not False
                                       or p.get("publication_status") != "PRIVATE_REVIEW_ONLY"):
                raise ValueError("Invalid pending review state: " + p["id"])
    return items


def featured_projects() -> list[dict]:
    return sorted(projects(), key=lambda p: (-p["total_score"], -p["revenue"]["last_30d"], p["id"]))[:3]


def usd(value) -> str:
    if value is None:
        return "未公开"
    return "$" + (f"{value:,.2f}" if float(value) != int(value) else f"{value:,.0f}")
