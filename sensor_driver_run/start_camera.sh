#!/bin/bash
# Start pony_camera ROS2 driver.
# Usage:
#   bash start_camera.sh one    # 1 camera test config
#   bash start_camera.sh six    # 6 camera production config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-one}"

CAMERA_CONFIG_BASE="/mnt/ufs_data/workspace/sensor_configure/camera_ros2/config"
case "$MODE" in
  one|1)
    CAMERA_CONFIG_DIR="$CAMERA_CONFIG_BASE/test_one_camera"
    EXPECTED_TOPIC="/camera/cam_0/CameraDeviceGroupA_0/jpeg"
    ;;
  six|6)
    CAMERA_CONFIG_DIR="$CAMERA_CONFIG_BASE"
    EXPECTED_TOPIC="/camera/cam_0/CameraDeviceGroupA_0/jpeg"
    ;;
  *)
    echo "Usage: bash start_camera.sh [one|six]"
    exit 1
    ;;
esac

unset ROS_LOCALHOST_ONLY
source /opt/ros/foxy/setup.bash
source /mnt/ufs_data/workspace/sensor_configure/camera_ros2/install/setup.bash

pkill -9 -f 'pony_camera_nod[e]' 2>/dev/null
sleep 1

setsid ros2 launch pony_camera pony_camera.launch.py \
  camera_config_file:="$CAMERA_CONFIG_DIR/camera.config" \
  nvmedia_camera_config_file:="$CAMERA_CONFIG_DIR/nvmedia_camera.config" \
  enable_undistortion:=false < /dev/null >/tmp/camera_driver_${MODE}.log 2>&1 &

sleep 10
echo "--- camera topics ($MODE) ---"
timeout 10 ros2 topic list | grep camera
echo "--- camera hz ---"
timeout -s INT 7 ros2 topic hz "$EXPECTED_TOPIC" 2>&1 | tail -5
echo "--- camera log ---"
tail -20 "/tmp/camera_driver_${MODE}.log"
