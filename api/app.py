import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from worker.lookup import lookup_dns as celery_lookup_dns
from worker.lookup import get_metrics as celery_get_metrics

from api.models import DNSLookup, DNSLookupStatus
from api.ansible import get_dns_servers_from_ansible

dnstester_logger = logging.getLogger('dnstester')
api_version = os.getenv('API_VERSION', '0.0.0')

app = FastAPI(
    title="DNS Tester API",
    version=api_version
)

@app.post("/dns-lookup")
async def enqueue_dns_lookup(request: DNSLookup):
    """
    Enqueue a DNS test task.
    """
    dnstester_logger.debug(f"Received DNS lookup request: {request}")

    # Get the request
    dns_servers = [server.model_dump() for server in request.dns_servers] if request.dns_servers else []

    # Checck if DNS inventory is empty
    if not dns_servers:
        dnstester_logger.debug(f"No DNS servers provided in request, fetching from Ansible inventory")
        dns_servers = get_dns_servers_from_ansible()
        dnstester_logger.debug(f"{len(dns_servers)} DNS servers detected")

    # Check if DNS inventory is still empty
    if not dns_servers:
        raise HTTPException(status_code=400, detail="No DNS servers provided")
    
    task = celery_lookup_dns.delay(request.domain, request.qtype, dns_servers, request.tls_insecure_skip_verify)
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
    metrics_data = celery_get_metrics.delay().get(timeout=5)
    return Response(metrics_data, media_type="text/plain")
