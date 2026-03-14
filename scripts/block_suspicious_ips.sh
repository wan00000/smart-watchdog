#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/config/watchdog.conf"

# shellcheck source=/dev/null
source "$CONFIG_FILE"

INPUT_FILE="${1:-$SUSPICIOUS_IP_REPORT_FILE}"
mkdir -p "$REPORT_DIR"
: > "$BLOCKED_IP_REPORT_FILE"

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Suspicious IP report not found: $INPUT_FILE" >&2
    exit 1
fi

run_cmd() {
    if [[ "$IPTABLES_DRY_RUN" == "1" ]]; then
        printf '[DRY-RUN] '
        printf '%q ' "$@"
        printf '\n'
        return 0
    fi
    "$@"
}

ensure_chain() {
    if "$IPTABLES_BIN" -S "$IPTABLES_CHAIN" >/dev/null 2>&1; then
        return 0
    fi
    run_cmd "$IPTABLES_BIN" -N "$IPTABLES_CHAIN"
    run_cmd "$IPTABLES_BIN" -C INPUT -j "$IPTABLES_CHAIN" >/dev/null 2>&1 || \
        run_cmd "$IPTABLES_BIN" -I INPUT 1 -j "$IPTABLES_CHAIN"
}

ensure_chain

IFS=',' read -r -a ports <<< "$BLOCK_TARGET_PORTS"

while read -r ip count; do
    [[ -n "$ip" && -n "$count" ]] || continue

    for port in "${ports[@]}"; do
        port_trimmed="${port// /}"
        rule=("$IPTABLES_BIN" -C "$IPTABLES_CHAIN" -s "$ip" -p tcp --dport "$port_trimmed" -m comment --comment "$BLOCK_REASON" -j DROP)
        if "${rule[@]}" >/dev/null 2>&1; then
            :
        else
            run_cmd "$IPTABLES_BIN" -A "$IPTABLES_CHAIN" -s "$ip" -p tcp --dport "$port_trimmed" -m comment --comment "$BLOCK_REASON" -j DROP
        fi
    done

    printf '%s %s\n' "$ip" "$count" | tee -a "$BLOCKED_IP_REPORT_FILE" >/dev/null

    if [[ "$ALERT_ON_BLOCK" == "1" && "$EMAIL_ALERTS_ENABLED" == "1" ]]; then
        ALERT_EMAIL_TO="$ALERT_EMAIL_TO" ALERT_EMAIL_FROM="$ALERT_EMAIL_FROM" SMTP_HOST="$SMTP_HOST" SMTP_PORT="$SMTP_PORT" \
            python3 "$SCRIPT_DIR/alert.py" \
            "ALERT - Suspicious IP blocked" \
            "Blocked IP $ip after $count requests exceeded threshold $SUSPICIOUS_THRESHOLD."
    fi
done < "$INPUT_FILE"
