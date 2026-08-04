#!/bin/bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y linuxptp
for bin in ptp4l phc2sys pmc; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERROR: $bin not found"
    exit 1
  fi
done
echo "linuxptp ready"
