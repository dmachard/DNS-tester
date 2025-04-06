<p align="center">
  <img src="https://img.shields.io/github/v/release/dmachard/dns-tester?logo=github&sort=semver" alt="release"/>
  <img src="https://img.shields.io/docker/pulls/dmachard/dnstester.svg" alt="docker"/>
</p>

<p align="center">
  <img src="docs/logo-dns-tester.png" alt="DNS-collector"/>
</p>

This tool provides a scalable solution for testing multiple DNS servers asynchronously. It uses:
- FastAPI for the REST API
- Redis as a message broker
- Celery for task queuing and execution
- Prometheus metrics for real-time monitoring
- Support DNS servers from Ansible inventory

## Installation

Clone the repository:

```bash
git clone https://github.com/dmachard/dns-tester.git
cd dns-tester
```

## Usage

### Start the application with docker compose

```bash
sudo docker compose --env-file example.env up -d
```

### Execute a DNS lookup

```bash
curl -X POST http://localhost:5000/dns-lookup \
  -H "Content-Type: application/json" \
  -d '{
        "domain": "example.com", 
        "dns_servers": [{"target": "udp://8.8.8.8:53"}, {"target": "tls://1.1.1.1:853"}], 
        "qtype": "A",
        "tls_insecure_skip_verify": false
      }'

```

Response:
```json
{
  "task_id": "a19e8aed-68b5-4639-ab21-f65caf8482ac",
  "status": "DNS lookup enqueued"
}
```

### Check the test result

```bash
curl http://localhost:5000/task/a19e8aed-68b5-4639-ab21-f65caf8482ac
```

Response:
```json
{
  "task_id": "30949f79-c80f-41a5-8a93-754f260472ca",
  "task_status": "SUCCESS",
  "result": {
    "udp://8.8.8.8:53": {
      "command_status": "ok",
      "description": "",
      "time_ms": 13.452129,
      "rcode": "NOERROR",
      "name": "example.com.",
      "qtype": "A",
      "answers": [
        {
          "name": "example.com.",
          "type": "A",
          "ttl": 110,
          "value": "23.192.228.80"
        }
      ],
      "error": null
    },
    "tls://1.1.1.1:853": {
      "command_status": "ok",
      "description": "",
      "time_ms": 128.041827,
      "rcode": "NOERROR",
      "name": "example.com.",
      "qtype": "A",
      "answers": [
        {
          "name": "example.com.",
          "type": "A",
          "ttl": 193,
          "value": "23.192.228.80"
        }
      ],
      "error": null
    }
  }
}
```

### Ansible Inventory Support

The DNS Tester supports retrieving DNS server information from a static Ansible inventory file.

When no dns_servers are explicitly provided in the request, the API loads the DNS server list from the [dns] group in the inventory.

Example inventory:

```
[dns]
google1 dns_address="8.8.8.8" domain_name="" services="do53" details="DNS GOOGLE"
quad9 dns_address="9.9.9.9" domain_name="dns9.quad9.net." services="do53, dot, doh" details="DNS QUAD9"
cloudflare dns_address="1.1.1.1" domain_name="" services="do53" details="DNS CLOUDFLARE"
```

Each host entry must define:
  - dns_address (required): IP address of the DNS server
  - domain_name (optional): FQDN used for protocols like DoT/DoH
  - services (optional): Comma-separated list of supported protocols (do53, dot, doh)
  - sdetails (optional): Description of the DNS provider

This allows for flexible and centralized DNS configuration management using existing Ansible setups.

## Monitoring with Prometheus

This project includes Prometheus metrics to track DNS resolution performance.

| **Metric Name**              | **Type**   | **Description** |
|------------------------------|-----------|----------------|
| `dns_total_queries`          | Counter   | Total number of DNS queries sent. |
| `dns_noerror_count`          | Counter   | Count of successful queries (`NOERROR`). |
| `dns_failure_count`          | Counter   | Count of failed queries (`NXDOMAIN`, `SERVFAIL`, etc.). |
| `dns_response_time_seconds`  | Histogram | Tracks the distribution of DNS response times. |
| `dns_avg_response_time`      | Gauge     | The most recent DNS response time per server. |
| `dns_query_types_count`      | Counter   | Number of queries per record type (A, AAAA, CNAME, etc.). |


## Running Tests

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
pytest tests/ -v
```

## More tools

## More tools

<a href="https://github.com/dmachard/DNS-collector" target="_blank">
  <img src="https://github.com/dmachard/DNS-collector/blob/main/docs/dns-collector_logo.png" alt="DNS-collector" style="max-width: 300px;"/>
</a>