#!/usr/bin/env bash
set -euo pipefail

: "${JIANSHI_DATABASE_URL:?JIANSHI_DATABASE_URL is required}"
: "${BACKUP_ENCRYPTION_PASSPHRASE:?BACKUP_ENCRYPTION_PASSPHRASE is required}"

OUT_DIR="${BACKUP_OUTPUT_DIR:-backup-output}"
mkdir -p "$OUT_DIR"

ts="$(date -u +%Y%m%dT%H%M%SZ)"
base="$OUT_DIR/jianshi-postgres-${ts}"
plain="${base}.dump"
enc="${base}.dump.enc"
manifest="${base}.sha256"

cleanup() {
  rm -f "$plain"
}
trap cleanup EXIT

# Full logical backup for portability. This captures application/auth metadata
# available to the database owner. Supabase Storage object bytes are NOT inside
# PostgreSQL and must be backed up separately if/when Storage is used.
pg_dump "$JIANSHI_DATABASE_URL"   --format=custom   --no-owner   --no-acl   --file="$plain"

# Basic structural validation before encryption.
pg_restore --list "$plain" >/dev/null

openssl enc -aes-256-cbc -pbkdf2 -salt   -in "$plain"   -out "$enc"   -pass env:BACKUP_ENCRYPTION_PASSPHRASE

sha256sum "$enc" > "$manifest"

echo "BACKUP_FILE=$enc"
echo "MANIFEST_FILE=$manifest"
echo "BACKUP_STATUS=PASS_CREATED_ENCRYPTED"
