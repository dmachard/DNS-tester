import os
from datetime import timedelta

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_TASK_RESULT_EXPIRES = int(os.getenv("CELERY_TASK_RESULT_EXPIRES", 86400))
# Auto-retry if broker is unavailable at startup
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = os.getenv("BROKER_CONNECTION_RETRY_ON_STARTUP", "true").lower() == "true"
