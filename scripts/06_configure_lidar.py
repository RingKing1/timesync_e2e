#!/usr/bin/env python3
"""Configure Pandar64 for IEEE 1588v2 L2 E2E time sync.

Usage:
    python3 scripts/06_configure_lidar.py
    python3 scripts/06_configure_lidar.py --reboot
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

LIDAR_IP = os.environ.get("LIDAR_IP", "192.168.1.201")
BASE = "http://" + LIDAR_IP


def api_get(endpoint, timeout=10):
    return json.loads(urllib.request.urlopen(endpoint, timeout=timeout).read().decode())


def api_set(object_param, key, value, timeout=10):
    url = BASE + "/pandar.cgi?action=set&object=%s&key=%s&value=%s" % (
        object_param, key, urllib.parse.quote(str(value)))
    return json.loads(urllib.request.urlopen(url, timeout=timeout).read().decode())


def set_ptp_config(profile, domain, network, announce_interval, sync_interval, min_delay_interval):
    config = json.dumps({
        "Profile": profile,
        "Domain": domain,
        "Network": network,
        "LogAnnounceInterval": announce_interval,
        "LogSyncInterval": sync_interval,
        "LogMinDelayReqInterval": min_delay_interval,
    })
    return api_set("lidar", "ptp_configuration", config)


def main():
    parser = argparse.ArgumentParser(description="Configure lidar for 1588v2 L2 E2E")
    parser.add_argument("--reboot", action="store_true", help="reboot lidar after config")
    args = parser.parse_args()

    print("Configure lidar:", LIDAR_IP)
    print("set_ptp:", set_ptp_config(
        profile=0, domain=1, network=1,
        announce_interval=0, sync_interval=-3, min_delay_interval=0))
    print("clock_source:", api_set("lidar", "clock_source", 1))

    if args.reboot:
        print("reboot:", api_get(BASE + "/pandar.cgi?action=set&object=reboot"))
        time.sleep(2)

    body = api_get(BASE + "/pandar.cgi?action=get&object=lidar_config").get("Body", {})
    print("PTPStatus=", body.get("PTPStatus"))
    print("PTPProfile=", body.get("PTPProfile"))
    print("PTPConfig=", body.get("PTPConfig"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
