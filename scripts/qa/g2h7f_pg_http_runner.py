#!/usr/bin/env python3
"""G2-H.7F disposable localhost HTTP -> *real* postgres:16 RPC harness.

No Supabase Data API, no cloud endpoint, no real secrets. Must run only AFTER
g2f_postgres_real_e2e.py has initialized a disposable Docker PG fixture.
The exposed HTTP listener and business gates exist only within this test step.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = os.environ.get("G2F_POSTGRES_CONTAINER", "")
DATABASE = os.environ.get("G2F_POSTGRES_DATABASE", "")
KEY = "SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET"
DIGEST = re.compile(r"^[a-f0-9]{64}$")
STAMP = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")
FROZEN = ("account_auth", "cms_editor", "v2_matchmaking")


def require(condition, reason):
    if not condition:
        raise RuntimeError("G2H7F_FAIL_CLOSED_" + reason)


def run_sql(query, error_ok=False):
    args = [
        "docker", "exec", "-i", "-u", "postgres", CONTAINER,
        "psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1",
        "-d", DATABASE,
    ]
    process = subprocess.run(args, input=query, text=True,
                             capture_output=True, timeout=25, check=False)
    if process.returncode:
        if error_ok:
            return None
        raise RuntimeError("G2H7F_DISPOSABLE_SQL_DENIED")
    return process.stdout.strip()


def check_environment():
    require(os.environ.get("JIANSHI_G2F_EPHEMERAL_ONLY") == "1",
            "EPHEMERAL_FLAG")
    require(os.environ.get("JIANSHI_G2H7F_DISPOSABLE_ONLY") == "1",
            "HTTP_DISPOSABLE_FLAG")
    require(re.fullmatch(r"[0-9a-f]{12,64}", CONTAINER) is not None,
            "NO_DOCKER_CONTAINER")
    require(DATABASE == "jianshi_g2f", "BAD_DATABASE")
    for name in (
        "DATABASE_URL", "SUPABASE_URL", "SUPABASE_DB_URL",
        "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEY",
        "SUPABASE_ACCESS_TOKEN", "CLOUDFLARE_API_TOKEN",
    ):
        require(not os.environ.get(name), "EXTERNAL_CREDS")
    status = subprocess.run([
        "docker", "inspect", CONTAINER, "--format", "{{.State.Running}}"
    ], check=False, capture_output=True, text=True, timeout=10)
    require(status.returncode == 0 and status.stdout.strip() == "true",
            "CONTAINER_NOT_RUNNING")
    require(run_sql(
        "SELECT (to_regclass('jianshi_cms.bff_email_challenges') "
        "IS NOT NULL)::text;"
    ) == "true", "ACTUAL_0062_MIGRATION_MISSING")
    require(run_sql(
        "SELECT (NOT (SELECT enabled FROM public.product_feature_flags "
        "WHERE feature_key='account_auth') AND "
        "NOT (SELECT enabled FROM public.product_feature_flags "
        "WHERE feature_key='cms_editor'))::text;"
    ) == "true", "ORIGINAL_GATES_ALREADY_OPEN")


def gate(opened: bool):
    if opened:
        query = """
UPDATE public.auth_launch_gates SET
 custom_smtp_configured=true,
 magic_link_e2e_pass=true,
 jwt_ab_isolation_pass=true,
 save_e2e_pass=true,
 watch_e2e_pass=true,
 alerts_isolation_pass=true,
 session_logout_refresh_pass=true,
 security_review_pass=true;
UPDATE public.product_feature_flags SET enabled=true
 WHERE feature_key IN ('account_auth','cms_editor');
SELECT public.auth_launch_ready_v01()::text;
"""
        require(run_sql(query) == "true", "DISPOSABLE_AUTH_GATE_NOT_READY")
    else:
        run_sql("""
UPDATE public.product_feature_flags SET enabled=false
 WHERE feature_key IN ('account_auth','cms_editor','v2_matchmaking');
""")


def rpc(body):
    require(isinstance(body, dict), "JSON_NOT_OBJECT")
    action = body.get("action")
    digests = body.get("stateDigest"), body.get("cookieDigest")
    require(action in ("issue", "consume") and
            all(isinstance(s, str) and DIGEST.fullmatch(s) for s in digests),
            "INPUT_REJECTED")
    if action == "issue":
        require(set(body) == {"action", "stateDigest", "cookieDigest",
                              "expiresAt"}, "ISSUE_KEYS")
        stamp = body["expiresAt"]
        require(isinstance(stamp, str) and STAMP.fullmatch(stamp),
                "EXPIRY_INVALID")
        expires = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        require(now < expires <= now + timedelta(minutes=5),
                "EXPIRY_OUT_OF_RANGE")
        query = ("SET ROLE service_role;\n"
                 "SELECT jianshi_cms.bff_issue_email_state_v01("
                 f"'{digests[0]}','{digests[1]}','{stamp}'::timestamptz)::text;")
        require(run_sql(query) == "true", "ISSUE_FAILED")
        return {"issued": True}
    require(set(body) == {"action", "stateDigest", "cookieDigest"},
            "CONSUME_KEYS")
    query = ("SET ROLE service_role;\n"
             "SELECT jianshi_cms.bff_consume_email_state_v01("
             f"'{digests[0]}','{digests[1]}')::text;")
    raw = run_sql(query)
    parsed = json.loads(raw)
    require(parsed in ({"used": True}, {"used": False}), "RPC_BAD_RETURN")
    return parsed


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        # No inbound URI, cookie, body, header or SQL error may go to CI.
        return

    def reply(self, status, data):
        payload = json.dumps(data, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(payload)))
        # Close every connection: rejected requests may have unread request
        # bodies; reusing the socket would allow HTTP request desynchronization.
        self.send_header("Connection", "close")
        self.close_connection = True
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.reply(404, {"error": "NOT_FOUND"})

    def do_POST(self):
        try:
            require(self.client_address[0] == "127.0.0.1", "LOOPBACK_ONLY")
            require(self.path == "/v1/email-state", "ENDPOINT_DENIED")
            require(self.headers.get("Authorization") == "Bearer " + KEY,
                    "FAKE_TEST_KEY_DENIED")
            require(self.headers.get("X-Jianshi-Test-Boundary")
                    == "SYNTHETIC_H7F_ONLY", "WRONG_TEST_BOUNDARY")
            require(self.headers.get("Content-Type") == "application/json",
                    "CONTENT_TYPE_DENIED")
            length = self.headers.get("Content-Length")
            require(length and length.isdigit() and 1 <= int(length) <= 512,
                    "BODY_TOO_LARGE")
            body = json.loads(self.rfile.read(int(length)).decode("utf-8"))
            self.reply(200, rpc(body))
        except Exception:
            # Fail closed with generic errors. Never print input or SQL details.
            self.reply(403, {"error": "DENIED"})


def main():
    check_environment()
    # Freeze validation first; even with valid secrets the real Staging remains
    # completely untouched. Gate opening is only on the disposable docker DB.
    gate(True)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.daemon_threads = True
    worker = threading.Thread(target=httpd.serve_forever, daemon=True)
    worker.start()
    try:
        env = dict(os.environ)
        env.update({
            "JIANSHI_G2H7F_URL":
                f"http://127.0.0.1:{httpd.server_address[1]}/v1/email-state",
            "JIANSHI_G2H7F_DISPOSABLE_ONLY": "1",
        })
        result = subprocess.run(
            ["node", "--test", "tests/g2h7f_worker_pg_http.test.mjs"],
            cwd=ROOT, env=env, check=False, capture_output=True, text=True,
            timeout=160,
        )
        # Only synthetic test diagnostics may be echoed; nothing user-derived.
        print(result.stdout[-12000:])
        if result.returncode:
            print("G2H7F_NODE_PG_INTEGRATION_FAILED",
                  result.stderr[-1800:], file=sys.stderr)
            raise RuntimeError("WORKER_HTTP_PG_TEST_FAILURE")
        print("G2H7F_REAL_POSTGRES_HTTP_INTEGRATION_PASS "
              '{"database":"postgres:16/disposable",'
              '"transport":"127.0.0.1-only-HTTP",'
              '"auth":"SYNTHETIC_FAKE_KEY",'
              '"remote_cloud_calls":0}')
    finally:
        httpd.shutdown()
        httpd.server_close()
        # Close the gates EVEN if tests fail. PG container is then destroyed
        # automatically by GitHub Actions as additional containment.
        gate(False)
        require(run_sql(
            "SELECT (NOT (SELECT enabled FROM public.product_feature_flags "
            "WHERE feature_key='account_auth') AND "
            "NOT (SELECT enabled FROM public.product_feature_flags "
            "WHERE feature_key='cms_editor'))::text;"
        ) == "true", "DISPOSABLE_GATE_REOPENED")
        print("G2H7F_DISPOSABLE_GATES_RELOCKED_PASS")
    # Correctly fail any operation on closed gates; no state inserted.
    failed = run_sql(
        "SET ROLE service_role;\n"
        "SELECT jianshi_cms.bff_issue_email_state_v01("
        f"'{('f' * 64)}','{('e' * 64)}',now()+interval '3 minutes');",
        error_ok=True,
    )
    require(failed is None, "SQL_GATE_OPEN_AFTER_TEST")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("G2H7F_FAIL_CLOSED", type(error).__name__, file=sys.stderr)
        sys.exit(1)
