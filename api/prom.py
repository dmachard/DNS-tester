
from prometheus_client import Counter, Gauge, Histogram

# Prometheus Metrics
dns_response_time = Histogram(
    "dns_response_time_seconds",
    "Time taken for DNS resolution",
    ["server"]
)

dns_total_queries = Counter(
    "dns_total_queries",
    "Total number of DNS queries",
    ["server"]
)

dns_noerror_count = Counter(
    "dns_noerror_count",
    "Count of successful DNS resolutions (NoError)",
    ["server"]
)

dns_failure_count = Counter(
    "dns_failure_count",
    "Total number of failed DNS queries",
    ["server", "rcode"]
)

dns_avg_response_time = Gauge(
    "dns_avg_response_time_seconds",
    "Average DNS response time",
    ["server"]
)

dns_query_types_count = Counter(
    "dns_query_types_count",
    "Total number of DNS queries per query type",
    ["qtype"]
)
