#!/usr/bin/env python3
"""Run sensor driver commands from PC on remote OrinA.

This script uploads the required shell scripts to:
    /mnt/ufs_data/workspace/timesync_e2e/sensor_driver_run

Then executes the requested command over SSH.

Usage:
    python3 run_sensors.py lidar
    python3 run_sensors.py camera one
    python3 run_sensors.py camera six
    python3 run_sensors.py stop
    python3 run_sensors.py record one 30
    python3 run_sensors.py record six 30
"""

import argparse
import re
import shlex
import stat
import sys
from pathlib import Path

import paramiko

ORIN_A = "192.168.1.100"
USERNAME = "nvidia"
PASSWORD = "nvidia"
REMOTE_DIR = "/mnt/ufs_data/workspace/timesync_e2e/sensor_driver_run"
REMOTE_CONFIG_BASE = "/mnt/ufs_data/workspace/sensor_configure/camera_ros2/config"

LOCAL_DIR = Path(__file__).resolve().parent
LOCAL_REPO = LOCAL_DIR.parent
LOCAL_BAG_DIR = LOCAL_REPO / "rosbag_storage"
UPLOAD_FILES = [
    "start_camera.sh",
    "start_lidar.sh",
    "stop_sensors.sh",
    "record_sensors.sh",
    "README.md",
]


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ORIN_A, username=USERNAME, password=PASSWORD, timeout=20,
                   look_for_keys=False, allow_agent=False)
    return client


def run(client, command, timeout=120):
    _in, out, err = client.exec_command(command, timeout=timeout)
    _in.close()
    out_text = out.read().decode(errors="replace")
    err_text = err.read().decode(errors="replace")
    rc = out.channel.recv_exit_status()
    return rc, out_text, err_text


def remote_files_ready(client):
    check_cmd = (
        "if [ -d %s ]; then ready=1; "
        "for f in %s; do [ -f %s/$f ] || ready=0; done; "
        "[ \"$ready\" = 1 ] && echo READY || echo NEED_UPLOAD; "
        "else echo NEED_UPLOAD; fi"
    ) % (REMOTE_DIR, " ".join(UPLOAD_FILES), REMOTE_DIR)
    _in, out, err = client.exec_command(check_cmd, timeout=20)
    _in.close()
    result = out.read().decode(errors="replace")
    err.read()
    return "READY" in result


def upload_scripts(client, force=False):
    if not force and remote_files_ready(client):
        print("remote files already exist, skip upload")
        return

    _in, out, err = client.exec_command("mkdir -p %s" % REMOTE_DIR, timeout=20)
    _in.close()
    out.read()
    err.read()

    sftp = client.open_sftp()
    try:
        for name in UPLOAD_FILES:
            local_path = LOCAL_DIR / name
            if not local_path.exists():
                print("WARNING: local file missing, skip:", name)
                continue
            sftp.put(str(local_path), "%s/%s" % (REMOTE_DIR, name))
            print("uploaded", name)
    finally:
        sftp.close()


def remote_command(script, args=()):
    parts = ["bash", script] + list(args)
    return "cd %s && %s" % (REMOTE_DIR, " ".join(parts))


def sftp_download_dir(sftp, remote_dir, local_dir):
    local_dir.mkdir(parents=True, exist_ok=True)
    for attr in sftp.listdir_attr(remote_dir):
        remote_child = remote_dir + "/" + attr.filename
        local_child = local_dir / attr.filename
        if stat.S_ISDIR(attr.st_mode):
            sftp_download_dir(sftp, remote_child, local_child)
        else:
            sftp.get(remote_child, str(local_child))


def download_and_remove_remote_bag(client, remote_bag):
    local_bag = LOCAL_BAG_DIR / Path(remote_bag).name
    LOCAL_BAG_DIR.mkdir(parents=True, exist_ok=True)
    print("downloading bag to", local_bag)
    sftp = client.open_sftp()
    try:
        sftp_download_dir(sftp, remote_bag, local_bag)
    finally:
        sftp.close()
    print("downloaded bag")
    run(client, "rm -rf %s" % shlex.quote(remote_bag), timeout=120)
    print("removed remote bag", remote_bag)


def main():
    parser = argparse.ArgumentParser(description="Run sensor drivers on remote OrinA from PC")
    parser.add_argument("--force-upload", action="store_true",
                        help="force upload even if remote files already exist")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("lidar", help="start lidar driver")

    camera = sub.add_parser("camera", help="start camera driver")
    camera.add_argument("mode", choices=["one", "six"], default="six", nargs="?",
                        help="one=1 camera test, six=6 camera production")

    sub.add_parser("stop", help="stop camera and lidar drivers")

    record = sub.add_parser("record", help="record sensor topics")
    record.add_argument("mode", choices=["one", "six"], default="six", nargs="?")
    record.add_argument("duration", type=int, default=0, nargs="?",
                        help="duration in seconds, 0 means run until Ctrl+C")

    args = parser.parse_args()

    client = connect()
    try:
        upload_scripts(client, force=args.force_upload)

        if args.command == "lidar":
            cmd = remote_command("start_lidar.sh")
        elif args.command == "camera":
            cmd = remote_command("start_camera.sh", [args.mode])
        elif args.command == "stop":
            cmd = remote_command("stop_sensors.sh")
        elif args.command == "record":
            cmd = remote_command("record_sensors.sh", [args.mode, str(args.duration)])
        else:
            parser.error("unknown command")

        rc, out_text, err_text = run(client, cmd, timeout=180)
        print(out_text[-6000:])
        if err_text.strip():
            print("--- stderr tail ---")
            print(err_text[-2000:])

        if args.command == "record" and rc == 0:
            match = re.search(r"BAG_PATH=(\S+)", out_text)
            if match:
                remote_bag = match.group(1)
                try:
                    download_and_remove_remote_bag(client, remote_bag)
                except Exception as exc:
                    print("download failed, remote bag kept:", exc)
                    return 1
        return rc
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
