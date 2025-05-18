
# Monitoring with Prometheus

This project includes Prometheus metrics to track DNS resolution performance.

| **Metric Name**              | **Type**   | **Description** |
|------------------------------|-----------|----------------|
| `dns_total_queries`          | Counter   | Total number of DNS queries sent. |
| `dns_noerror_count`          | Counter   | Count of successful queries (`NOERROR`). |
| `dns_failure_count`          | Counter   | Count of failed queries (`NXDOMAIN`, `SERVFAIL`, etc.). |
| `dns_response_time_seconds`  | Histogram | Tracks the distribution of DNS response times. |
| `dns_avg_response_time`      | Gauge     | The most recent DNS response time per server. |
| `dns_query_types_count`      | Counter   | Number of queries per record type (A, AAAA, CNAME, etc.). |

