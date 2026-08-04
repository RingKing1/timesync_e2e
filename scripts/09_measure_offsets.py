#!/usr/bin/env python3
"""Sample offsetFromMaster for Lidar, OrinA, and OrinB for a few seconds.

The script runs pmc on the time master and parses offsets reported by the
current 1588v2 L2 E2E domain.

Usage:
    python3 scripts/09_measure_offsets.py --seconds 5
    SUDO_PASSWORD=... python3 scripts/09_measure_offsets.py --seconds 5
"""

import argparse
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER_CONFIG = ROOT / "config" / "master_1588v2_e2e.cfg"
SUDO_PASSWORD = os.environ.get("SUDO_PASSWORD", "8966")

TARGETS = {
    "Lidar": os.environ.get("LIDAR_PTP_ID", "ec9f0d.fffe.00afcd"),
    "OrinA": os.environ.get("ORIN_A_PTP_ID", "c022f1.fffe.634415"),
    "OrinB": os.environ.get("ORIN_B_PTP_ID", "c022f1.fffe.634419"),
}


def read_offsets():
    cmd = [
        "sudo", "-S", "-p", "", "pmc", "-u", "-b", "1",
        "-f", str(MASTER_CONFIG), "GET CURRENT_DATA_SET",
    ]
    proc = subprocess.run(
        cmd, input=SUDO_PASSWORD + "\n",
        capture_output=True, text=True, timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError("pmc failed: %s" % proc.stderr.strip())

    offsets = {}
    current = None
    identity_re = re.compile(r"^\s*([0-9a-fA-F.]+)-\d+\s+seq")
    for line in proc.stdout.splitlines():
        m = identity_re.match(line)
        if m:
            current = m.group(1)
            continue
        if current and "offsetFromMaster" in line:
            try:
                offsets[current] = float(line.split()[-1])
            except ValueError:
                pass
    return offsets


def sample_once():
    data = read_offsets()
    out = {}
    for name, identity in TARGETS.items():
        out[name] = data.get(identity)
    return out


def main():
    parser = argparse.ArgumentParser(description="Measure PTP offset differences")
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    samples = []
    start = time.monotonic()
    deadline = start + args.seconds
    while time.monotonic() < deadline:
        try:
            samples.append(sample_once())
        except Exception as exc:
            print("sample error:", exc, file=sys.stderr)
        if time.monotonic() + args.interval < deadline:
            time.sleep(args.interval)

    if not samples:
        print("no samples collected", file=sys.stderr)
        return 1

    names = list(TARGETS.keys())
    print("%-8s %14s %14s %14s %14s %14s %14s" % (
        "Time", "Lidar", "OrinA", "OrinB", "A-B", "R-A", "R-B"))
    print("-" * 96)
    for i, s in enumerate(samples):
        lidar, orina, orinb = s["Lidar"], s["OrinA"], s["OrinB"]
        if lidar is None or orina is None or orinb is None:
            print("incomplete sample", s)
            continue
        print("%-8s %14.1f %14.1f %14.1f %14.1f %14.1f %14.1f" % (
            i + 1, lidar, orina, orinb, orina - orinb, lidar - orina, lidar - orinb))

    def col(values):
        vals = [v for v in values if v is not None]
        if not vals:
            return float("nan")
        return statistics.mean(vals)

    lidar = [s["Lidar"] for s in samples if s["Lidar"] is not None]
    orina = [s["OrinA"] for s in samples if s["OrinA"] is not None]
    orinb = [s["OrinB"] for s in samples if s["OrinB"] is not None]
    print("-" * 96)
    print("Avg offsets: Lidar=%.1f ns, OrinA=%.1f ns, OrinB=%.1f ns" % (
        col(lidar), col(orina), col(orinb)))
    if orina and orinb:
        print("Avg OrinA-OrinB=%.1f ns, Lidar-OrinA=%.1f ns, Lidar-OrinB=%.1f ns" % (
            col(orina) - col(orinb), col(lidar) - col(orina), col(lidar) - col(orinb)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
