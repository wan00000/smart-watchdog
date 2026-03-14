#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/watchdog.conf"

# shellcheck source=/dev/null
source "$CONFIG_FILE"

mkdir -p "$REPORT_DIR"
: > "$CLEANUP_LOG_FILE"

if [[ ! -d "$DB_ROOT" ]]; then
    echo "DB root not found: $DB_ROOT" >&2
    exit 1
fi

mapfile -t targets < <(find "$DB_ROOT" -mindepth 1 -mtime -"$CLEANUP_DAYS" -print | awk '{ print length, $0 }' | sort -rn | cut -d' ' -f2-)

for path in "${targets[@]}"; do
    [[ -e "$path" ]] || continue
    printf '%s\n' "$path" | tee -a "$CLEANUP_LOG_FILE"
    rm -rf -- "$path"
done
