#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/watchdog.conf"

# shellcheck source=/dev/null
source "$CONFIG_FILE"

mkdir -p "$REPORT_DIR"

latest_file() {
    local pattern="$1"
    local latest
    latest=$(find "$REPORT_DIR" -maxdepth 1 -type f -name "$pattern" -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n1 | cut -d' ' -f2-)
    printf '%s' "$latest"
}

health_file="$(latest_file 'health_*.log')"
cleanup_file="$(latest_file 'cleanup_*.log')"
blocked_file="$(latest_file 'blocked_ips_*.txt')"
suspicious_file="$(latest_file 'suspicious_ips_*.txt')"
top_file="$(latest_file 'top_ips_*.txt')"

health_status='No health log yet'
if [[ -n "$health_file" && -f "$health_file" ]]; then
    health_status="$(tail -n1 "$health_file")"
fi

cleanup_count=0
if [[ -n "$cleanup_file" && -f "$cleanup_file" ]]; then
    cleanup_count=$(grep -c '^/' "$cleanup_file" || true)
fi

blocked_count=0
if [[ -n "$blocked_file" && -f "$blocked_file" ]]; then
    blocked_count=$(grep -Ec '^[^[:space:]]+[[:space:]]+[0-9]+$' "$blocked_file" || true)
fi

suspicious_count=0
if [[ -n "$suspicious_file" && -f "$suspicious_file" ]]; then
    suspicious_count=$(grep -Ec '^[^[:space:]]+[[:space:]]+[0-9]+$' "$suspicious_file" || true)
fi

{
    echo 'Health status:'
    echo "$health_status"
    echo
    echo 'Suspicious IPs:'
    echo "$suspicious_count"
    echo
    echo 'Blocked IPs:'
    echo "$blocked_count"
    echo
    echo 'Cleanup status:'
    echo "$cleanup_count removed in last run"
    echo
    echo 'Top IP addresses:'
    if [[ -n "$top_file" && -f "$top_file" ]]; then
        cat "$top_file"
    else
        echo 'No report yet'
    fi
    echo
    echo 'Generated at:'
    date '+%Y-%m-%d %H:%M:%S'
} > "$DASHBOARD_FILE"

printf 'Dashboard written to %s\n' "$DASHBOARD_FILE"
