import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from cli.version import API_VERSION

from worker.lookup import lookup_dns as celery_lookup_dns
from worker.lookup import get_metrics as celery_get_metrics

from api.models import DNSLookup, ReverseDNSLookup, DNSLookupStatus
from api.ansible import get_dns_servers_from_ansible

dnstester_logger = logging.getLogger('dnstester')

app = FastAPI(
    title="DNS Tester API",
    version=API_VERSION,
)

@app.post("/dns-lookup")
async def enqueue_dns_lookup(request: DNSLookup):
    """
    Enqueue a DNS lookup task.
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

@app.post("/reverse-lookup")
async def enqueue_reverse_lookup(request: ReverseDNSLookup):
    """
    Enqueue a DNS reverse task.
    """
    dnstester_logger.debug(f"Received Reverse DNS lookup request: {request}")

    # Get from request
    reverse_ip = str(request.reverse_ip)
    dns_servers = [server.model_dump() for server in request.dns_servers] if request.dns_servers else []

    # Checck if DNS inventory is empty
    if not dns_servers:
        dnstester_logger.debug(f"No DNS servers provided in request, fetching from Ansible inventory")
        dns_servers = get_dns_servers_from_ansible()
        dnstester_logger.debug(f"{len(dns_servers)} DNS servers detected")

    # Check if DNS inventory is still empty
    if not dns_servers:
        raise HTTPException(status_code=400, detail="No DNS servers provided")
    
    task = celery_lookup_dns.delay(reverse_ip, "PTR", dns_servers, request.tls_insecure_skip_verify)
    return {"task_id": task.id, "message": "Reverse DNS lookup enqueued"}

@app.get("/tasks/{task_id}", response_model=DNSLookupStatus)
async def get_task_status(task_id: str):
    """
    Get task status by task ID.
    """
    task_result = celery_lookup_dns.AsyncResult(task_id)
    return {"task_id": task_id, "task_status": task_result.state, "task_result": task_result.result}
    
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
