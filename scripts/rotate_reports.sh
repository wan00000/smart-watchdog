#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/watchdog.conf"

# shellcheck source=/dev/null
source "$CONFIG_FILE"

mkdir -p "$REPORT_DIR" "$ARCHIVE_DIR"

archive_name="$ARCHIVE_DIR/${ARCHIVE_PREFIX}_$(date +%F_%H%M%S).tar.gz"

mapfile -t aged_reports < <(find "$REPORT_DIR" -maxdepth 1 -type f -mtime +"$REPORT_RETENTION_DAYS" | sort)

if [[ ${#aged_reports[@]} -gt 0 ]]; then
    tar -czf "$archive_name" -C "$REPORT_DIR" $(printf '%q ' "${aged_reports[@]##$REPORT_DIR/}")
    for file in "${aged_reports[@]}"; do
        rm -f -- "$file"
        printf 'Archived and removed report: %s\n' "$file"
    done
else
    printf 'No aged reports to archive.\n'
fi

find "$ARCHIVE_DIR" -maxdepth 1 -type f -name "${ARCHIVE_PREFIX}_*.tar.gz" -mtime +"$ARCHIVE_RETENTION_DAYS" -print -delete || true
