#!/bin/bash
# Start Hesai lidar ROS2 driver.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

unset ROS_LOCALHOST_ONLY
source /opt/ros/foxy/setup.bash
source /mnt/ufs_data/workspace/sensor_configure/hesai_ws/install/setup.bash

pkill -9 -f 'hesai_ros_driver_nod[e]' 2>/dev/null
sleep 1

setsid ros2 launch hesai_ros_driver start.py < /dev/null >/tmp/lidar_driver.log 2>&1 &

sleep 10
echo '--- lidar topics ---'
timeout 10 ros2 topic list | grep lidar
echo '--- lidar hz ---'
timeout -s INT 7 ros2 topic hz /lidar_points 2>&1 | tail -5
echo '--- lidar log ---'
tail -20 /tmp/lidar_driver.log
