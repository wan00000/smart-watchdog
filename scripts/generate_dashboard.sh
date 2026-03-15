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
probe_log_file="$(latest_file 'probe_*.log')"
probe_report_file="$(latest_file 'probe_*.jsonl')"

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

probe_summary='No probe report yet'
if [[ -n "$probe_report_file" && -f "$probe_report_file" ]]; then
    probe_summary="$(python3 - "$probe_report_file" <<'PY'
import json
import sys
from collections import Counter
from pathlib import Path

path = Path(sys.argv[1])
entries = []
for raw_line in path.read_text(encoding='utf-8').splitlines():
    line = raw_line.strip()
    if not line:
        continue
    try:
        entries.append(json.loads(line))
    except json.JSONDecodeError:
        continue

if not entries:
    print('No probe entries in latest report')
    raise SystemExit(0)

status_counter = Counter(str(item.get('status', 'unknown')) for item in entries)
open_ports = 0
probed_targets = 0
for item in entries:
    if item.get('status') == 'probed':
        probed_targets += 1
    for tcp_item in item.get('tcp_connect', []) or []:
        if tcp_item.get('ok'):
            open_ports += 1

print(f"Targets in latest report: {len(entries)}")
print(f"Probed targets: {probed_targets}")
print(f"TCP open results: {open_ports}")
for status, count in sorted(status_counter.items()):
    print(f"Status {status}: {count}")
PY
)"
fi

probe_log_tail='No probe log yet'
if [[ -n "$probe_log_file" && -f "$probe_log_file" ]]; then
    probe_log_tail="$(tail -n 12 "$probe_log_file")"
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
    echo 'Probe summary:'
    echo "$probe_summary"
    echo
    echo 'Top IP addresses:'
    if [[ -n "$top_file" && -f "$top_file" ]]; then
        cat "$top_file"
    else
        echo 'No report yet'
    fi
    echo
    echo 'Latest probe log lines:'
    echo "$probe_log_tail"
    echo
    echo 'Generated at:'
    date '+%Y-%m-%d %H:%M:%S'
} > "$DASHBOARD_FILE"

printf 'Dashboard written to %s\n' "$DASHBOARD_FILE"
