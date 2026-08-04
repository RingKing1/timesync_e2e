#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$ROOT/config/network.env"

if [ "$EUID" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
$SUDO pkill -9 ptp4l 2>/dev/null || true
$SUDO pkill -9 phc2sys 2>/dev/null || true
rm -f "$ROOT"/logs/*.log
echo "cleanup done"
