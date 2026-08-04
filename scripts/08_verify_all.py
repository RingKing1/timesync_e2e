#!/usr/bin/env python3
"""Verify IEEE 1588v2 L2 E2E time sync for Host, Lidar, OrinA, and OrinB.

Paths inside this repository are relative to the script location. Remote Orin
status is checked with pmc and the phc2sys log under /tmp.

Usage:
    python3 scripts/08_verify_all.py
    python3 scripts/08_verify_all.py --iface eth1
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import paramiko

LIDAR_IP = os.environ.get("LIDAR_IP", "192.168.1.201")
ORIN_A = os.environ.get("ORIN_A_IP", "192.168.1.100")
ORIN_B = os.environ.get("ORIN_B_IP", "192.168.1.101")
USERNAME = os.environ.get("ORIN_USER", "nvidia")
PASSWORD = os.environ.get("ORIN_PASSWORD", "nvidia")
ORIN_IFACE = os.environ.get("ORIN_IFACE", "mgbe3_0")
ORIN_CONFIG = "/etc/1588v2-slave_e2e.cfg"

ROOT = Path(__file__).resolve().parent.parent
LOCAL_LOG_DIR = ROOT / "logs"


def tail_local(name):
    path = LOCAL_LOG_DIR / name
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def local_ptp4l(iface):
    try:
        out = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return False, "cannot read ps"
    lines = [l for l in out.splitlines() if "ptp4l" in l and "grep" not in l and iface in l]
    if not lines:
        return False, "no ptp4l process for %s" % iface
    text = tail_local("ptp4l_1588_e2e.log")
    if text and ("assuming the grand master role" in text or "LISTENING to MASTER" in text):
        return True, "log: logs/ptp4l_1588_e2e.log"
    return True, "process running, log not verified"


def local_phc2sys():
    try:
        out = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return False, "cannot read ps"
    lines = [l for l in out.splitlines() if "phc2sys" in l and "grep" not in l]
    if not lines:
        return False, "no phc2sys process"
    text = tail_local("phc2sys_1588_e2e.log")
    if text and " s2 " in text:
        return True, "log: logs/phc2sys_1588_e2e.log"
    return True, "process running, s2 not verified"


def check_lidar():
    try:
        body = json.loads(urllib.request.urlopen(
            "http://%s/pandar.cgi?action=get&object=lidar_config" % LIDAR_IP,
            timeout=5).read().decode()).get("Body", {})
    except Exception as exc:
        return False, "lidar web error: %s" % exc
    status = body.get("PTPStatus", "")
    profile = body.get("PTPProfile", "")
    cfg = body.get("PTPConfig", "")
    ok = status.startswith("Locked") and profile == "0" and '"Domain":1' in cfg and '"Network":1' in cfg
    return ok, "PTPStatus=%s Profile=%s PTPConfig=%s" % (status, profile, cfg)


def remote_status(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=USERNAME, password=PASSWORD, timeout=15,
                       look_for_keys=False, allow_agent=False)
        cmd = r"""MAC=$(ip link show %s | awk '/ether/{print $2; exit}')
ID=$(echo "$MAC" | awk -F: '{printf "%%s%%s%%s.fffe.%%s%%s%%s", $1,$2,$3,$4,$5,$6}')
PMC=$(echo 'nvidia' | sudo -S -p '' pmc -u -b 1 -f %s 'GET PORT_DATA_SET' 2>&1)
if echo "$PMC" | grep -A1 "$ID" | grep -q 'portState               SLAVE'; then
  echo PTP_SLAVE_OK
else
  echo PTP_SLAVE_FAIL
fi
if tail -30 /tmp/phc2sys_slave_1588.log 2>/dev/null | grep -q ' s2 '; then
  echo PHC_S2_OK
else
  echo PHC_S2_FAIL
fi
echo ---ps---; ps aux | grep -E "ptp4l|phc2sys" | grep -v grep""" % (ORIN_IFACE, ORIN_CONFIG)
        _in, out, err = client.exec_command(cmd, timeout=25)
        _in.close()
        text = out.read().decode(errors="replace")
        err_text = err.read().decode(errors="replace")
        return text, err_text
    except Exception as exc:
        return "", "ssh error: %s" % exc
    finally:
        client.close()


def check_remote(host):
    text, err = remote_status(host)
    if err:
        return False, err
    ptp_ok = "PTP_SLAVE_OK" in text
    phc_ok = "PHC_S2_OK" in text
    detail = text.replace("\n", " | ")[:220]
    return ptp_ok and phc_ok, detail


def main():
    parser = argparse.ArgumentParser(description="Verify 1588v2 L2 E2E time sync")
    parser.add_argument("--iface", default=os.environ.get("MASTER_IFACE", "enp5s0"))
    args = parser.parse_args()

    checks = []
    checks.append(("Host ptp4l", local_ptp4l(args.iface)))
    checks.append(("Host phc2sys", local_phc2sys()))
    checks.append(("Lidar", check_lidar()))
    checks.append(("OrinA", check_remote(ORIN_A)))
    checks.append(("OrinB", check_remote(ORIN_B)))

    all_ok = True
    print("%-16s %-6s %s" % ("Check", "Result", "Detail"))
    print("-" * 80)
    for name, (ok, detail) in checks:
        all_ok &= ok
        print("%-16s %-6s %s" % (name, "PASS" if ok else "FAIL", detail))
    print("-" * 80)
    print("Overall:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
