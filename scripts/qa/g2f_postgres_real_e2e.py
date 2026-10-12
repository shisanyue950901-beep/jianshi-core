#!/usr/bin/env python3
"""G2-F genuine PostgreSQL E2E using ONLY a disposable GitHub Actions container.

Loads REAL repository migrations 0037 and 0054-0057. Test auth schema and
identities are a minimal synthetic fixture, NOT actual Supabase GoTrue.
The disposable flags are opened only inside this container; neither Staging
nor Production is contacted, and no external data sources are requested.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = (
    "0037_auth_launch_gate.sql",
    "0054_jianshi_cms_private_foundation.sql",
    "0055_jianshi_cms_transaction_gate.sql",
    "0056_jianshi_cms_session_guard.sql",
    "0057_jianshi_cms_historical_draft_restore.sql",
)
EDITOR = "00000000-0000-4000-8000-00000000a001"
REVIEWER = "00000000-0000-4000-8000-00000000a002"
PUBLISHER = "00000000-0000-4000-8000-00000000a003"
OTHER = "00000000-0000-4000-8000-00000000a004"
AUX_EDITOR = "00000000-0000-4000-8000-00000000a005"
CURRENT = "SYNTHETIC_G2F_RESTORE"
CONCURRENT = "SYNTHETIC_G2F_CONCURRENT"
BAD_SOURCE = "SYNTHETIC_G2F_INVALID_SOURCE"
CONTAINER = os.environ.get("G2F_POSTGRES_CONTAINER", "")
DB = os.environ.get("G2F_POSTGRES_DATABASE", "")
NEGATIVE = []


def require(ok: bool, detail: str) -> None:
    if not ok:
        raise AssertionError("G2F contract failure: " + detail)


def sql_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def run_sql(sql: str, *, allow_error: bool = False, timeout: int = 40):
    args = [
        "docker", "exec", "-i", "-u", "postgres", CONTAINER,
        "psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-d", DB,
    ]
    r = subprocess.run(args, input=sql, text=True, capture_output=True,
                       timeout=timeout, check=False)
    if r.returncode and not allow_error:
        # No sensitive records exist: all source/content/identities are synthetic.
        # Even so, return only the final bounded diagnostic lines.
        raise AssertionError("G2F_SQL_FAILURE " + "\n".join(
            (r.stderr or r.stdout).splitlines()[-5:])[:900])
    return r


def scalar(sql: str) -> str:
    r = run_sql(sql)
    lines = [line.strip() for line in r.stdout.splitlines() if line.strip()]
    require(len(lines) == 1, "expected one scalar SQL result")
    return lines[0]


def svc(statement: str) -> str:
    return "SET ROLE service_role;\n" + statement + "\nRESET ROLE;\n"


def check_denial(statement: str, code: str, *, role: str = "service_role"):
    r = run_sql("SET ROLE " + role + ";\n" + statement + "\n", allow_error=True)
    require(r.returncode != 0, "operation unexpectedly accepted: " + code)
    # Only categorical error text is inspected; no raw body is published.
    require(code in r.stderr, "wrong error for expected " + code)
    NEGATIVE.append(code)


def revision(item: str) -> int:
    return int(scalar("SELECT current_revision FROM jianshi_cms.content_items "
                      "WHERE content_key=" + sql_quote(item) + ";"))


def uuid_for(item: str) -> str:
    value = scalar("SELECT id FROM jianshi_cms.content_items "
                   "WHERE content_key=" + sql_quote(item) + ";")
    require(bool(re.fullmatch(r"[0-9a-f-]{36}", value)), "bad synthetic item id")
    return value


def rid(n: int) -> str:
    require(1 <= n < 1000, "synthetic request id range")
    return "10000000-0000-4000-8000-" + f"{n:012x}"


def projection(*, bad: bool = False, version: int = 1) -> str:
    entry = {
        "title": "G2F 合成版本 " + str(version),
        "summary": "仅供一次性 PostgreSQL 容器测试的合成内容，不能发布到正式见势网站。",
        "category": "SYNTHETIC_TEST",
        "tags": ["G2F", "ISOLATED"],
        "language": "zh-CN",
        "source_verified_at": "2026-10-12",
        "source_refs": [
            {"kind": "PUBLIC_URL", "url": ("http://forbidden.test/token"
                                           if bad else "https://example.org/test-source")}
        ],
        "private_notes": "SYNTHETIC_PRIVATE_DO_NOT_PUBLISH",
        "unapproved_financial_claim": "SYNTHETIC_NO_REAL_FINANCE",
    }
    return sql_quote(json.dumps(entry, ensure_ascii=False, separators=(",", ":"))) + "::jsonb"


def refs() -> str:
    return """'["SYNTHETIC_AUTHOR_EVIDENCE"]'::jsonb"""


def create(actor: str, key: str, request: int, *, bad=False) -> str:
    value = scalar(svc(
        f"SELECT jianshi_cms.create_draft("
        f"'{actor}'::uuid, {sql_quote(key)}, 'SOLUTION_GUIDE', "
        f"{projection(bad=bad)}, {refs()}, '{rid(request)}'::uuid);"))
    require(re.fullmatch(r"[0-9a-f-]{36}", value) is not None, "create returned UUID")
    return value


def edit(actor: str, item: str, rev: int, request: int, *,
         rights=True, facts=True, bad=False, version=2) -> int:
    value = scalar(svc(
        "SELECT jianshi_cms.edit_draft("
        f"'{actor}'::uuid,'{item}'::uuid,{rev},"
        f"{projection(bad=bad, version=version)},{refs()},"
        f"{str(rights).lower()},{str(facts).lower()},'{rid(request)}'::uuid);"))
    return int(value)


def transition(actor: str, item: str, rev: int, state: str, request: int) -> int:
    return int(scalar(svc(
        "SELECT jianshi_cms.change_review_state("
        f"'{actor}'::uuid,'{item}'::uuid,{rev},"
        f"{sql_quote(state)},'{rid(request)}'::uuid,NULL);")))


def restore(actor: str, item: str, rev: int, source: int, request: int) -> int:
    return int(scalar(svc(
        "SELECT jianshi_cms.restore_draft_revision("
        f"'{actor}'::uuid,'{item}'::uuid,{rev},{source},'{rid(request)}'::uuid);")))


def initialize():
    require(os.environ.get("JIANSHI_G2F_EPHEMERAL_ONLY") == "1", "ephemeral guard")
    require(bool(re.fullmatch(r"[a-f0-9]{12,64}", CONTAINER)), "Docker container id required")
    require(DB == "jianshi_g2f", "must use disposable database, never remote host")
    require(not any(os.environ.get(x) for x in (
        "SUPABASE_URL", "SUPABASE_DB_URL", "DATABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ACCESS_TOKEN")),
        "external database credentials detected in isolated runner")
    bootstrap = """
DO $fixture$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='service_role') THEN
    CREATE ROLE service_role NOLOGIN BYPASSRLS;
  END IF;
END $fixture$;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE auth.users (id uuid PRIMARY KEY, deleted_at timestamptz);
CREATE TABLE auth.sessions (
  id uuid PRIMARY KEY, user_id uuid REFERENCES auth.users(id),
  not_after timestamptz
);
"""
    run_sql(bootstrap)
    for filename in MIGRATIONS:
        source = ROOT / "db" / "migrations" / filename
        require(source.is_file(), "real migration not found: " + filename)
        content = source.read_text(encoding="utf-8")
        require("jianshi_cms" in content or filename.startswith("0037"), "bad migration")
        run_sql(content)
    # Production-like RLS and role grants are now installed by the REAL migrations.
    priv = scalar(
        """SELECT (
          (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
           WHERE n.nspname='jianshi_cms' AND c.relkind='r'
             AND c.relrowsecurity AND c.relforcerowsecurity)=6
          AND NOT has_schema_privilege('authenticated','jianshi_cms','USAGE')
          AND NOT has_schema_privilege('anon','jianshi_cms','USAGE')
        )::text;""")
    require(priv == "true", "RLS and default-deny not installed")


def gate_test_and_synthetic_setup():
    check_denial(
        "SELECT jianshi_cms.create_draft("
        f"'{EDITOR}'::uuid,'SYNTHETIC_DENIED','SOLUTION_GUIDE',"
        f"{projection()},{refs()},'{rid(1)}'::uuid);",
        "CMS_WRITE_DISABLED")
    require(scalar("SELECT count(*) FROM jianshi_cms.content_items;") == "0",
            "closed gate must not write")

    users = (EDITOR, REVIEWER, PUBLISHER, OTHER, AUX_EDITOR)
    values = ",".join(f"('{u}'::uuid)" for u in users)
    run_sql(f"INSERT INTO auth.users(id) VALUES {values};")
    grants = [(EDITOR, "EDITOR"), (REVIEWER, "REVIEWER"),
              (PUBLISHER, "PUBLISHER"), (OTHER, "EDITOR"),
              (AUX_EDITOR, "EDITOR")]
    assignments = ",".join(f"('{u}'::uuid,{sql_quote(role)},true)" for u, role in grants)
    run_sql(
        "INSERT INTO jianshi_cms.editor_grants(actor_user_id,permission,active) "
        f"VALUES {assignments};"
        """UPDATE public.auth_launch_gates SET
             custom_smtp_configured=true,
             magic_link_e2e_pass=true,
             jwt_ab_isolation_pass=true,
             save_e2e_pass=true,
             watch_e2e_pass=true,
             alerts_isolation_pass=true,
             session_logout_refresh_pass=true,
             security_review_pass=true;
           UPDATE public.product_feature_flags
             SET enabled=true WHERE feature_key IN ('cms_editor','account_auth');""")
    require(scalar("SELECT public.auth_launch_ready_v01()::text;") == "true",
            "ephemeral positive gate fixture not ready")
    # Before every positive call the SQL function also verifies current_user.
    check_denial(
        "SELECT jianshi_cms.ensure_write_gate("
        f"'{EDITOR}'::uuid,ARRAY['EDITOR']::text[]);",
        "permission denied", role="authenticated")
    # With flags open but invoking via superuser directly, the current_user
    # assertion in the true SQL kernel must still deny bypass.
    check_denial(
        "SELECT jianshi_cms.ensure_write_gate("
        f"'{EDITOR}'::uuid,ARRAY['EDITOR']::text[]);",
        "CMS_TRUSTED_SERVER_ONLY", role="postgres")


def lifecycle():
    ident = create(EDITOR, CURRENT, 10)
    require(edit(EDITOR, ident, 1, 11, version=2) == 2, "first edit")
    check_denial(svc(
        "SELECT jianshi_cms.restore_draft_revision("
        f"'{OTHER}'::uuid,'{ident}'::uuid,2,1,'{rid(12)}'::uuid);"),
        "CMS_OWNER_DENIED", role="postgres")  # nested SET ROLE service_role
    check_denial(
        "SELECT jianshi_cms.restore_draft_revision("
        f"'{EDITOR}'::uuid,'{ident}'::uuid,1,1,'{rid(12)}'::uuid);",
        "CMS_STALE_REVISION")
    check_denial(
        "SELECT jianshi_cms.restore_draft_revision("
        f"'{EDITOR}'::uuid,'{ident}'::uuid,2,2,'{rid(12)}'::uuid);",
        "CMS_INVALID_SOURCE_REVISION")
    require(restore(EDITOR, ident, 2, 1, 13) == 3, "real historical restoration")
    require(scalar(
        "SELECT (NOT rights_declared AND NOT facts_checked)::text "
        f"FROM jianshi_cms.content_revisions WHERE item_id='{ident}'::uuid "
        "AND revision=3;") == "true", "restored evidence flags not reset")
    require(scalar(
        "SELECT (rights_declared AND facts_checked)::text "
        f"FROM jianshi_cms.content_revisions WHERE item_id='{ident}'::uuid "
        "AND revision=2;") == "true", "historical revision changed")
    require(scalar(
        f"SELECT count(*) FROM jianshi_cms.review_events WHERE item_id='{ident}'::uuid "
        "AND actor_action='RESTORE';") == "1", "restore audit missing")

    check_denial(
        "SELECT jianshi_cms.restore_draft_revision("
        f"'{EDITOR}'::uuid,'{ident}'::uuid,3,1,'{rid(13)}'::uuid);",
        "CMS_DUPLICATE_REQUEST")
    require(transition(EDITOR, ident, 3, "IN_REVIEW", 14) == 4, "review submit")
    check_denial(
        "SELECT jianshi_cms.change_review_state("
        f"'{REVIEWER}'::uuid,'{ident}'::uuid,4,'APPROVED','{rid(15)}'::uuid,NULL);",
        "CMS_EVIDENCE_OR_RIGHTS_MISSING")
    check_denial(
        "SELECT jianshi_cms.change_review_state("
        f"'{EDITOR}'::uuid,'{ident}'::uuid,4,'APPROVED','{rid(15)}'::uuid,NULL);",
        "CMS_INDEPENDENT_REVIEW_REQUIRED")
    require(transition(REVIEWER, ident, 4, "REJECTED", 16) == 5, "reject")
    require(transition(EDITOR, ident, 5, "DRAFT", 17) == 6, "reopen")
    require(edit(EDITOR, ident, 6, 18, version=4) == 7, "fresh evidence edit")
    require(transition(EDITOR, ident, 7, "IN_REVIEW", 19) == 8, "resubmit")
    require(transition(REVIEWER, ident, 8, "APPROVED", 20) == 9, "independent review")
    check_denial(
        "SELECT jianshi_cms.change_review_state("
        f"'{EDITOR}'::uuid,'{ident}'::uuid,9,'PUBLISHED','{rid(21)}'::uuid,NULL);",
        "CMS_PUBLISHER_DENIED")
    require(transition(PUBLISHER, ident, 9, "PUBLISHED", 22) == 10, "publish")
    projection_ok = scalar(
        "SELECT (public_allowlist_json ? 'title' "
        "AND public_allowlist_json ? 'source_refs' "
        "AND NOT public_allowlist_json ? 'private_notes' "
        "AND NOT public_allowlist_json ? 'unapproved_financial_claim' "
        "AND (SELECT count(*) FROM jsonb_object_keys(public_allowlist_json))=11)::text "
        f"FROM jianshi_cms.publication_snapshots WHERE item_id='{ident}'::uuid;")
    require(projection_ok == "true", "publication allowlist leaking private data")
    check_denial(
        "SELECT jianshi_cms.restore_draft_revision("
        f"'{EDITOR}'::uuid,'{ident}'::uuid,10,1,'{rid(23)}'::uuid);",
        "CMS_RESTORE_REQUIRES_DRAFT")
    require(transition(PUBLISHER, ident, 10, "UNPUBLISHED", 24) == 11, "retract")
    require(transition(EDITOR, ident, 11, "IN_REVIEW", 25) == 12, "re-review")
    require(transition(REVIEWER, ident, 12, "APPROVED", 26) == 13, "approve again")
    require(transition(PUBLISHER, ident, 13, "PUBLISHED", 27) == 14, "publish again")
    snap = scalar(
        "SELECT count(*)::text||':'||"
        "count(*) FILTER(WHERE lifecycle='RETRACTED')::text||':'||"
        "count(*) FILTER(WHERE lifecycle='STAGED')::text "
        f"FROM jianshi_cms.publication_snapshots WHERE item_id='{ident}'::uuid;")
    require(snap == "2:1:1", "retraction/snapshot isolation failed")
    require(revision(CURRENT) == 14, "revision chain incomplete")
    return ident


def invalid_source():
    ident = create(EDITOR, BAD_SOURCE, 50, bad=True)
    require(edit(EDITOR, ident, 1, 51, bad=True) == 2, "bad source edit")
    require(transition(EDITOR, ident, 2, "IN_REVIEW", 52) == 3, "bad source submit")
    require(transition(REVIEWER, ident, 3, "APPROVED", 53) == 4, "bad source approved for test")
    check_denial(
        "SELECT jianshi_cms.change_review_state("
        f"'{PUBLISHER}'::uuid,'{ident}'::uuid,4,'PUBLISHED','{rid(54)}'::uuid,NULL);",
        "CMS_SOURCE_UNSAFE")
    require(scalar(
        f"SELECT count(*) FROM jianshi_cms.publication_snapshots WHERE item_id='{ident}'::uuid;")
        == "0", "invalid source leaked to publication")


def competing_clients():
    ident = create(AUX_EDITOR, CONCURRENT, 60)
    require(edit(AUX_EDITOR, ident, 1, 61) == 2, "concurrent base")
    # First real client explicitly holds FOR UPDATE; a second client races
    # against the same expected revision. Exactly one can commit.
    first_sql = svc(
        "BEGIN;\n"
        f"SELECT id FROM jianshi_cms.content_items WHERE id='{ident}'::uuid FOR UPDATE;\n"
        "SELECT pg_sleep(1.4);\n"
        "SELECT jianshi_cms.edit_draft("
        f"'{AUX_EDITOR}'::uuid,'{ident}'::uuid,2,"
        f"{projection(version=3)},{refs()},true,true,'{rid(62)}'::uuid);\nCOMMIT;")
    second_sql = svc(
        "SELECT jianshi_cms.edit_draft("
        f"'{AUX_EDITOR}'::uuid,'{ident}'::uuid,2,"
        f"{projection(version=4)},{refs()},true,true,'{rid(63)}'::uuid);")
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(run_sql, first_sql, allow_error=True, timeout=35)
        time.sleep(0.35)
        b = pool.submit(run_sql, second_sql, allow_error=True, timeout=35)
        a_result, b_result = a.result(), b.result()
    states = [a_result, b_result]
    require(sum(r.returncode == 0 for r in states) == 1,
            "concurrency must have exactly one successful winner")
    require(sum(r.returncode != 0 and "CMS_STALE_REVISION" in r.stderr
                for r in states) == 1, "loser must be SQL revision conflict")
    require(revision(CONCURRENT) == 3, "concurrency created extra versions")
    require(scalar(f"SELECT count(*) FROM jianshi_cms.content_revisions "
                   f"WHERE item_id='{ident}'::uuid;") == "3", "lost update")
    NEGATIVE.append("CONCURRENT_STALE_REVISION")


def main():
    initialize()
    gate_test_and_synthetic_setup()
    main_id = lifecycle()
    invalid_source()
    competing_clients()
    # Only synthetic fixture rows should exist in disposable PG database.
    totals = scalar(
        "SELECT (SELECT count(*) FROM jianshi_cms.content_items)::text||':'||"
        "(SELECT count(*) FROM jianshi_cms.publication_snapshots)::text||':'||"
        "(SELECT count(*) FROM jianshi_cms.editor_grants)::text;")
    require(totals == "3:2:5", "unexpected disposable fixture row counts")
    require(len(NEGATIVE) >= 10, "insufficient negative privilege cases")
    print("G2F_REAL_POSTGRES_E2E_PASS " + json.dumps({
        "engine": "postgres:16/disposable",
        "actual_migrations": len(MIGRATIONS),
        "real_transaction_flow": "CREATE_EDIT_RESTORE_REVIEW_PUBLISH_RETRACT_REPUBLISH",
        "real_competing_clients": "ONE_WINNER_ONE_STALE",
        "verified_negative_cases": len(NEGATIVE),
        "source_projection_private_fields": "DENIED",
        "isolated_fixture_counts": totals,
        "external_database_connections": 0,
        "production_or_staging_changes": 0,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("G2F_ISOLATED_E2E_FAILED " + str(exc)[:1000], file=sys.stderr)
        sys.exit(1)
