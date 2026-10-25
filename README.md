# network-core

Shared **network operations** library for the ops platform.

Profile map: https://github.com/drycov#-ops-platform-ecosystem

## Install

```bash
pip install "network-core @ https://github.com/drycov/network-core/archive/main.zip"
```

## Modules

| Module | Purpose |
| --- | --- |
| `network_core.mikrotik` | RouterOS API read + subnet candidate discovery |
| `network_core.ssh` | Read-only Cisco / Junos / Huawei version facts |
| `network_core.vendor_identity` | Normalize manufacturer names |
| `network_core.geo` | Haversine distance in meters |

## Non-goals

- Camera / ONVIF probing → [`camera-probe`](https://github.com/drycov/camera-probe)
- Cerebro HTTP client → [`cerebro-client`](https://github.com/drycov/cerebro-client)
- Product UI / inventory DB

## Consumers

Intended: `equipment-bot`, `backup_tool`, `cmdb` (MikroTik paths).
