"""Celery Beat scheduler configuration for background jobs."""

from celery.schedules import crontab

# Celery Beat schedule configuration
beat_schedule = {
    # Daily Garmin sync at 6:00 AM UTC
    "garmin-daily-sync": {
        "task": "ai_trainer.jobs.garmin_sync.sync_all_users",
        "schedule": crontab(hour=6, minute=0),
        "options": {
            "queue": "garmin",
            "expires": 3600,  # Task expires after 1 hour if not picked up
        },
    },
    # Daily recovery score calculation at 6:30 AM UTC (after Garmin sync)
    "calculate-daily-recovery": {
        "task": "ai_trainer.jobs.calculate_recovery.calculate_all_users",
        "schedule": crontab(hour=6, minute=30),
        "options": {
            "queue": "recovery",
            "expires": 3600,
        },
    },
    # Weekly insight generation every Sunday at 7:00 AM UTC
    "generate-weekly-insights": {
        "task": "ai_trainer.jobs.generate_insights.generate_weekly_insights",
        "schedule": crontab(day_of_week=0, hour=7, minute=0),
        "options": {
            "queue": "insights",
            "expires": 7200,  # 2 hours
        },
    },
    # Weekly training plan adjustment every Sunday at 8:00 AM UTC
    "adjust-training-plans": {
        "task": "ai_trainer.jobs.generate_plans.adjust_weekly_plans",
        "schedule": crontab(day_of_week=0, hour=8, minute=0),
        "options": {
            "queue": "plans",
            "expires": 7200,
        },
    },
    # Cleanup old data every day at 2:00 AM UTC
    "cleanup-old-data": {
        "task": "ai_trainer.jobs.maintenance.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),
        "options": {
            "queue": "maintenance",
            "expires": 3600,
        },
    },
}

# Task configuration for scheduled jobs
task_settings = {
    # Retry policy for failed tasks
    "task_autoretry_for": (Exception,),
    "task_retry_kwargs": {
        "max_retries": 3,
        "countdown": 60,  # Wait 1 minute between retries
    },
    # Task result compression
    "task_compression": "gzip",
    # Task result extended
    "task_track_started": True,
    "task_send_sent_event": True,
}
