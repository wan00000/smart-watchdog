#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_ROOT="$SCRIPT_DIR/database/db"

rm -rf "$DB_ROOT"
mkdir -p "$DB_ROOT/job_old" "$DB_ROOT/job_recent" "$DB_ROOT/tmp_recent/nested"
printf 'old data\n' > "$DB_ROOT/job_old/keep.txt"
printf 'recent data\n' > "$DB_ROOT/job_recent/remove.txt"
printf 'nested recent\n' > "$DB_ROOT/tmp_recent/nested/remove.txt"

touch -d '10 days ago' "$DB_ROOT/job_old" "$DB_ROOT/job_old/keep.txt"
touch -d '1 day ago' "$DB_ROOT/job_recent" "$DB_ROOT/job_recent/remove.txt" "$DB_ROOT/tmp_recent" "$DB_ROOT/tmp_recent/nested" "$DB_ROOT/tmp_recent/nested/remove.txt"

echo "Demo environment prepared under $DB_ROOT"
