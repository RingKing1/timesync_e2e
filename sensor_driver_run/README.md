# Sensor Driver Run

用于在远程 OrinA 上启动相机驱动、雷达驱动，并录制数据集。

本目录位于：

```text
timesync_e2e/sensor_driver_run/
```

## 目录结构

```text
sensor_driver_run/
├── README.md
├── start_camera.sh     # 支持单相机 / 6 相机
├── start_lidar.sh      # 启动雷达
├── stop_sensors.sh     # 停止相机和雷达
└── record_sensors.sh   # 录制
```

相机 config 不复制到本目录，直接使用 OrinA 上已有的远程配置：

```text
/mnt/ufs_data/workspace/sensor_configure/camera_ros2/config/
├── camera.config                    # 6 相机生产配置
├── nvmedia_camera.config
└── test_one_camera/
    ├── camera.config                # 单相机测试配置
    └── nvmedia_camera.config
```

## 远程执行前提

在 OrinA 上假设本目录位于：

```text
/mnt/ufs_data/workspace/timesync_e2e/sensor_driver_run
```

如果还没上传，先把 `timesync_e2e/sensor_driver_run` 放到 OrinA 对应路径。

## 启动雷达

```bash
cd /mnt/ufs_data/workspace/timesync_e2e/sensor_driver_run
bash start_lidar.sh
```

话题：

```text
/lidar_points
/lidar_imu
/lidar_ptp
/lidar_packets_loss
```

## 单相机测试

```bash
bash start_camera.sh one
```

使用的远程配置：

```text
/mnt/ufs_data/workspace/sensor_configure/camera_ros2/config/test_one_camera/
```

预期话题：

```text
/camera/cam_0/CameraDeviceGroupA_0/jpeg
```

## 6 相机测试

```bash
bash start_camera.sh six
```

使用的远程配置：

```text
/mnt/ufs_data/workspace/sensor_configure/camera_ros2/config/
```

预期话题：

```text
/camera/cam_0/CameraDeviceGroupA_0/jpeg
/camera/cam_1/CameraDeviceGroupA_1/jpeg
/camera/cam_2/CameraDeviceGroupA_2/jpeg
/camera/cam_3/CameraDeviceGroupB_0/jpeg
/camera/cam_4/CameraDeviceGroupB_1/jpeg
/camera/cam_5/CameraDeviceGroupB_2/jpeg
```

## 从 PC 一键执行

本目录提供 `run_sensors.py`，脚本会自动把需要的文件上传到 OrinA：

```text
/mnt/ufs_data/workspace/timesync_e2e/sensor_driver_run/
```

然后远程执行命令，不需要手动在 OrinA 上建目录或复制文件。

如果远程目录和脚本已经存在，`run_sensors.py` 会跳过重复上传；需要强制覆盖时加 `--force-upload`。

```bash
# 启动雷达
python3 run_sensors.py lidar

# 单相机测试
python3 run_sensors.py camera one

# 6 相机测试
python3 run_sensors.py camera six

# 停止相机和雷达
python3 run_sensors.py stop

# 录制 30 秒
python3 run_sensors.py record six 30
```

## 录制话题

录制时默认包含以下话题：

one 模式：

```text
/lidar_points
/camera/cam_0/CameraDeviceGroupA_0/jpeg
```

six 模式：

```text
/lidar_points
/camera/cam_0/CameraDeviceGroupA_0/jpeg
/camera/cam_1/CameraDeviceGroupA_1/jpeg
/camera/cam_2/CameraDeviceGroupA_2/jpeg
/camera/cam_3/CameraDeviceGroupB_0/jpeg
/camera/cam_4/CameraDeviceGroupB_1/jpeg
/camera/cam_5/CameraDeviceGroupB_2/jpeg
```

## 录制

推荐从 PC 使用 `run_sensors.py` 录制，录制完成后会自动：

1. 把 rosbag 下载到本地：
   ```text
   timesync_e2e/rosbag_storage/
   ```
2. 删除 OrinA 上对应的源 bag

单相机录制 30 秒：

```bash
python3 run_sensors.py record one 30
```

6 相机模式录制 30 秒：

```bash
python3 run_sensors.py record six 30
```

不带时间则一直录制：

```bash
python3 run_sensors.py record six
```

如果直接在 OrinA 上运行 `record_sensors.sh`，bag 会保留在远程 `rosbag_storage`，不会自动回传或删除。

## 停止

```bash
bash stop_sensors.sh
```

## 预期频率

- Lidar: 约 10 Hz
- Camera: 每路约 10 Hz
