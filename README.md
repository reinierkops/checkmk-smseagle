# CheckMK SMSEagle

CheckMK SNMP monitoring plugin for the [SMSEagle](https://www.smseagle.eu/) SMS gateway.

## Checks

| Check name | Service name | Description |
|---|---|---|
| `smseagle_gsm` | `SMSEagle Modem <N>` | GSM modem state, SIM status, signal strength, network name |
| `smseagle_sms_count` | `SMSEagle SMS Count Modem <N>` | Incoming and outgoing SMS counters with performance graphs |
| `smseagle_environment` | `SMSEagle <sensor>` | Temperature (°C) and humidity (%) from optional sensors |

## How it works

The SMSEagle exposes its extended properties via the NET-SNMP EXTEND-MIB
(`OID: .1.3.6.1.4.1.8072.1.3.2.3.1.2`). Each leaf OID encodes its own name
as a length-prefixed ASCII byte sequence in the OID index, e.g.:

```
.1.3.6.1.4.1.8072.1.3.2.3.1.2.10.83.73.77.95.83.116.97.116.101.49  →  SIM_State1 = READY
.1.3.6.1.4.1.8072.1.3.2.3.1.2.11.71.83.77.95.83.105.103.110.97.108.49  →  GSM_Signal1 = 72
```

The plugin decodes these OID names automatically and builds a key/value map
used by all three checks.

## Variables monitored

| Variable | Example | Description |
|---|---|---|
| `GSM_ModemState1/2` | `on` | Modem power state |
| `SIM_State1/2` | `READY` | SIM card state |
| `SIM_RegState1/2` | `Registered Home` | Network registration state |
| `GSM_Signal1/2` | `72` | Signal strength (%) |
| `GSM_NetName1/2` | `KPN KPN` | Network operator name |
| `SMSCountIn1/2` | `0` | Cumulative incoming SMS count |
| `SMSCountOut1/2` | `0` | Cumulative outgoing SMS count |
| `Temp` / `Temp1-4` | `21.5` | Temperature in °C (optional sensor) |
| `Humidity` | `55.0` | Relative humidity % (optional sensor) |

A value of `-1` means the item is not present or not connected.

## Thresholds

| Metric | WARN | CRIT |
|---|---|---|
| GSM signal strength | < 20 % | < 10 % |
| SIM state | not `READY` | — |
| Modem state | — | not `on` |
| SIM reg state | roaming | not registered/home/roaming |

## Requirements

- CheckMK ≥ 2.3.0
- SNMP v2c or v3 access to the SMSEagle device
- NET-SNMP `extend` module enabled on the SMSEagle (enabled by default)

## Installation

### Via MKP (recommended)

Build or download the `.mkp` package and install it:

```bash
mkp install smseagle-1.0.0.mkp
```

### Manual installation

Copy the files to your CheckMK site:

```bash
cp agent_based/smseagle.py   ~/local/lib/check_mk/plugins/agent_based/
cp checkman/smseagle_*       ~/local/share/check_mk/checkman/
```

Restart the CheckMK site services and run service discovery on the SMSEagle host.
