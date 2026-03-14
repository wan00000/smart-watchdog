#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/watchdog.conf"

# shellcheck source=/dev/null
source "$CONFIG_FILE"

mkdir -p "$REPORT_DIR"

if [[ ! -f "$ACCESS_LOG_FILE" ]]; then
    echo "Access log not found: $ACCESS_LOG_FILE" >&2
    exit 1
fi

# Requirement-aligned output: <ip_address> <count>
awk '{print $1}' "$ACCESS_LOG_FILE" \
    | sort \
    | uniq -c \
    | sort -k1,1nr -k2,2 \
    | head -n "$TOP_N" \
    | awk '{print $2, $1}' | tee "$TOP_IP_REPORT_FILE"

# Enhancement: record suspicious IPs separately.
awk '{print $1}' "$ACCESS_LOG_FILE" \
    | sort \
    | uniq -c \
    | sort -k1,1nr -k2,2 \
    | awk -v threshold="$SUSPICIOUS_THRESHOLD" '{ if ($1 > threshold) print $2, $1 }' > "$SUSPICIOUS_IP_REPORT_FILE"

# Optional defensive action.
if [[ "$BLOCK_SUSPICIOUS_IPS" == "1" && -s "$SUSPICIOUS_IP_REPORT_FILE" ]]; then
    "$SCRIPT_DIR/block_suspicious_ips.sh" "$SUSPICIOUS_IP_REPORT_FILE"
fi
