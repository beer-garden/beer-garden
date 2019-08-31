from prometheus_client import Summary

# Summaries:
http_api_latency_total = Summary(
    "bg_http_api_latency_seconds",
    "Total number of seconds each API endpoint is taking to respond.",
    ["method", "route", "status"],
)
