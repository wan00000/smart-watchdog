#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/watchdog.conf"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Config file not found: $CONFIG_FILE" >&2
    exit 1
fi

# Export sourced variables
set -a
source "$CONFIG_FILE"
set +a

pause_time="${1:-1}"
overall_rc=0

mkdir -p "$REPORT_DIR" "$LOG_DIR" "$ARCHIVE_DIR"

"$SCRIPT_DIR/analyze_top_ips.sh"
"$SCRIPT_DIR/cleanup_recent.sh"

if [[ "${HEALTH_CHECK_ENABLED:-1}" == "1" ]]; then
    if ! printf '%s\n' "$pause_time" | python3 "$SCRIPT_DIR/health_check.py"; then
        rc=$?
        overall_rc=$rc
    fi
fi

if [[ "${PROBE_ENABLED:-1}" == "1" ]]; then
    if ! python3 "$SCRIPT_DIR/probe_ips.py"; then
        rc=$?
        if [[ $overall_rc -eq 0 ]]; then
            overall_rc=$rc
        fi
    fi
fi

"$SCRIPT_DIR/generate_dashboard.sh"
exit "$overall_rc"
