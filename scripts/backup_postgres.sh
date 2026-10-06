#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL required}"
OUT_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$OUT_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$OUT_DIR/jianshi_${STAMP}.sql.gz"
pg_dump "$DATABASE_URL" --no-owner --no-privileges | gzip -9 > "$OUT"
sha256sum "$OUT" > "$OUT.sha256"
echo "BACKUP_PASS $OUT"
