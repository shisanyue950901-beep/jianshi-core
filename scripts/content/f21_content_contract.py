"""JIANSHI F2.1 CMS contract: offline metadata validation and review transitions.

No database, network, credentials, or production writes. Public projection is
an allowlist: nothing from private draft fields is ever copied implicitly.
"""
from __future__ import annotations

import copy
from datetime import date
from urllib.parse import urlsplit

TYPES = frozenset({
    "PROJECT_RESEARCH", "SOLUTION_GUIDE", "COURSE", "LESSON",
    "RESOURCE", "EVENT", "CASE_STUDY",
})
STATES = frozenset({
    "DRAFT", "IN_REVIEW", "APPROVED", "REJECTED",
    "PUBLISHED", "UNPUBLISHED", "ARCHIVED",
})
LICENSES = frozenset({"OWNED", "LICENSED", "UNKNOWN"})
NEXT = {
    "DRAFT": frozenset({"IN_REVIEW", "ARCHIVED"}),
    "IN_REVIEW": frozenset({"APPROVED", "REJECTED"}),
    "APPROVED": frozenset({"PUBLISHED", "ARCHIVED"}),
    "REJECTED": frozenset({"DRAFT", "ARCHIVED"}),
    "PUBLISHED": frozenset({"UNPUBLISHED"}),
    "UNPUBLISHED": frozenset({"IN_REVIEW", "ARCHIVED"}),
    "ARCHIVED": frozenset(),
}
PUBLIC_KEYS = frozenset({
    "content_id", "content_type", "title", "summary", "category", "tags",
    "language", "source_refs", "source_verified_at", "published_at", "revision",
})
SENSITIVE_FIELDS = frozenset({
    "private_notes", "internal_budget", "contact_email", "contact_phone",
    "personal_id", "raw_company_brief", "private_moderation_reason",
    "service_role", "api_token",
})


class ContentContractError(ValueError):
    """Fail-closed editorial contract violation."""


def _valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_draft(record: dict) -> None:
    if not isinstance(record, dict):
        raise ContentContractError("Content must be a dict")
    required = {
        "content_id", "content_type", "title", "summary", "category",
        "tags", "language", "status", "author_id", "revision",
        "source_refs", "source_verified_at", "license_status",
        "rights_confirmed", "facts_verified",
    }
    if not required.issubset(record):
        raise ContentContractError("Missing required CMS fields")
    if record["content_type"] not in TYPES or record["status"] not in STATES:
        raise ContentContractError("Unsupported content type or state")
    lengths = {"content_id": 100, "title": 140, "summary": 1600,
               "category": 80, "author_id": 100}
    for key, maximum in lengths.items():
        val = record[key]
        if not isinstance(val, str) or not val.strip() or len(val) > maximum:
            raise ContentContractError("Invalid or overlong " + key)
    if (not isinstance(record["revision"], int) or isinstance(record["revision"], bool)
            or record["revision"] < 1):
        raise ContentContractError("Invalid content revision")
    if (not isinstance(record["tags"], list) or len(record["tags"]) > 12
            or any(not isinstance(v, str) or not v or len(v) > 35 for v in record["tags"])):
        raise ContentContractError("Invalid tags")
    if record["language"] not in ("zh-CN", "en"):
        raise ContentContractError("Unsupported locale")
    if (record["license_status"] not in LICENSES
            or type(record["rights_confirmed"]) is not bool
            or type(record["facts_verified"]) is not bool):
        raise ContentContractError("Invalid license and verification state")
    if not _valid_date(record["source_verified_at"]):
        raise ContentContractError("Invalid source verification date")
    sources = record["source_refs"]
    if not isinstance(sources, list) or len(sources) > 30:
        raise ContentContractError("Invalid source references")
    for source in sources:
        if not isinstance(source, dict) or source.get("kind") not in ("PUBLIC_URL", "AUTHOR_ORIGINAL"):
            raise ContentContractError("Source identity invalid")
        if source["kind"] == "PUBLIC_URL":
            url = source.get("url")
            if (not isinstance(url, str) or len(url) > 1000
                    or urlsplit(url).scheme != "https" or not urlsplit(url).hostname):
                raise ContentContractError("External source URL must be HTTPS")
        elif source.get("description", "") == "" or len(str(source["description"])) > 300:
            raise ContentContractError("Original source requires attribution")
    if record.get("reviewer_id") == record["author_id"]:
        raise ContentContractError("Self-review forbidden")
    if record["status"] in ("APPROVED", "PUBLISHED") and not record.get("reviewer_id"):
        raise ContentContractError("Approved content must have independent reviewer")


def transition(record: dict, state: str, *, actor_id: str, role: str,
               timestamp: str | None = None) -> dict:
    """Return a validated NEW revision; caller controls trusted actor identity."""
    validate_draft(record)
    if state not in NEXT[record["status"]]:
        raise ContentContractError("Illegal CMS transition")
    if not isinstance(actor_id, str) or not actor_id.strip():
        raise ContentContractError("Missing trusted actor")
    old_state = record["status"]
    if state == "IN_REVIEW" and (actor_id != record["author_id"] or role not in ("AUTHOR", "EDITOR")):
        raise ContentContractError("Only owner may submit")
    if state in ("APPROVED", "REJECTED") and (role not in ("REVIEWER", "ADMIN") or actor_id == record["author_id"]):
        raise ContentContractError("Independent reviewer required")
    if state == "PUBLISHED" and role not in ("PUBLISHER", "ADMIN"):
        raise ContentContractError("Publisher permission required")
    if state == "UNPUBLISHED" and role not in ("PUBLISHER", "ADMIN"):
        raise ContentContractError("Retraction requires publisher")
    if state == "DRAFT" and (role not in ("AUTHOR", "EDITOR") or actor_id != record["author_id"]):
        raise ContentContractError("Only author can revise rejected draft")
    if state == "ARCHIVED" and role not in ("PUBLISHER", "ADMIN"):
        raise ContentContractError("Archive requires publisher")
    if state in ("APPROVED", "PUBLISHED"):
        if (not record["facts_verified"] or not record["rights_confirmed"]
                or record["license_status"] not in ("OWNED", "LICENSED")
                or not record["source_refs"]):
            raise ContentContractError("Facts, sources and rights must pass")
    new = copy.deepcopy(record)
    new["status"] = state
    new["revision"] += 1
    if state in ("APPROVED", "REJECTED"):
        new["reviewer_id"] = actor_id
    if state == "PUBLISHED":
        if not _valid_date(timestamp):
            raise ContentContractError("Publish date required")
        new["published_at"] = timestamp
    if old_state == "UNPUBLISHED" and state == "IN_REVIEW":
        new.pop("reviewer_id", None)
    validate_draft(new)
    return new


def public_projection(record: dict) -> dict:
    """Release only the exact public field whitelist, after all safety gates."""
    validate_draft(record)
    if (record["status"] != "PUBLISHED" or not record.get("published_at")
            or not _valid_date(record["published_at"])
            or not record["facts_verified"] or not record["rights_confirmed"]
            or record["license_status"] not in ("OWNED", "LICENSED")
            or not record["source_refs"] or record.get("reviewer_id") == record["author_id"]):
        raise ContentContractError("Public projection denied")
    out = {key: copy.deepcopy(record[key]) for key in PUBLIC_KEYS if key in record}
    if SENSITIVE_FIELDS.intersection(out):
        raise ContentContractError("Private content leaked into public projection")
    return out
