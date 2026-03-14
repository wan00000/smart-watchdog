#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/watchdog.conf"

# shellcheck source=/dev/null
source "$CONFIG_FILE"

pause_time="${1:-1}"
health_rc=0

"$SCRIPT_DIR/analyze_top_ips.sh"
"$SCRIPT_DIR/cleanup_recent.sh"

if ! printf '%s\n' "$pause_time" | python3 "$SCRIPT_DIR/health_check.py"; then
    health_rc=$?
fi

"$SCRIPT_DIR/generate_dashboard.sh"
exit "$health_rc"
