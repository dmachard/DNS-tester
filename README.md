# DNS Tester with Async Queue

A non-blocking API for testing DNS servers using Redis and Celery, 
allowing parallel execution of dig commands with configurable concurrency.

## Overview

This project provides a scalable solution for testing multiple DNS servers asynchronously. It uses:
- FastAPI for the REST API
- Redis as a message broker
- Celery for task queuing and execution
- Prometheus metrics for real-time monitoring
- Docker and Docker Compose for containerization

## Features

- Asynchronous execution of DNS tests using `[https://github.com/natesales/q](q)`
- Configurable concurrency level for parallel processing
- Task status tracking and result retrieval
- API documentation with Swagger UI
- Prometheus metrics for monitoring: DNS response time, total queries, failures, and more
- Containerized deployment

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
        "dns_servers": ["udp://8.8.8.8:53", "tls://1.1.1.1:853"], 
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

## Troubleshooting

List stored keys:

```bash
$ sudo docker exec -it dns-tester-redis-1 redis-cli keys '*'
2) "celery-task-meta-70b230d3-f8df-47f0-85e2-380d6b7f0254"
```

Retrieve task result:

```bash
$ sudo docker exec -it dns-tester-redis-1 redis-cli get celery-task-meta-70b230d3-f8df-47f0-85e2-380d6b7f0254
```