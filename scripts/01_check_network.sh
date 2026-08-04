#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$ROOT/config/network.env"

echo "== Interface =="
ip link show "$MASTER_IFACE"
echo
echo "== Timestamping =="
sudo ethtool -T "$MASTER_IFACE"
echo
if sudo ethtool -T "$MASTER_IFACE" 2>/dev/null | grep -q "hardware-transmit" &&
   sudo ethtool -T "$MASTER_IFACE" 2>/dev/null | grep -q "hardware-receive"; then
  echo "Hardware timestamping: OK"
else
  echo "Hardware timestamping: NOT OK"
  exit 1
fi
