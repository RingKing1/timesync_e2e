#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$ROOT/config/network.env"

echo "Setting $MASTER_IFACE to $MASTER_IP/$MASTER_PREFIX"
sudo ip link set "$MASTER_IFACE" up
sudo ip addr flush dev "$MASTER_IFACE"
sudo ip addr add "$MASTER_IP/$MASTER_PREFIX" dev "$MASTER_IFACE"
ip -brief addr show "$MASTER_IFACE"
echo
echo "Permanent network config still needs netplan or NetworkManager."
