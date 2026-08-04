# Lidar Setup

Use:
```bash
python3 scripts/06_configure_lidar.py
```

Expected:
```text
PTPProfile=0
PTPConfig={"Domain":1,"Network":1,...}
PTPStatus=Locked
```

If Free Run or Frozen:
```bash
python3 scripts/06_configure_lidar.py --reboot
```
