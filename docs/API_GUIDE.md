
# API Usage

## Execute a DNS lookup

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

## Check the test result

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
        "tags": "",
        "dns_protocol": "Do53",
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
        "tags": "",
        "dns_protocol": "DoT",
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
