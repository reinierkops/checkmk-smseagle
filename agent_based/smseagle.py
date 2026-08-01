#!/usr/bin/env python3
"""
CheckMK SNMP check plugin for SMSEagle SMS gateway.

Monitors via NET-SNMP EXTEND-MIB (OID: .1.3.6.1.4.1.8072.1.3.2.3.1.2).
The OID index encodes the variable name as <length>.<ascii_byte>...

Checks provided:
  smseagle_gsm         - Per-modem GSM status (state, signal, SIM, network)
  smseagle_sms_count   - Per-modem SMS in/out counters
  smseagle_environment - Temperature and humidity sensors
  smseagle_folders     - Device-wide message folder statistics
"""

from collections.abc import Mapping, Sequence
from typing import Any, Dict

from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Metric,
    OIDEnd,
    Result,
    Service,
    SNMPSection,
    SNMPTree,
    State,
    StringTable,
    contains,
)

Section = Dict[str, str]

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_UNAVAILABLE = "-1"
_NO_LEVELS = ("no_levels", None)


def _decode_oid_name(oid_end: str) -> str:
    """Decode an OID suffix <length>.<ascii_byte>... into a human-readable name.

    Example: "10.83.73.77.95.83.116.97.116.101.49" -> "SIM_State1"
    """
    # OIDEnd() is relative to the base OID; strip a leading column number
    # ("2.") when the base stops one level above the column.
    if oid_end.startswith("2."):
        oid_end = oid_end[2:]
    parts = oid_end.split(".")
    try:
        length = int(parts[0])
        if len(parts) < length + 1:
            return ""
        return "".join(chr(int(x)) for x in parts[1 : length + 1])
    except (ValueError, IndexError):
        return ""


def _is_available(value: str) -> bool:
    return value != _UNAVAILABLE and value != ""


def _discover_indexes(section: Section, prefixes: Sequence[str]) -> DiscoveryResult:
    for index in range(1, 10):
        if any(
            key in section and _is_available(section[key])
            for key in (f"{prefix}{index}" for prefix in prefixes)
        ):
            yield Service(item=str(index))


def _get_fixed_levels(
    params: Mapping[str, Any],
    key: str,
) -> tuple[float, float] | None:
    levels = params.get(key)
    if not isinstance(levels, tuple) or len(levels) != 2 or levels[0] != "fixed":
        return None

    values = levels[1]
    if not isinstance(values, tuple) or len(values) != 2:
        return None

    try:
        return float(values[0]), float(values[1])
    except (TypeError, ValueError):
        return None


def _state_from_lower_levels(value: float, levels: tuple[float, float] | None) -> State:
    if levels is None:
        return State.OK

    warn, crit = levels
    if value <= crit:
        return State.CRIT
    if value <= warn:
        return State.WARN
    return State.OK


def _state_from_upper_levels(value: float, levels: tuple[float, float] | None) -> State:
    if levels is None:
        return State.OK

    warn, crit = levels
    if value >= crit:
        return State.CRIT
    if value >= warn:
        return State.WARN
    return State.OK


# ──────────────────────────────────────────────────────────────────────────────
# SNMP section
# ──────────────────────────────────────────────────────────────────────────────


def parse_smseagle(string_table: Sequence[StringTable]) -> Section:
    """Return a flat dict mapping extended-property name -> value string."""
    section: Section = {}
    for row in string_table[0]:
        oid_end, value = row[0], row[1]
        name = _decode_oid_name(oid_end)
        if name:
            section[name] = value.strip()
    return section


snmp_section_smseagle = SNMPSection(
    name="smseagle",
    parse_function=parse_smseagle,
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.8072.1.3.2.3.1",
            oids=[OIDEnd(), "2"],  # nsExtendOutput1Line
        ),
    ],
    detect=contains(".1.3.6.1.2.1.1.1.0", "smseagle"),
)


# ──────────────────────────────────────────────────────────────────────────────
# smseagle_gsm  – GSM modem status
# ──────────────────────────────────────────────────────────────────────────────

_GSM_SIGNAL_WARN = 20.0   # % signal strength warning threshold
_GSM_SIGNAL_CRIT = 10.0   # % signal strength critical threshold
_GSM_FIELDS = (
    "GSM_ModemState",
    "SIM_State",
    "SIM_RegState",
    "GSM_Signal",
    "GSM_NetName",
)


def discover_smseagle_gsm(section: Section) -> DiscoveryResult:
    """Yield one service per modem with any available GSM data."""
    yield from _discover_indexes(section, _GSM_FIELDS)


def check_smseagle_gsm(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
    modem_state = section.get(f"GSM_ModemState{item}", _UNAVAILABLE)
    sim_state = section.get(f"SIM_State{item}", _UNAVAILABLE)
    sim_reg_state = section.get(f"SIM_RegState{item}", _UNAVAILABLE)
    gsm_signal_raw = section.get(f"GSM_Signal{item}", _UNAVAILABLE)
    gsm_net_name = section.get(f"GSM_NetName{item}", _UNAVAILABLE)
    signal_levels = _get_fixed_levels(params, "signal_levels")

    if not any(
        _is_available(value)
        for value in (modem_state, sim_state, sim_reg_state, gsm_signal_raw, gsm_net_name)
    ):
        yield Result(state=State.UNKNOWN, summary=f"Modem {item} data not available")
        return

    # Modem on/off
    if _is_available(modem_state):
        if modem_state.lower() == "on":
            yield Result(state=State.OK, summary=f"Modem: {modem_state}")
        else:
            yield Result(state=State.CRIT, summary=f"Modem: {modem_state}")

    # SIM card state
    if _is_available(sim_state):
        if sim_state.upper() == "READY":
            yield Result(state=State.OK, summary=f"SIM: {sim_state}")
        else:
            yield Result(state=State.WARN, summary=f"SIM: {sim_state}")

    # SIM registration state
    if _is_available(sim_reg_state):
        lower = sim_reg_state.lower()
        if "home" in lower or "registered" in lower:
            reg_state = State.OK
        elif "roaming" in lower:
            reg_state = State.WARN
        else:
            reg_state = State.CRIT
        yield Result(state=reg_state, summary=f"Registration: {sim_reg_state}")

    # GSM signal strength
    if _is_available(gsm_signal_raw):
        try:
            signal = float(gsm_signal_raw)
            sig_state = _state_from_lower_levels(signal, signal_levels)
            yield Result(state=sig_state, summary=f"Signal: {signal:.0f}%")
            metric_kwargs: dict[str, Any] = {"boundaries": (0.0, 100.0)}
            if signal_levels is not None:
                metric_kwargs["levels"] = signal_levels
            yield Metric("gsm_signal", signal, **metric_kwargs)
        except ValueError:
            yield Result(state=State.UNKNOWN, summary=f"Signal: {gsm_signal_raw} (invalid)")

    # Network name (informational only)
    if _is_available(gsm_net_name):
        yield Result(state=State.OK, summary=f"Network: {gsm_net_name}")


check_plugin_smseagle_gsm = CheckPlugin(
    name="smseagle_gsm",
    service_name="SMSEagle GSM Modem %s",
    sections=["smseagle"],
    discovery_function=discover_smseagle_gsm,
    check_function=check_smseagle_gsm,
    check_ruleset_name="smseagle_gsm",
    check_default_parameters={
        "signal_levels": ("fixed", (_GSM_SIGNAL_WARN, _GSM_SIGNAL_CRIT)),
    },
)


# ──────────────────────────────────────────────────────────────────────────────
# smseagle_sms_count  – SMS in/out counters
# ──────────────────────────────────────────────────────────────────────────────


def discover_smseagle_sms_count(section: Section) -> DiscoveryResult:
    """Yield one service per modem that has SMS counters."""
    yield from _discover_indexes(section, ("SMSCountIn", "SMSCountOut"))


def check_smseagle_sms_count(item: str, section: Section) -> CheckResult:
    count_in = section.get(f"SMSCountIn{item}", _UNAVAILABLE)
    count_out = section.get(f"SMSCountOut{item}", _UNAVAILABLE)

    if not _is_available(count_in) and not _is_available(count_out):
        yield Result(state=State.UNKNOWN, summary=f"Modem {item} SMS counters not available")
        return

    details = []

    if _is_available(count_in):
        try:
            in_val = int(count_in)
            details.append(f"Incoming: {in_val}")
            yield Metric("sms_count_in", float(in_val))
        except ValueError:
            details.append(f"Incoming: {count_in} (invalid)")

    if _is_available(count_out):
        try:
            out_val = int(count_out)
            details.append(f"Outgoing: {out_val}")
            yield Metric("sms_count_out", float(out_val))
        except ValueError:
            details.append(f"Outgoing: {count_out} (invalid)")

    yield Result(state=State.OK, summary=", ".join(details))


check_plugin_smseagle_sms_count = CheckPlugin(
    name="smseagle_sms_count",
    service_name="SMSEagle SMS Count Modem %s",
    sections=["smseagle"],
    discovery_function=discover_smseagle_sms_count,
    check_function=check_smseagle_sms_count,
)


# ──────────────────────────────────────────────────────────────────────────────
# smseagle_environment  – Temperature / Humidity sensors
# ──────────────────────────────────────────────────────────────────────────────

_TEMP_KEYS = ["Temp", "Temp1", "Temp2", "Temp3", "Temp4"]


def discover_smseagle_environment(section: Section) -> DiscoveryResult:
    """Yield one service per available temperature sensor and for humidity."""
    for key in _TEMP_KEYS:
        if key in section and _is_available(section[key]):
            yield Service(item=key)
    if "Humidity" in section and _is_available(section["Humidity"]):
        yield Service(item="Humidity")


def check_smseagle_environment(
    item: str,
    params: Mapping[str, Any],
    section: Section,
) -> CheckResult:
    value_str = section.get(item, _UNAVAILABLE)
    if not _is_available(value_str):
        yield Result(state=State.UNKNOWN, summary=f"{item} not available")
        return

    try:
        value = float(value_str)
    except ValueError:
        yield Result(state=State.UNKNOWN, summary=f"{item}: {value_str!r} (invalid)")
        return

    if item.startswith("Temp"):
        levels = _get_fixed_levels(params, "temperature_levels")
        yield Result(
            state=_state_from_upper_levels(value, levels),
            summary=f"Temperature: {value:.1f} °C",
        )
        metric_kwargs = {"levels": levels} if levels is not None else {}
        yield Metric("temp", value, **metric_kwargs)
    else:
        levels = _get_fixed_levels(params, "humidity_levels")
        yield Result(
            state=_state_from_upper_levels(value, levels),
            summary=f"Humidity: {value:.1f}%",
        )
        metric_kwargs = {"boundaries": (0.0, 100.0)}
        if levels is not None:
            metric_kwargs["levels"] = levels
        yield Metric("humidity", value, **metric_kwargs)


check_plugin_smseagle_environment = CheckPlugin(
    name="smseagle_environment",
    service_name="SMSEagle %s",
    sections=["smseagle"],
    discovery_function=discover_smseagle_environment,
    check_function=check_smseagle_environment,
    check_ruleset_name="smseagle_environment",
    check_default_parameters={
        "temperature_levels": _NO_LEVELS,
        "humidity_levels": _NO_LEVELS,
    },
)


# ──────────────────────────────────────────────────────────────────────────────
# smseagle_folders  – Device-wide message folder statistics
# ──────────────────────────────────────────────────────────────────────────────

_FOLDER_KEYS = (
    "FolderInbox_Total",
    "FolderOutbox_Total",
    "FolderSent_Last24H",
    "FolderSent_Last24HSendErr",
    "FolderSent_Last1M",
)


def discover_smseagle_folders(section: Section) -> DiscoveryResult:
    """Yield one service when at least one folder statistic is available."""
    if any(k in section and _is_available(section[k]) for k in _FOLDER_KEYS):
        yield Service()


def check_smseagle_folders(section: Section) -> CheckResult:
    found_any = False
    send_err_val = 0

    for key in _FOLDER_KEYS:
        raw = section.get(key, _UNAVAILABLE)
        if not _is_available(raw):
            continue
        try:
            val = int(raw)
        except ValueError:
            yield Result(state=State.UNKNOWN, summary=f"{key}: {raw!r} (invalid)")
            continue

        found_any = True
        label_map = {
            "FolderInbox_Total": "Inbox",
            "FolderOutbox_Total": "Outbox",
            "FolderSent_Last24H": "Sent 24h",
            "FolderSent_Last24HSendErr": "Send errors 24h",
            "FolderSent_Last1M": "Sent 1 month",
        }
        metric_map = {
            "FolderInbox_Total": "folder_inbox_total",
            "FolderOutbox_Total": "folder_outbox_total",
            "FolderSent_Last24H": "folder_sent_last_24h",
            "FolderSent_Last24HSendErr": "folder_sent_last_24h_send_err",
            "FolderSent_Last1M": "folder_sent_last_1m",
        }

        label = label_map[key]
        metric_name = metric_map[key]

        if key == "FolderSent_Last24HSendErr":
            send_err_val = val
        else:
            yield Result(state=State.OK, summary=f"{label}: {val}")
        yield Metric(metric_name, float(val))

    if not found_any:
        yield Result(state=State.UNKNOWN, summary="No folder statistics available")
        return

    # Report send errors last so they set the worst state
    if "FolderSent_Last24HSendErr" in section and _is_available(
        section["FolderSent_Last24HSendErr"]
    ):
        err_state = State.CRIT if send_err_val > 0 else State.OK
        yield Result(
            state=err_state,
            summary=f"Send errors 24h: {send_err_val}",
        )


check_plugin_smseagle_folders = CheckPlugin(
    name="smseagle_folders",
    service_name="SMSEagle Folders",
    sections=["smseagle"],
    discovery_function=discover_smseagle_folders,
    check_function=check_smseagle_folders,
)
