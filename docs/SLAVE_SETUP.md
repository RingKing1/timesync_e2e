# OrinA/B Slave Setup

Use:
```bash
python3 scripts/07_deploy_slaves.py
```

The script checks `/etc/1588v2-slave_e2e.cfg`:
- If the file exists, it keeps it.
- If the file is missing, it writes it from `config/slave_1588v2_e2e.cfg`.

Expected on each Orin:
```text
UNCALIBRATED to SLAVE
phc2sys ... s2
```

Verify:
```bash
bash scripts/08_verify_all.sh
```
