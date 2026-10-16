#!/usr/bin/env python3
"""Verify the *generated* homepage recommendations against reviewed T08 JSON.

Used by main build-static and PR dry-runs. No network calls and no hard-coded
project identifiers or revenue data. A missing, extra, duplicated, reordered,
misnamed or mislinked recommendation makes the release fail closed.
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from t08_project_selection import featured_projects

class RecommendedCards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.active = None
        self.article_depth = 0

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == "article":
            if self.active is not None:
                self.article_depth += 1
                if "data-t08-id" in fields:
                    raise AssertionError("Nested recommendation card")
            elif "data-t08-id" in fields:
                self.active = {"id": fields["data-t08-id"], "text": [], "hrefs": []}
                self.article_depth = 1
        if self.active is not None and tag == "a" and "href" in fields:
            self.active["hrefs"].append(fields["href"])

    def handle_data(self, data):
        if self.active is not None:
            self.active["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "article" and self.active is not None:
            self.article_depth -= 1
            if self.article_depth == 0:
                self.cards.append(self.active)
                self.active = None


def verify(html_text: str, expected: list[dict] | None = None) -> list[str]:
    ranked = featured_projects() if expected is None else expected
    if len(ranked) != 3 or len({p["id"] for p in ranked}) != 3:
        raise AssertionError("JSON must produce exactly three distinct recommendations")
    parser = RecommendedCards()
    parser.feed(html_text)
    parser.close()
    if parser.active is not None:
        raise AssertionError("Unclosed recommendation article")
    found = parser.cards
    ids = [card["id"] for card in found]
    wanted = [p["id"] for p in ranked]
    if len(found) != 3 or ids != wanted:
        raise AssertionError(f"Featured card IDs/order mismatch: rendered={ids!r}, JSON={wanted!r}")
    for card, project in zip(found, ranked, strict=True):
        visible_text = " ".join(card["text"])
        if project["name"] not in visible_text:
            raise AssertionError(f"Featured card name mismatch: {project['id']!r}")
        href = f"/projects/{project['id']}/"
        if card["hrefs"] != [href]:
            raise AssertionError(f"Featured href mismatch for {project['id']!r}: {card['hrefs']!r}")
    return wanted


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tests/verify_t08_home_snapshot.py web/dist/index.html")
    path = Path(sys.argv[1])
    if not path.is_file():
        raise AssertionError(f"Generated homepage not found: {path}")
    ids = verify(path.read_text(encoding="utf-8"))
    print(f"PASS T08 build-static homepage contract: exactly 3 ranked JSON cards, names, ids and detail links: {', '.join(ids)}")


if __name__ == "__main__":
    main()
