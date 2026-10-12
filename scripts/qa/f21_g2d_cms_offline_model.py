"""G2-D: deterministic, offline CMS transaction *contract model*, not the database.

All actor names are SYNTHETIC. This file must never connect to Supabase, import
production records, or claim it executed the real PostgreSQL write path.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import re

ROLES = {"EDITOR", "REVIEWER", "PUBLISHER", "ADMIN"}
STATES = {"DRAFT", "IN_REVIEW", "APPROVED", "REJECTED", "PUBLISHED", "UNPUBLISHED"}
VALID_SOURCE = re.compile(r"^https://[a-zA-Z0-9.-]+(?:/[^?#\s@]*)?$")
VALID_DATE = re.compile(r"^20[0-9]{2}-[01][0-9]-[0-3][0-9]$")
PUBLIC_FIELDS = frozenset({
    "content_id", "content_type", "title", "summary", "category",
    "tags", "language", "source_refs", "source_verified_at",
    "revision", "published_at",
})


class Rejected(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class Revision:
    number: int
    content: dict
    sources_private: list
    rights: bool
    facts: bool


@dataclass
class Item:
    key: str
    owner: str
    kind: str
    state: str = "DRAFT"
    revision: int = 1
    last_reviewer: str | None = None
    versions: dict[int, Revision] = field(default_factory=dict)
    events: list[tuple[str, int, str, str]] = field(default_factory=list)
    request_ids: set[str] = field(default_factory=set)
    snapshots: list[dict] = field(default_factory=list)


class OfflineCms:
    """Transition parity model with atomic copy-and-commit; no external I/O."""

    def __init__(self, *, simulated_gates_ready: bool = False):
        # The real staging gates stay CLOSED. True is only a locally simulated
        # post-approval branch for exercising hypothetical positive transitions.
        self.simulated_gates_ready = simulated_gates_ready
        self.roles: dict[str, str] = {}
        self.items: dict[str, Item] = {}

    def grant_synthetic(self, actor: str, role: str):
        if not actor.startswith("SYNTHETIC_") or role not in ROLES:
            raise Rejected("CMS_SYNTHETIC_FIXTURE_ONLY")
        self.roles[actor] = role

    def _gate(self, actor: str, allowed: tuple[str, ...]) -> str:
        if not self.simulated_gates_ready:
            raise Rejected("CMS_WRITE_DISABLED")
        if not actor.startswith("SYNTHETIC_"):
            raise Rejected("CMS_SYNTHETIC_FIXTURE_ONLY")
        role = self.roles.get(actor)
        if not role or (role not in allowed and role != "ADMIN"):
            raise Rejected("CMS_PERMISSION_DENIED")
        return role

    @staticmethod
    def _request(item: Item, request_id: str):
        if not request_id.startswith("SYNTHETIC_REQUEST_"):
            raise Rejected("CMS_INVALID_REQUEST")
        if request_id in item.request_ids:
            raise Rejected("CMS_DUPLICATE_REQUEST")

    @staticmethod
    def _expected(item: Item, expected: int):
        if expected != item.revision:
            raise Rejected("CMS_STALE_REVISION")

    def create(self, actor: str, key: str, kind: str, content: dict,
               sources: list, request_id: str):
        self._gate(actor, ("EDITOR",))
        if not (key.startswith("SYNTHETIC_") and 6 <= len(key) <= 100
                and isinstance(content, dict) and isinstance(sources, list)
                and kind in {"SOLUTION_GUIDE", "PROJECT_RESEARCH", "COURSE",
                             "LESSON", "RESOURCE", "EVENT", "CASE_STUDY"}):
            raise Rejected("CMS_INVALID_DRAFT")
        if key in self.items:
            raise Rejected("CMS_DUPLICATE_CONTENT_KEY")
        item = Item(key, actor, kind)
        self._request(item, request_id)
        item.versions[1] = Revision(1, deepcopy(content), deepcopy(sources), False, False)
        item.events.append(("CREATE", 1, actor, "DRAFT"))
        item.request_ids.add(request_id)
        self.items[key] = item
        return 1

    def edit(self, actor: str, key: str, expected: int, content: dict,
             sources: list, rights: bool, facts: bool, request_id: str):
        self._gate(actor, ("EDITOR",))
        item = self._copy(key)
        self._request(item, request_id)
        if item.owner != actor:
            raise Rejected("CMS_OWNER_DENIED")
        if item.state != "DRAFT":
            raise Rejected("CMS_DRAFT_LOCKED")
        self._expected(item, expected)
        if not isinstance(content, dict) or not isinstance(sources, list) or (
                not isinstance(rights, bool) or not isinstance(facts, bool)):
            raise Rejected("CMS_INVALID_EDIT")
        item.revision += 1
        item.versions[item.revision] = Revision(
            item.revision, deepcopy(content), deepcopy(sources), rights, facts)
        item.events.append(("EDIT", item.revision, actor, "DRAFT"))
        item.request_ids.add(request_id)
        self.items[key] = item
        return item.revision

    @staticmethod
    def _publish_projection(item: Item, rev: Revision) -> dict:
        p = rev.content
        if not (isinstance(p.get("title"), str) and 2 <= len(p["title"]) <= 140
                and isinstance(p.get("summary"), str) and 8 <= len(p["summary"]) <= 1600
                and isinstance(p.get("category"), str) and 1 <= len(p["category"]) <= 80
                and p.get("language") in ("zh-CN", "en")
                and isinstance(p.get("source_verified_at"), str)
                and VALID_DATE.fullmatch(p["source_verified_at"])
                and isinstance(p.get("tags"), list) and len(p["tags"]) <= 12
                and all(isinstance(x, str) and 1 <= len(x) <= 35 for x in p["tags"])
                and isinstance(p.get("source_refs"), list)
                and 1 <= len(p["source_refs"]) <= 30):
            raise Rejected("CMS_INVALID_PUBLIC_PROJECTION")
        safe_refs = []
        for source in p["source_refs"]:
            if not isinstance(source, dict):
                raise Rejected("CMS_SOURCE_UNSAFE")
            if source.get("kind") == "PUBLIC_URL" and set(source) == {"kind", "url"}:
                url = source.get("url")
                if not isinstance(url, str) or len(url) > 1000 or not VALID_SOURCE.fullmatch(url):
                    raise Rejected("CMS_SOURCE_UNSAFE")
                safe_refs.append({"kind": "PUBLIC_URL", "url": url})
            elif source.get("kind") == "AUTHOR_ORIGINAL" and set(source) == {"kind", "description"}:
                value = source.get("description")
                if not isinstance(value, str) or not 1 <= len(value) <= 300:
                    raise Rejected("CMS_SOURCE_UNSAFE")
                safe_refs.append({"kind": "AUTHOR_ORIGINAL", "description": value})
            else:
                raise Rejected("CMS_SOURCE_UNSAFE")
        projection = {
            "content_id": item.key, "content_type": item.kind,
            "title": p["title"], "summary": p["summary"],
            "category": p["category"], "tags": deepcopy(p["tags"]),
            "language": p["language"], "source_refs": safe_refs,
            "source_verified_at": p["source_verified_at"],
            "revision": item.revision + 1, "published_at": "SYNTHETIC_DATE",
        }
        if set(projection) != PUBLIC_FIELDS:
            raise Rejected("CMS_ALLOWLIST_BROKEN")
        return projection

    def transition(self, actor: str, key: str, expected: int, state: str,
                   request_id: str, *, media_ready: bool = True):
        # An authorization check precedes data access, as in the SQL kernel.
        role = self._gate(actor, ("EDITOR", "REVIEWER", "PUBLISHER"))
        item = self._copy(key)
        self._request(item, request_id)
        self._expected(item, expected)
        edge = (item.state, state)
        if edge in {("DRAFT", "IN_REVIEW"), ("REJECTED", "DRAFT"),
                    ("UNPUBLISHED", "IN_REVIEW")}:
            if actor != item.owner or role not in {"EDITOR", "ADMIN"}:
                raise Rejected("CMS_OWNER_DENIED")
            action = "RESTORE" if state == "DRAFT" else "SUBMIT"
        elif edge in {("IN_REVIEW", "APPROVED"), ("IN_REVIEW", "REJECTED")}:
            if role not in {"REVIEWER", "ADMIN"} or actor == item.owner:
                raise Rejected("CMS_INDEPENDENT_REVIEW_REQUIRED")
            action = "APPROVE" if state == "APPROVED" else "REJECT"
        elif edge in {("APPROVED", "PUBLISHED"), ("PUBLISHED", "UNPUBLISHED")}:
            if role not in {"PUBLISHER", "ADMIN"} or actor == item.owner:
                raise Rejected("CMS_PUBLISHER_DENIED")
            action = "PUBLISH" if state == "PUBLISHED" else "RETRACT"
        else:
            raise Rejected("CMS_ILLEGAL_TRANSITION")
        rev = item.versions[item.revision]
        if state in {"APPROVED", "PUBLISHED"} and (
                not rev.rights or not rev.facts or not rev.sources_private):
            raise Rejected("CMS_EVIDENCE_OR_RIGHTS_MISSING")
        if state in {"APPROVED", "PUBLISHED"} and not media_ready:
            raise Rejected("CMS_MEDIA_RIGHTS_NOT_READY")
        projection = self._publish_projection(item, rev) if state == "PUBLISHED" else None
        item.revision += 1
        item.state = state
        if state in {"APPROVED", "REJECTED"}:
            item.last_reviewer = actor
        elif state == "IN_REVIEW":
            item.last_reviewer = None
        item.versions[item.revision] = Revision(
            item.revision, deepcopy(rev.content), deepcopy(rev.sources_private),
            rev.rights, rev.facts)
        item.events.append((action, item.revision, actor, state))
        item.request_ids.add(request_id)
        if state == "PUBLISHED":
            item.snapshots.append({"revision": item.revision,
                                   "lifecycle": "STAGED", "public": projection})
        elif state == "UNPUBLISHED":
            for snap in item.snapshots:
                if snap["lifecycle"] == "STAGED":
                    snap["lifecycle"] = "RETRACTED"
        self.items[key] = item
        return item.revision

    def restore_old_revision(self, *_args):
        # Not in SQL 0055. Prohibited until a new author+reviewer release
        # contract is approved; never silently change revision history.
        raise Rejected("CMS_VERSION_ROLLBACK_NOT_IMPLEMENTED")

    def _copy(self, key: str) -> Item:
        if key not in self.items:
            raise Rejected("CMS_NOT_FOUND")
        return deepcopy(self.items[key])
