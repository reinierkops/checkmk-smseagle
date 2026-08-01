#!/usr/bin/env python3

from cmk.graphing.v1 import graphs, metrics, perfometers, Title

UNIT_COUNT = metrics.Unit(metrics.DecimalNotation(""), metrics.StrictPrecision(0))
UNIT_PERCENTAGE = metrics.Unit(metrics.DecimalNotation("%"))

metric_gsm_signal = metrics.Metric(
    name="gsm_signal",
    title=Title("GSM signal strength"),
    unit=UNIT_PERCENTAGE,
    color=metrics.Color.GREEN,
)
metric_sms_count_in = metrics.Metric(
    name="sms_count_in",
    title=Title("Incoming SMS"),
    unit=UNIT_COUNT,
    color=metrics.Color.BLUE,
)
metric_sms_count_out = metrics.Metric(
    name="sms_count_out",
    title=Title("Outgoing SMS"),
    unit=UNIT_COUNT,
    color=metrics.Color.ORANGE,
)
metric_folder_inbox_total = metrics.Metric(
    name="folder_inbox_total",
    title=Title("Inbox messages"),
    unit=UNIT_COUNT,
    color=metrics.Color.BLUE,
)
metric_folder_outbox_total = metrics.Metric(
    name="folder_outbox_total",
    title=Title("Outbox messages"),
    unit=UNIT_COUNT,
    color=metrics.Color.ORANGE,
)
metric_folder_sent_last_24h = metrics.Metric(
    name="folder_sent_last_24h",
    title=Title("Sent in last 24 hours"),
    unit=UNIT_COUNT,
    color=metrics.Color.GREEN,
)
metric_folder_sent_last_24h_send_err = metrics.Metric(
    name="folder_sent_last_24h_send_err",
    title=Title("Send errors in last 24 hours"),
    unit=UNIT_COUNT,
    color=metrics.Color.RED,
)
metric_folder_sent_last_1m = metrics.Metric(
    name="folder_sent_last_1m",
    title=Title("Sent in last month"),
    unit=UNIT_COUNT,
    color=metrics.Color.PURPLE,
)

perfometer_gsm_signal = perfometers.Perfometer(
    name="gsm_signal",
    focus_range=perfometers.FocusRange(
        perfometers.Closed(0),
        perfometers.Closed(100.0),
    ),
    segments=["gsm_signal"],
)

graph_smseagle_gsm_signal = graphs.Graph(
    name="smseagle_gsm_signal",
    title=Title("GSM signal strength"),
    compound_lines=["gsm_signal"],
    simple_lines=[
        metrics.WarningOf("gsm_signal"),
        metrics.CriticalOf("gsm_signal"),
    ],
)
graph_smseagle_sms_count = graphs.Graph(
    name="smseagle_sms_count",
    title=Title("SMS counters"),
    compound_lines=["sms_count_in", "sms_count_out"],
)
graph_smseagle_folder_totals = graphs.Graph(
    name="smseagle_folder_totals",
    title=Title("Message folder totals"),
    compound_lines=[
        "folder_inbox_total",
        "folder_outbox_total",
        "folder_sent_last_24h",
        "folder_sent_last_1m",
    ],
)
graph_smseagle_folder_send_errors = graphs.Graph(
    name="smseagle_folder_send_errors",
    title=Title("Message send errors"),
    compound_lines=["folder_sent_last_24h_send_err"],
)
