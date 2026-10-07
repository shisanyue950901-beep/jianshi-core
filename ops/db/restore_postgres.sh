#!/usr/bin/env bash
set -euo pipefail

: "${1:?Usage: restore_postgres.sh <backup.dump.enc>}"
: "${TARGET_DATABASE_URL:?TARGET_DATABASE_URL is required}"
: "${BACKUP_ENCRYPTION_PASSPHRASE:?BACKUP_ENCRYPTION_PASSPHRASE is required}"

enc="$1"

if [[ "${ALLOW_RESTORE:-NO}" != "YES" ]]; then
  echo "Refusing restore: set ALLOW_RESTORE=YES after confirming TARGET_DATABASE_URL is an isolated recovery target." >&2
  exit 2
fi

tmp="$(mktemp)"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2   -in "$enc"   -out "$tmp"   -pass env:BACKUP_ENCRYPTION_PASSPHRASE

pg_restore --list "$tmp" >/dev/null

# Restore into an isolated/fresh PostgreSQL recovery target.
# Do not point this at Production.
pg_restore   --dbname="$TARGET_DATABASE_URL"   --no-owner   --no-acl   --exit-on-error   "$tmp"

echo "RESTORE_STATUS=PASS_COMPLETED"
