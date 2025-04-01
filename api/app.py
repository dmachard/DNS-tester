import os

from fastapi import FastAPI
from fastapi.responses import Response

from worker.lookup import lookup_dns as celery_lookup_dns
from api.models import DNSLookup, DNSLookupStatus
import api.prom 

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

api_version = os.getenv('API_VERSION', '0.0.0')

app = FastAPI(
    title="DNS Tester API",
    version=api_version
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
        # Update Prometheus metrics
        for server, result in task_result.result.items():
            if 'command_status' in result and result["command_status"] == "ok" :
                response_time_sec = result["time_ms"] / 1000  # Convert ms → seconds
                
                # Increment total queries count
                api.prom.dns_total_queries.labels(server=server).inc()
                
                # Observe response time histogram
                api.prom.dns_response_time.labels(server=server).observe(response_time_sec)
                
                # pdate latest response time
                api.prom.dns_avg_response_time.labels(server=server).set(response_time_sec)
                
                # Increment query type count (A, AAAA, CNAME, etc.)
                api.prom.dns_query_types_count.labels(qtype=result["qtype"]).inc()
                
                # Increment successful resolution count
                if result["rcode"] == "NOERROR":
                    api.prom.dns_noerror_count.labels(server=server).inc()
                else:
                    # Increment failed resolution count (NXDOMAIN, SERVFAIL...)
                    api.prom.dns_failure_count.labels(server=server, rcode=result["rcode"]).inc()


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
async def prom():
    """
    Expose Prometheus metrics.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)