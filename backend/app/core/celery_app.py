"""Celery Application Configuration for Asynchronous Tasks."""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "dealguard_tasks",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend(),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max for large diligence packets
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
