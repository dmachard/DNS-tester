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
- CLI support: display the results of the DNS lookup, including the DNS server, resolved IP addresses, TTL values, and response times.

Example CLI output:

```
Starting DNS lookup for domain: github.com
  Using DNS servers: Fetching from inventory
  API Base URL: http://localhost:5000
  TLS Skip Verify: False
  Task ID: 1245-3456-6789

DNS Lookup Results:
  udp://8.8.8.8 - 15.76854ms - TTL: 300s - 216.239.32.27
  udp://9.9.9.9 - 21.19606ms - TTL: 128s - 216.239.32.27
  udp://9.9.9.10 - 20.19477ms - TTL: 128s - 216.239.32.27
  tcp://8.8.8.8 - 25.51609ms - TTL: 300s - 216.239.32.27
  udp://1.1.1.1 - 10.36629ms - TTL: 150s - 216.239.32.27
  tcp://1.1.1.1 - 23.39788ms - TTL: 227s - 216.239.32.27
  tcp://9.9.9.9 - 45.15521ms - TTL: 300s - 216.239.32.27
  tcp://9.9.9.10 - 43.10374ms - TTL: 300s - 216.239.32.27
  tls://dns9.quad9.net. - 104.73758ms - TTL: 193s - 216.239.32.27
  tls://dns10.quad9.net. - 107.42914ms - TTL: 246s - 216.239.32.27
  https://dns9.quad9.net. - 116.62068ms - TTL: 65s - 216.239.32.27
  https://dns10.quad9.net. - 115.81571ms - TTL: 245s - 216.239.32.27
```

## Installation

Clone the repository:

```bash
git clone https://github.com/dmachard/dns-tester.git
cd dns-tester
```

## Usage

### Start the application with docker compose

```bash
sudo docker compose up -d
```

### Execute a DNS lookup

The swagger is available at http://localhost:5000/docs#

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
curl -s http://localhost:5000/tasks/a19e8aed-68b5-4639-ab21-f65caf8482ac
```

Response:
```json
{
  "task_id": "30949f79-c80f-41a5-8a93-754f260472ca",
  "task_status": "SUCCESS",
  "task_result": {
    "duration": 0.1,
    "details": {
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
  - details (optional): Description of the DNS provider

This allows for flexible and centralized DNS configuration management using existing Ansible setups.


## CLI Usage

The DNS Tester includes a CLI tool for performing DNS lookups directly from the command line.

### Running the CLI

To use the CLI, run the following command:

```bash
python3 cli/main.py <domain> [dns_servers...] [--qtype <query_type>] [--api-url <api_url>] [--insecure]
```

### Arguments

- `<domain>`: The domain name to query.
- `[dns_servers...]`: A list of DNS servers to query (e.g., `udp://8.8.8.8`). If not provided, the servers will be fetched from the inventory.
- `--qtype`: The DNS query type. Supported values are `A` (default) and `AAAA`.
- `--api-url`: The base URL of the API (default: `http://localhost:5000`).
- `--insecure`: Skip TLS certificate verification for secure DNS queries.

### Example Usage

#### Query a domain or IP using specific DNS servers:
```bash
python3 cli/main.py github.com udp://8.8.8.8 udp://1.1.1.1 --qtype A
```

#### Query a domain without specifying DNS servers (fetch from inventory):
```bash
python3 cli/main.py github.com --qtype AAAA
```

#### Query a domain with a custom API URL:
```bash
python3 cli/main.py github.com udp://8.8.8.8 --api-url http://custom-api-url:5000
```

#### Query a domain with insecure TLS verification:
```bash
python3 cli/main.py github.com udp://8.8.8.8 --insecure
```

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


## For developpers - running unit-tests

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
pytest tests/ -v
```

## More DNS tools ?

| | |
|:--:|------------|
| <a href="https://github.com/dmachard/DNS-collector" target="_blank"><img src="https://github.com/dmachard/DNS-collector/blob/main/docs/dns-collector_logo.png?raw=true" alt="DNS-collector" width="200"/></a> | Ingesting, pipelining, and enhancing your DNS logs with usage indicators, security analysis, and additional metadata. |
| <a href="https://github.com/dmachard/DNS-tester" target="_blank"><img src="https://github.com/dmachard/DNS-tester/blob/main/docs/logo-dns-tester.png?raw=true" alt="DNS-collector" width="200"/></a> | Monitoring DNS server availability and comparing response times across multiple DNS providers. |