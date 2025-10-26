"""Celery application with Redis broker."""

import os
from celery import Celery

# Redis URL for broker and result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery application
celery_app = Celery(
    "ai_trainer",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    # Task result expiration (24 hours)
    result_expires=86400,
    # Task hard time limit (10 minutes)
    task_time_limit=600,
    # Task soft time limit (5 minutes)
    task_soft_time_limit=300,
    # Task acknowledgment settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Task routing
    task_routes={
        "ai_trainer.jobs.garmin_sync.*": {"queue": "garmin"},
        "ai_trainer.jobs.calculate_recovery.*": {"queue": "recovery"},
        "ai_trainer.jobs.generate_insights.*": {"queue": "insights"},
        "ai_trainer.jobs.generate_plans.*": {"queue": "plans"},
    },
)

# Auto-discover tasks in jobs directory
celery_app.autodiscover_tasks(
    ["src.jobs"],
    force=True,
)
