"""F2.1 G1-B isolated, in-memory CMS editorial workflow prototype.

A testable workflow kernel, NOT an authenticated admin API, database,
session store, background worker, or public publishing service.
Use staging/synthetic content only; production must provide transactional
revision locks, access checks, and durable moderation/audit persistence.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from f21_content_contract import (
    ContentContractError, public_projection, transition, validate_draft,
)


@dataclass(frozen=True)
class ReviewEvent:
    content_id: str
    previous_state: str
    next_state: str
    revision: int
    actor_id: str  # internal audit only; never returned in public_feed()
    action: str


class InMemoryReviewWorkbench:
    """Offline-only editorial workflow with optimistic revision checks."""

    def __init__(self) -> None:
        self._private_records: dict[str, dict[str, Any]] = {}
        self._audit: list[ReviewEvent] = []

    def add_draft(self, record: dict) -> dict:
        validate_draft(record)
        if record["status"] != "DRAFT":
            raise ContentContractError("Only draft content may be created")
        content_id = record["content_id"]
        if content_id in self._private_records:
            raise ContentContractError("Duplicate content ID")
        self._private_records[content_id] = copy.deepcopy(record)
        return copy.deepcopy(self._private_records[content_id])

    def private_view(self, content_id: str, *, actor_id: str, role: str) -> dict:
        record = self._private_records.get(content_id)
        if record is None:
            raise ContentContractError("Content not found")
        if actor_id != record["author_id"] and role not in ("REVIEWER", "PUBLISHER", "ADMIN"):
            raise ContentContractError("Private editorial access denied")
        return copy.deepcopy(record)

    def change_state(self, content_id: str, next_state: str, *,
                     actor_id: str, role: str, expected_revision: int,
                     published_at: str | None = None) -> dict:
        old = self._private_records.get(content_id)
        if old is None:
            raise ContentContractError("Content not found")
        if (not isinstance(expected_revision, int) or isinstance(expected_revision, bool)
                or expected_revision != old["revision"]):
            raise ContentContractError("Stale editorial version")
        if (actor_id != old["author_id"] and role not in ("REVIEWER", "PUBLISHER", "ADMIN")):
            raise ContentContractError("Not authorized to change this draft")
        # Domain contract decides valid status changes and independent review.
        new = transition(old, next_state, actor_id=actor_id, role=role,
                         timestamp=published_at)
        if next_state == "PUBLISHED":
            # Do not commit state unless the complete public whitelist succeeds.
            public_projection(new)
        self._private_records[content_id] = copy.deepcopy(new)
        self._audit.append(ReviewEvent(content_id, old["status"], new["status"],
                                       new["revision"], actor_id, "STATUS_CHANGE"))
        return copy.deepcopy(new)

    def audit_log(self) -> tuple[ReviewEvent, ...]:
        """Internal test evidence; never embed this in a public site."""
        return tuple(self._audit)

    def public_feed(self) -> list[dict]:
        """Reviewed, currently published materials only. No private keys."""
        entries = []
        for rec in self._private_records.values():
            if rec["status"] == "PUBLISHED":
                entries.append(public_projection(rec))
        return sorted(entries, key=lambda row: row["content_id"])
