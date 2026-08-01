# CheckMK SMSEagle

CheckMK SNMP monitoring plugin for the [SMSEagle](https://www.smseagle.eu/) SMS gateway, including the NXS-9700 4G/5G single-modem platform.

## Checks

| Check name | Service name | Description |
|---|---|---|
| `smseagle_gsm` | `SMSEagle GSM Modem <N>` | GSM modem state, SIM status, signal strength, network name |
| `smseagle_sms_count` | `SMSEagle SMS Counters Modem <N>` | Incoming and outgoing SMS counters with performance graphs |
| `smseagle_environment` | `SMSEagle <sensor>` | Temperature (°C) and humidity (%) from optional sensors |
| `smseagle_folders` | `SMSEagle Folders` | Device-wide message folder statistics (inbox, outbox, sent, errors) |

## How it works

The SMSEagle exposes its extended properties via the NET-SNMP EXTEND-MIB
(`OID: .1.3.6.1.4.1.8072.1.3.2.3.1.2`). Each leaf OID encodes its own name
as a length-prefixed ASCII byte sequence in the OID index, e.g.:

```
.1.3.6.1.4.1.8072.1.3.2.3.1.2.10.83.73.77.95.83.116.97.116.101.49  →  SIM_State1 = READY
.1.3.6.1.4.1.8072.1.3.2.3.1.2.11.71.83.77.95.83.105.103.110.97.108.49  →  GSM_Signal1 = 72
```

The plugin decodes these OID names automatically and builds a key/value map
used by all four checks.

## Variables monitored

### Per-modem (N = modem index)

| Variable | Example | Description |
|---|---|---|
| `GSM_ModemState1/2` | `on` | Modem power state |
| `SIM_State1/2` | `READY` | SIM card state |
| `SIM_RegState1/2` | `Registered Home` | Network registration state |
| `GSM_Signal1/2` | `72` | Signal strength (%) |
| `GSM_NetName1/2` | `KPN KPN` | Network operator name |
| `SMSCountIn1/2` | `0` | Cumulative incoming SMS count |
| `SMSCountOut1/2` | `0` | Cumulative outgoing SMS count |

### Device-wide

| Variable | Example | Description |
|---|---|---|
| `FolderInbox_Total` | `3` | Total messages currently in inbox |
| `FolderOutbox_Total` | `0` | Total messages currently queued in outbox |
| `FolderSent_Last24H` | `42` | Messages successfully sent in the last 24 hours |
| `FolderSent_Last24HSendErr` | `0` | Messages that failed to send in the last 24 hours |
| `FolderSent_Last1M` | `1247` | Messages successfully sent in the last calendar month |
| `Temp` / `Temp1-4` | `21.5` | Temperature in °C (optional sensor) |
| `Humidity` | `55.0` | Relative humidity % (optional sensor) |

### NXS-9700 4G/5G sensor mapping

For the single-modem NXS-9700 the currently available SNMP sensors map as follows:

| Variable | Sensor |
|---|---|
| `GSM_NetName1` | Modem #1 network name |
| `GSM_Signal1` | Modem #1 signal strength |
| `Humidity` | Internal humidity |
| `Temp1` | Internal temperature |
| `Temp2` | External temperature #1 |
| `Temp3` | External temperature #2 |
| `Temp4` | External temperature #3 |
| `FolderInbox_Total` | Inbox messages |
| `FolderOutbox_Total` | Outbox messages |
| `FolderSent_Last24H` | Sent messages, last 24 hours |
| `FolderSent_Last24HSendErr` | Send errors, last 24 hours |
| `FolderSent_Last1M` | Sent messages, last month |

A value of `-1` means the item is not present or not connected.

## Thresholds

| Metric | WARN | CRIT |
|---|---|---|
| GSM signal strength | < 40 % | < 20 % |
| SIM state | not `READY` | — |
| Modem state | — | not `on` |
| SIM reg state | roaming | not registered/home/roaming |
| Send errors 24h | — | > 0 |

GSM signal levels are configurable via rules. Temperature and humidity can also
be monitored with configurable upper thresholds.

## Graphing and perfometers

- `gsm_signal` includes a perfometer and graph
- `temp` and `humidity` are stored as metrics for graphs and alert rules
- SMS counters and folder statistics are exposed as metrics for trend graphs

## Requirements

- CheckMK ≥ 2.3.0
- SNMP v2c or v3 access to the SMSEagle device
- NET-SNMP `extend` module enabled on the SMSEagle (enabled by default)

## Installation

### Via MKP (recommended)

Build or download the `.mkp` package and install it:

```bash
mkp install smseagle-1.2.0.mkp
```

### Manual installation

Copy the files to your CheckMK site:

```bash
mkdir -p ~/local/lib/python3/cmk_addons/plugins/smseagle/{agent_based,graphing,rulesets}
cp agent_based/smseagle.py   ~/local/lib/python3/cmk_addons/plugins/smseagle/agent_based/
cp graphing/smseagle.py      ~/local/lib/python3/cmk_addons/plugins/smseagle/graphing/
cp rulesets/smseagle.py      ~/local/lib/python3/cmk_addons/plugins/smseagle/rulesets/
cp checkman/smseagle_*       ~/local/share/check_mk/checkman/
```

Restart the CheckMK site services and run service discovery on the SMSEagle host.
