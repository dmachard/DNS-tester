import os
import logging
import logging.config
import time

from celery import Celery
from prometheus_client import generate_latest

from worker.q import run_q
from worker import celeryconfig

wrk = Celery('dns_tester', broker=celeryconfig.CELERY_BROKER_URL, backend=celeryconfig.CELERY_RESULT_BACKEND)
wrk.conf.update(
    result_expires=celeryconfig.CELERY_TASK_RESULT_EXPIRES,
    broker_connection_retry_on_startup=celeryconfig.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
)

wrk.conf.broker_connection_retry_on_startup = True

@wrk.on_after_configure.connect
def setup_logging(**kwargs):
    logging.config.fileConfig('/app/logging.conf')

@wrk.task()
def lookup_dns(domain, qtype, dns_servers, tls_insecure_skip_verify):
    start_time = time.time()
    results = run_q(domain, qtype, dns_servers, tls_insecure_skip_verify)
    runtime = time.time() - start_time
    return {"details": results, "duration": runtime}

@wrk.task()
def get_metrics():
    return  generate_latest().decode('utf-8')