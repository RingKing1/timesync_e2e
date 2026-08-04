#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$ROOT/config/network.env"
export MASTER_IFACE LIDAR_IP ORIN_A_IP ORIN_B_IP ORIN_IFACE ORIN_USER ORIN_PASSWORD
exec python3 "$ROOT/scripts/08_verify_all.py" --iface "$MASTER_IFACE"
