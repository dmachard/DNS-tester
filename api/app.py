import os

from fastapi import FastAPI
from fastapi.responses import Response

from worker.lookup import lookup_dns as celery_lookup_dns
from api.models import DNSLookup, DNSLookupStatus

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

api_version = os.getenv('API_VERSION', '0.0.0')

app = FastAPI(
    title="DNS Tester API",
    version=api_version
)

# 🔥 Prometheus Metrics
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

@app.post("/dns-lookup")
async def create_dns_lookup(request: DNSLookup):
    """
    Enqueue a DNS test task.
    """
    task = celery_lookup_dns.delay(request.domain, request.qtype, request.dns_servers, request.tls_insecure_skip_verify)
    return {"task_id": task.id, "message": "DNS lookup enqueued"}

@app.get("/tasks/{task_id}", response_model=DNSLookupStatus)
async def get_task_status(task_id: str):
    """
    Get task status by task ID.
    """
    task_result = celery_lookup_dns.AsyncResult(task_id)
    if task_result.state == 'PENDING':
        return {"task_id": task_id, "task_status": "PENDING", "message": "Task is pending execution"}
    elif task_result.state == 'FAILURE':
        return {"task_id": task_id, "task_status": "FAILURE", "error": str(task_result.result)}
    elif task_result.state == 'SUCCESS':
        # 🔥 Update Prometheus metrics
        for server, result in task_result.result.items():
            if 'command_status' in result and result["command_status"] == "ok" :
                response_time_sec = result["time_ms"] / 1000  # Convert ms → seconds
                
                # 🔢 Increment total queries count
                dns_total_queries.labels(server=server).inc()
                
                # ⏱ Observe response time histogram
                dns_response_time.labels(server=server).observe(response_time_sec)
                
                # 📊 Update latest response time
                dns_avg_response_time.labels(server=server).set(response_time_sec)
                
                # 📡 Increment query type count (A, AAAA, CNAME, etc.)
                dns_query_types_count.labels(qtype=result["qtype"]).inc()
                
                # ✅ Increment successful resolution count
                if result["rcode"] == "NOERROR":
                    dns_noerror_count.labels(server=server).inc()
                else:
                    # ❌ Increment failed resolution count (NXDOMAIN, SERVFAIL...)
                    dns_failure_count.labels(server=server, rcode=result["rcode"]).inc()


        return {"task_id": task_id, "task_status": "SUCCESS", "result": task_result.result}
    else:
        return {"task_id": task_id, "task_status": task_result.state}
    
@app.get("/status")
async def health_check():
    """
    Health check endpoint for the API service.
    """
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)