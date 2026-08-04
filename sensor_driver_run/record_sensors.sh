#!/bin/bash
# Record lidar + camera topics.
# Usage:
#   bash record_sensors.sh six [duration]
#   bash record_sensors.sh one [duration]

export ROS_LOCALHOST_ONLY=1
source /opt/ros/foxy/setup.bash
source /mnt/ufs_data/workspace/sensor_configure/hesai_ws/install/setup.bash
source /mnt/ufs_data/workspace/sensor_configure/camera_ros2/install/setup.bash

MODE="${1:-six}"
DURATION="${2:-0}"
RECORD_DIR="${RECORD_DIR:-/mnt/ufs_data/workspace/rosbag_storage}"

if [ "$MODE" = "one" ]; then
  TOPICS=(
    /lidar_points
    /camera/cam_0/CameraDeviceGroupA_0/jpeg
  )
elif [ "$MODE" = "six" ]; then
  TOPICS=(
    /lidar_points
    /camera/cam_0/CameraDeviceGroupA_0/jpeg
    /camera/cam_1/CameraDeviceGroupA_1/jpeg
    /camera/cam_2/CameraDeviceGroupA_2/jpeg
    /camera/cam_3/CameraDeviceGroupB_0/jpeg
    /camera/cam_4/CameraDeviceGroupB_1/jpeg
    /camera/cam_5/CameraDeviceGroupB_2/jpeg
  )
else
  echo "Usage: bash record_sensors.sh [one|six] [duration_seconds]"
  exit 1
fi

mkdir -p "$RECORD_DIR"
OUTPUT="$RECORD_DIR/${MODE}_sensor_bag_$(date +%Y%m%d_%H%M%S)"

if [ "$DURATION" -gt 0 ]; then
  timeout -s INT "$DURATION" ros2 bag record -o "$OUTPUT" "${TOPICS[@]}"
else
  ros2 bag record -o "$OUTPUT" "${TOPICS[@]}"
fi
sleep 2
echo "BAG_PATH=$OUTPUT"
ros2 bag info "$OUTPUT"
