#!/bin/bash
# Stop camera and lidar ROS2 driver nodes.
pkill -9 -f 'pony_camera_nod[e]' 2>/dev/null
pkill -9 -f 'hesai_ros_driver_nod[e]' 2>/dev/null
sleep 1
ps aux | grep -E 'pony_camera|hesai_ros_driver' | grep -v grep || echo 'sensor drivers stopped'
