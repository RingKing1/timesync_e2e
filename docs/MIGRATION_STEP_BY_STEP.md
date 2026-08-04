# Migration Step by Step

1. Back up the old time-sync files.
2. Copy `timesync_e2e` to the new time master.
3. Edit `config/network.env`:
   - `MASTER_IFACE=enp5s0`
   - `MASTER_IP=192.168.1.1`
4. Run `bash scripts/01_check_network.sh`.
5. Run `bash scripts/02_install_linuxptp.sh`.
6. Run `bash scripts/03_setup_master.sh`.
7. Stop the old master before starting the new one.
8. Run `bash scripts/04_start_master.sh`.
9. Wait for ptp4l `assuming the grand master role`.
10. Run `python3 scripts/06_configure_lidar.py`.
11. Reboot lidar if PTPStatus is Free Run or Frozen.
12. Run `python3 scripts/07_deploy_slaves.py`.
13. Wait for OrinA/B `SLAVE` and phc2sys `s2`.
14. Run `bash scripts/08_verify_all.sh`.
15. Run `python3 scripts/09_measure_offsets.py --seconds 5` to inspect residuals.
