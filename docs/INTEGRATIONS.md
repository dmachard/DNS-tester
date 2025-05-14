
# Ansible Inventory Support

The DNS Tester supports retrieving DNS server information from a static Ansible inventory file.

When no dns_servers are explicitly provided in the request, the API loads the DNS server list from the [dns] group in the inventory.

Example inventory:

```
[dns]
google1 dns_address="8.8.8.8" domain_name="" services="do53" tags="GOOGLE"
quad9 dns_address="9.9.9.9" domain_name="dns9.quad9.net." services="do53, dot, doh" tags="QUAD9, ALLPROTOCOL"
cloudflare dns_address="1.1.1.1" domain_name="" services="do53" tags="CLOUDFLARE"
```

Each host entry must define:
  - dns_address (required): IP address of the DNS server
  - domain_name (optional): FQDN used for protocols like DoT/DoH
  - services (optional): Comma-separated list of supported protocols (do53, dot, doh)
  - tags (optional): Tags for the DNS provider

This allows for flexible and centralized DNS configuration management using existing Ansible setups.

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

