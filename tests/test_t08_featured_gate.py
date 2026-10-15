#!/usr/bin/env python3
"""Mutation tests proving the T08 homepage publishing guard fails closed."""
from __future__ import annotations
import sys
import unittest
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts" / "release"))
from t08_project_selection import featured_projects
from verify_t08_home_snapshot import verify


def card(project: dict) -> str:
    return (
        f'<article class="j2-project" data-t08-id="{escape(project["id"], quote=True)}">'
        f'<h3>{escape(project["name"])}</h3>'
        f'<a href="/projects/{escape(project["id"], quote=True)}/">看项目详情</a>'
        "</article>"
    )


class RankedHomepageGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projects = featured_projects()
        assert len(cls.projects) == 3
        cls.cards = [card(p) for p in cls.projects]

    def test_accepts_exact_json_three(self):
        self.assertEqual(verify("".join(self.cards)), [p["id"] for p in self.projects])

    def test_rejects_missing_card(self):
        with self.assertRaisesRegex(AssertionError, "IDs/order"):
            verify("".join(self.cards[:2]))

    def test_rejects_duplicate_card(self):
        with self.assertRaisesRegex(AssertionError, "IDs/order"):
            verify("".join(self.cards + self.cards[:1]))

    def test_rejects_wrong_order(self):
        with self.assertRaisesRegex(AssertionError, "IDs/order"):
            verify("".join(reversed(self.cards)))

    def test_rejects_stale_or_unregistered_id(self):
        invalid = self.cards[0].replace(
            f'data-t08-id="{self.projects[0]["id"]}"', 'data-t08-id="removed-legacy-project"'
        )
        with self.assertRaisesRegex(AssertionError, "IDs/order"):
            verify(invalid + "".join(self.cards[1:]))

    def test_rejects_correct_id_with_wrong_visible_name(self):
        invalid = self.cards[0].replace(escape(self.projects[0]["name"]), "Unrelated Project")
        with self.assertRaisesRegex(AssertionError, "name mismatch"):
            verify(invalid + "".join(self.cards[1:]))

    def test_rejects_correct_id_with_wrong_detail_link(self):
        invalid = self.cards[0].replace(
            f'href="/projects/{self.projects[0]["id"]}/"', 'href="/projects/"'
        )
        with self.assertRaisesRegex(AssertionError, "href mismatch"):
            verify(invalid + "".join(self.cards[1:]))

    def test_rejects_extra_external_link_in_card(self):
        invalid = self.cards[0].replace("</article>", '<a href="https://example.org/">X</a></article>')
        with self.assertRaisesRegex(AssertionError, "href mismatch"):
            verify(invalid + "".join(self.cards[1:]))


if __name__ == "__main__":
    unittest.main()
