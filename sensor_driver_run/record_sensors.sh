#!/bin/bash
# Record lidar + camera topics.
# Usage:
#   bash record_sensors.sh six [duration]
#   bash record_sensors.sh one [duration]

unset ROS_LOCALHOST_ONLY
source /opt/ros/foxy/setup.bash
source /mnt/ufs_data/workspace/sensor_configure/hesai_ws/install/setup.bash
source /mnt/ufs_data/workspace/sensor_configure/camera_ros2/install/setup.bash
if [ -f /mnt/ufs_data/workspace/ptp_pps_time_synchroize_ws/install/setup.bash ]; then
  source /mnt/ufs_data/workspace/ptp_pps_time_synchroize_ws/install/setup.bash
fi

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
    /localization/kinematicstate
    /beidou/navsatfix
    /beidou/inspva
    /beidou/corrimudata
  )
else
  echo "Usage: bash record_sensors.sh [one|six] [duration_seconds]"
  exit 1
fi

mkdir -p "$RECORD_DIR"
OUTPUT="$RECORD_DIR/${MODE}_sensor_bag_$(date +%Y%m%d_%H%M%S)"
PID_FILE="/tmp/rosbag_record.pid"
BAG_FILE="/tmp/rosbag_record_bag.txt"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "active recording exists, stopping it first"
  kill -INT "$(cat "$PID_FILE")"
  sleep 2
fi
rm -f "$PID_FILE" "$BAG_FILE"

if [ "$DURATION" -gt 0 ]; then
  timeout -s INT "$DURATION" ros2 bag record -o "$OUTPUT" "${TOPICS[@]}"
  sleep 2
  echo "BAG_PATH=$OUTPUT"
  ros2 bag info "$OUTPUT"
else
  setsid ros2 bag record -o "$OUTPUT" "${TOPICS[@]}" \
    < /dev/null >/tmp/rosbag_record.log 2>&1 &
  REC_PID=$!
  echo "$REC_PID" > "$PID_FILE"
  echo "$OUTPUT" > "$BAG_FILE"
  echo "RECORD_PID=$REC_PID"
  echo "BAG_PATH=$OUTPUT"
  echo "recording started in background, use run_sensors.py stop to stop"
fi
