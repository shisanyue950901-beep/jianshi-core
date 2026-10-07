#!/usr/bin/env bash
set -euo pipefail

: "${1:?Usage: verify_backup.sh <backup.dump.enc> [manifest.sha256]}"
: "${BACKUP_ENCRYPTION_PASSPHRASE:?BACKUP_ENCRYPTION_PASSPHRASE is required}"

enc="$1"
manifest="${2:-${enc%.dump.enc}.sha256}"

if [[ -f "$manifest" ]]; then
  (cd "$(dirname "$manifest")" && sha256sum -c "$(basename "$manifest")")
fi

tmp="$(mktemp)"
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2   -in "$enc"   -out "$tmp"   -pass env:BACKUP_ENCRYPTION_PASSPHRASE

pg_restore --list "$tmp" >/dev/null

echo "BACKUP_VERIFY=PASS"
