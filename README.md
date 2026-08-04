# IEEE 1588v2 L2 E2E 时间同步迁移包

本目录用于将授时主机从旧机器迁移到新机器，并为以下设备统一授时：

- 授时主机：IEEE 1588v2 L2 E2E Grand Master
- Pandar64 Lidar：1588v2 L2 E2E Slave
- OrinA：1588v2 L2 E2E Slave
- OrinB：1588v2 L2 E2E Slave

## 目录结构

```text
timesync_e2e/
├── README.md
├── config/
│   ├── master_1588v2_e2e.cfg
│   ├── slave_1588v2_e2e.cfg
│   └── network.env
├── scripts/
│   ├── 01_check_network.sh
│   ├── 02_install_linuxptp.sh
│   ├── 03_setup_master.sh
│   ├── 04_start_master.sh
│   ├── 05_stop_master.sh
│   ├── 06_configure_lidar.py
│   ├── 07_deploy_slaves.py
│   ├── 08_verify_all.py
│   ├── 08_verify_all.sh
│   ├── 09_measure_offsets.py
│   └── 10_cleanup.sh
├── docs/
│   ├── LIDAR_SETUP.md
│   ├── MASTER_SETUP.md
│   ├── MIGRATION_STEP_BY_STEP.md
│   └── SLAVE_SETUP.md
└── logs/
    └── .gitkeep
```

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `config/network.env` | 统一配置：主机网口、主机 IP、PTP Domain、Lidar IP、OrinA/B IP |
| `config/master_1588v2_e2e.cfg` | 主机 ptp4l master 配置 |
| `config/slave_1588v2_e2e.cfg` | OrinA/B ptp4l slave 配置 |
| `scripts/01_check_network.sh` | 检查主机网口和硬件时间戳 |
| `scripts/02_install_linuxptp.sh` | 安装 linuxptp |
| `scripts/03_setup_master.sh` | 设置主机静态 IP，默认 192.168.1.1/24 |
| `scripts/04_start_master.sh` | 启动主机 ptp4l 和 phc2sys |
| `scripts/05_stop_master.sh` | 停止主机 ptp4l 和 phc2sys |
| `scripts/06_configure_lidar.py` | 配置 Lidar 为 1588v2 L2 E2E |
| `scripts/07_deploy_slaves.py` | 一键部署 OrinA/B slave |
| `scripts/08_verify_all.sh` | 一键检查主机、Lidar、OrinA/B 是否授时成功 |
| `scripts/08_verify_all.py` | `08_verify_all.sh` 实际调用的检查实现 |
| `scripts/09_measure_offsets.py` | 抓取几秒采样各设备 offset 并计算差值 |
| `scripts/10_cleanup.sh` | 清理测试进程和本地日志 |
| `logs/` | 运行日志目录，默认保存 ptp4l、phc2sys 输出 |

## 网络环境

正常情况只需要修改 `config/network.env` 中的：

```bash
MASTER_IFACE=enp5s0
MASTER_IP=192.168.1.1
MASTER_PREFIX=24
```

Lidar、OrinA、OrinB 的 IP 已固定，不需要修改：

```bash
LIDAR_IP=192.168.1.201
ORIN_A_IP=192.168.1.100
ORIN_B_IP=192.168.1.101
ORIN_IFACE=mgbe3_0
```

## 快速开始

### 1. 检查主机网络

```bash
bash scripts/01_check_network.sh
```

预期结果：

```text
Hardware timestamping: OK
```

如果网口名不是 `enp5s0`，先修改 `config/network.env` 中的 `MASTER_IFACE`。

### 2. 安装 linuxptp

```bash
bash scripts/02_install_linuxptp.sh
```

需要确认 `ptp4l`、`phc2sys`、`pmc` 三个命令可用。

### 3. 设置主机 IP

```bash
bash scripts/03_setup_master.sh
```

该脚本会临时设置：

```text
192.168.1.1/24
```

如需永久生效，后续还需要使用 netplan 或 NetworkManager 保存配置。

### 4. 启动授时主机

```bash
bash scripts/04_start_master.sh
```

等价于启动：

```bash
ptp4l -i enp5s0 -f config/master_1588v2_e2e.cfg -m
phc2sys -s CLOCK_REALTIME -c enp5s0 --domainNumber=1 --step_threshold=1 -w -m
```

预期日志：

```text
LISTENING to MASTER
assuming the grand master role
```

### 5. 配置 Lidar

```bash
python3 scripts/06_configure_lidar.py
```

Lidar 应配置为：

```text
PTPProfile=0
Domain=1
Network=L2
ClockSource=PTP
```

如果状态是 `Free Run` 或 `Frozen`：

```bash
python3 scripts/06_configure_lidar.py --reboot
```

### 6. 部署 OrinA/B

```bash
python3 scripts/07_deploy_slaves.py
```

脚本会检查远程 Orin 上是否存在 `/etc/1588v2-slave_e2e.cfg`：

- 存在：保留现有文件
- 不存在：写入 `config/slave_1588v2_e2e.cfg`

然后自动启动：

```bash
ptp4l -i mgbe3_0 -f /etc/1588v2-slave_e2e.cfg -m
phc2sys -s mgbe3_0 -c CLOCK_REALTIME --domainNumber=1 --step_threshold=1 -w -m
```

### 7. 一键检查

```bash
bash scripts/08_verify_all.sh
```

检查项：

- Host ptp4l
- Host phc2sys
- Lidar PTPStatus
- OrinA ptp4l / phc2sys
- OrinB ptp4l / phc2sys

全部正常时：

```text
Overall: PASS
```

### 8. 分析授时差值

```bash
python3 scripts/09_measure_offsets.py --seconds 5
```

输出每台设备的 `offsetFromMaster`，并计算：

- OrinA - OrinB
- Lidar - OrinA
- Lidar - OrinB

### 9. 停止与清理

```bash
bash scripts/05_stop_master.sh
bash scripts/10_cleanup.sh
```

## 迁移注意事项

1. 新老授时主机不能同时作为 Grand Master。
2. 切换顺序：
   - 新主机准备好 IP、配置、linuxptp
   - 停掉旧授时主机
   - 新主机启动 master
   - Lidar 配置并锁定
   - OrinA/B slave 配置并锁定
3. `phc2sys -w` 必须带 `--domainNumber=1`，否则会一直 `Waiting for ptp4l...`。
4. 当前方案使用 `1588v2 L2 E2E`，不要给 master 或 slave 加 gPTP 的 `--transportSpecific=1`。
5. 远程 Orin 使用 `/etc/1588v2-slave_e2e.cfg` 是允许的；部署脚本会先判断文件是否存在。

## 常见问题

### phc2sys 一直 Waiting for ptp4l

原因：`phc2sys -w` 默认等 Domain 0，但当前 ptp4l 使用 Domain 1。

解决：

```bash
phc2sys -s CLOCK_REALTIME -c enp5s0 --domainNumber=1 --step_threshold=1 -w -m
```

### Lidar 一直 Free Run 或 Frozen

检查 Lidar 配置：

```text
PTPProfile=0
Domain=1
Network=L2
```

然后重启 Lidar：

```bash
python3 scripts/06_configure_lidar.py --reboot
```

### ptp4l 报 rogue peer delay response

当前方案是 E2E，不要使用 P2P 或 gPTP 配置。确认 master 和 slave 都使用：

```text
delay_mechanism=E2E
ptp_dst_mac=01:1B:19:00:00:00
transportSpecific=0
domainNumber=1
```

## 验证标准

| 设备 | 要求 |
| --- | --- |
| Host ptp4l | `assuming the grand master role` |
| Host phc2sys | `s2` |
| Lidar | `PTPStatus=Locked`，`PTPProfile=0`，`Domain=1`，`Network=L2` |
| OrinA | ptp4l `SLAVE`，phc2sys `s2` |
| OrinB | ptp4l `SLAVE`，phc2sys `s2` |
