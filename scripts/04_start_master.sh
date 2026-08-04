#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$ROOT/config/network.env"

if [ "$EUID" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
PTP4L_BIN="${PTP4L_BIN:-$(command -v ptp4l || echo /usr/sbin/ptp4l)}"
PHC2SYS_BIN="${PHC2SYS_BIN:-$(command -v phc2sys || echo /usr/sbin/phc2sys)}"

$SUDO pkill -9 ptp4l 2>/dev/null || true
$SUDO pkill -9 phc2sys 2>/dev/null || true
sleep 1
mkdir -p "$ROOT/logs"

$SUDO nohup "$PTP4L_BIN" -i "$MASTER_IFACE" -f "$ROOT/config/master_1588v2_e2e.cfg" -m   >"$ROOT/logs/ptp4l_1588_e2e.log" 2>&1 &
$SUDO nohup "$PHC2SYS_BIN" -s CLOCK_REALTIME -c "$MASTER_IFACE"   --domainNumber="$PTP_DOMAIN" --step_threshold=1 -w -m   >"$ROOT/logs/phc2sys_1588_e2e.log" 2>&1 &

sleep 4
echo "== processes =="
ps aux | grep -E "ptp4l|phc2sys" | grep -v grep || true
echo "== ptp4l log =="
tail -20 "$ROOT/logs/ptp4l_1588_e2e.log" || true
echo "== phc2sys log =="
tail -10 "$ROOT/logs/phc2sys_1588_e2e.log" || true
