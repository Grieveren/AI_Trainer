"""
Garmin data synchronization background jobs.

Celery tasks for fetching health metrics and workout data from Garmin Connect API.
Runs daily at 6 AM or can be triggered manually.
"""

from datetime import date, timedelta
import logging

from src.celery_app import celery_app
from src.database.connection import get_sync_db_session
from src.models.user import User
from src.utils.encryption import decrypt_token
from sqlalchemy import select

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
def sync_user_garmin_data(self, user_id: str, sync_date: str = None):
    """
    Sync Garmin data for a single user.

    Args:
        user_id: UUID of user to sync
        sync_date: Optional ISO date string (defaults to yesterday)

    Raises:
        Exception: If sync fails after retries
    """
    try:
        # Parse sync date (default to yesterday to ensure data is available)
        if sync_date:
            target_date = date.fromisoformat(sync_date)
        else:
            target_date = date.today() - timedelta(days=1)

        logger.info(f"Starting Garmin sync for user {user_id}, date {target_date}")

        # Get database session (sync context for Celery)
        with get_sync_db_session() as db:
            # Load user
            user = db.execute(
                select(User).where(User.id == user_id)
            ).scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return {"status": "error", "message": "User not found"}

            # Verify user has Garmin connected
            if not user.garmin_access_token:
                logger.warning(f"User {user_id} has no Garmin account connected")
                return {"status": "skipped", "message": "No Garmin account"}

            # Decrypt tokens
            access_token = decrypt_token(user.garmin_access_token)
            refresh_token = decrypt_token(user.garmin_refresh_token)

            # Create Garmin client
            # Note: Need to convert to async context or use sync client
            # For now, this is a simplified version
            # TODO: Implement proper async/sync handling

            # Sync health metrics
            health_synced = _sync_health_metrics_sync(
                db, user, access_token, refresh_token, target_date
            )

            # Sync workouts (last 7 days)
            workouts_synced = _sync_workouts_sync(
                db, user, access_token, refresh_token, target_date
            )

            logger.info(
                f"Garmin sync complete for user {user_id}: "
                f"{health_synced} health metrics, {workouts_synced} workouts"
            )

            return {
                "status": "success",
                "user_id": user_id,
                "sync_date": str(target_date),
                "health_metrics_synced": health_synced,
                "workouts_synced": workouts_synced,
            }

    except Exception as exc:
        logger.error(f"Garmin sync failed for user {user_id}: {exc}")

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries)


def _sync_health_metrics_sync(
    db, user: User, access_token: str, refresh_token: str, target_date: date
) -> int:
    """
    Sync health metrics for target date (synchronous version).

    Returns:
        Number of metrics synced
    """
    # TODO: Implement sync version or refactor to use async properly
    # This is a placeholder that needs proper implementation

    logger.info(f"Syncing health metrics for {user.id} on {target_date}")

    # For now, return 0 indicating work needed
    # In full implementation, would fetch from Garmin and save to DB
    return 0


def _sync_workouts_sync(
    db, user: User, access_token: str, refresh_token: str, target_date: date
) -> int:
    """
    Sync workouts for last 7 days (synchronous version).

    Returns:
        Number of workouts synced
    """
    # TODO: Implement sync version or refactor to use async properly
    # This is a placeholder that needs proper implementation

    logger.info(f"Syncing workouts for {user.id} around {target_date}")

    # For now, return 0 indicating work needed
    # In full implementation, would fetch from Garmin and save to DB
    return 0


@celery_app.task
def sync_all_users():
    """
    Sync Garmin data for all users with connected accounts.

    Scheduled to run daily at 6 AM via Celery Beat.
    """
    logger.info("Starting daily Garmin sync for all users")

    with get_sync_db_session() as db:
        # Find all users with Garmin connected
        users = (
            db.execute(select(User).where(User.garmin_access_token.isnot(None)))
            .scalars()
            .all()
        )

        logger.info(f"Found {len(users)} users with Garmin connected")

        # Queue individual sync jobs for each user
        yesterday = date.today() - timedelta(days=1)
        jobs_queued = 0

        for user in users:
            try:
                sync_user_garmin_data.delay(
                    user_id=str(user.id), sync_date=yesterday.isoformat()
                )
                jobs_queued += 1
            except Exception as e:
                logger.error(f"Failed to queue sync for user {user.id}: {e}")

        logger.info(f"Queued {jobs_queued} Garmin sync jobs")

        return {
            "status": "success",
            "total_users": len(users),
            "jobs_queued": jobs_queued,
        }
