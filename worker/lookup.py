import os

from celery import Celery

from worker.q import run_q
from worker import celeryconfig

wrk = Celery('dns_tester', broker=celeryconfig.CELERY_BROKER_URL, backend=celeryconfig.CELERY_RESULT_BACKEND)
wrk.conf.update(
    result_expires=celeryconfig.CELERY_TASK_RESULT_EXPIRES,
    broker_connection_retry_on_startup=celeryconfig.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
)

wrk.conf.broker_connection_retry_on_startup = True

@wrk.task()
def lookup_dns(domain, qtype, dns_servers, tls_insecure_skip_verify):
    return run_q(domain, qtype, dns_servers, tls_insecure_skip_verify)