#!/usr/bin/env python3
"""Deploy IEEE 1588v2 L2 E2E slave to OrinA and OrinB.

The slave config is stored at /etc/1588v2-slave_e2e.cfg on each Orin.
If the file already exists, it is kept. If it is missing, it is created.

Usage:
    python3 scripts/07_deploy_slaves.py
    python3 scripts/07_deploy_slaves.py --host 192.168.1.101
"""

import argparse
import os
import sys
from pathlib import Path

import paramiko

ORIN_A = os.environ.get("ORIN_A_IP", "192.168.1.100")
ORIN_B = os.environ.get("ORIN_B_IP", "192.168.1.101")
USERNAME = os.environ.get("ORIN_USER", "nvidia")
PASSWORD = os.environ.get("ORIN_PASSWORD", "nvidia")
ORIN_IFACE = os.environ.get("ORIN_IFACE", "mgbe3_0")
SLAVE_CONFIG = "/etc/1588v2-slave_e2e.cfg"
PTP_LOG = "/tmp/ptp4l_slave_1588.log"
PHC_LOG = "/tmp/phc2sys_slave_1588.log"

ROOT = Path(__file__).resolve().parent.parent
LOCAL_CONFIG = ROOT / "config" / "slave_1588v2_e2e.cfg"


def connect(host: str):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD, timeout=15,
                   look_for_keys=False, allow_agent=False)
    return client


def run(client, command, timeout=30):
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    stdin.close()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return out, err


def deploy_one(host: str) -> int:
    print("=" * 60)
    print("Deploying slave:", host)
    print("=" * 60)

    client = connect(host)
    try:
        check = "test -f %s && echo CONFIG_EXISTS || echo CONFIG_MISSING" % SLAVE_CONFIG
        out, _ = run(client, check, timeout=15)
        if "CONFIG_EXISTS" in out:
            print("config exists, keep existing:", SLAVE_CONFIG)
        else:
            print("config missing, writing:", SLAVE_CONFIG)
            config_text = LOCAL_CONFIG.read_text(encoding="utf-8")
            stdin, stdout, stderr = client.exec_command(
                "sudo -S -p '' tee %s >/dev/null" % SLAVE_CONFIG, timeout=20)
            stdin.write(b"nvidia\n" + config_text.encode())
            stdin.channel.shutdown_write()
            stdout.read()
            err = stderr.read().decode(errors="replace")
            if err and "password" not in err.lower():
                print("write stderr:", err[:300])

        cmd = r"""echo 'nvidia' | sudo -S -p '' bash -c '
pkill -9 ptp4l 2>/dev/null || true
pkill -9 phc2sys 2>/dev/null || true
sleep 1
nohup "$(command -v ptp4l)" -i %s -f %s -m >%s 2>&1 &
sleep 4
nohup "$(command -v phc2sys)" -s %s -c CLOCK_REALTIME --domainNumber=1 --step_threshold=1 -w -m >%s 2>&1 &
sleep 8
echo ---ps---; ps aux | grep -E "ptp4l|phc2sys" | grep -v grep
echo ---ptp4l---; tail -20 %s
echo ---phc2sys---; tail -10 %s
'""" % (
            ORIN_IFACE, SLAVE_CONFIG, PTP_LOG,
            ORIN_IFACE, PHC_LOG, PTP_LOG, PHC_LOG
        )
        out, err = run(client, cmd, timeout=45)
        print(out)
        if err.strip():
            print("stderr:", err[:500])
        return 0
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy 1588v2 L2 E2E slave to OrinA/B")
    parser.add_argument("--host", default=None, help="deploy to only one host")
    args = parser.parse_args()

    hosts = [args.host] if args.host else [ORIN_A, ORIN_B]
    rc = 0
    for host in hosts:
        rc = max(rc, deploy_one(host))
    return rc


if __name__ == "__main__":
    sys.exit(main())
