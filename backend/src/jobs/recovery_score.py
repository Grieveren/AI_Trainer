"""
Recovery Score Background Jobs.

Calculates daily recovery scores for users based on:
- HRV (40% weight)
- Resting HR (30% weight)
- Sleep (20% weight)
- ACWR training load (10% weight)

Runs daily via Celery Beat to update recovery scores.
"""

from datetime import date, timedelta
from typing import Optional, Dict, List
import logging

from sqlalchemy import select

from src.celery_app import celery_app
from src.database.connection import get_sync_db_session
from src.models.user import User
from src.models.health_metrics import HealthMetrics
from src.models.workout import Workout
from src.models.recovery_score import RecoveryScore
from src.services.recovery import (
    HRVCalculator,
    HRCalculator,
    SleepCalculator,
    ACWRCalculator,
    RecoveryAggregator,
    AnomalyDetector,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    name="calculate_user_recovery_score",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def calculate_user_recovery_score(
    self, user_id: str, target_date: Optional[str] = None
):
    """
    Calculate recovery score for a specific user.

    This task:
    1. Fetches health metrics (HRV, HR, sleep) for target date
    2. Fetches historical health data (7-28 days) for baselines
    3. Fetches workout history for ACWR calculation
    4. Calculates each component score
    5. Aggregates final recovery score
    6. Stores result in database

    Args:
        user_id: User UUID
        target_date: Date to calculate for (ISO format YYYY-MM-DD),
                    defaults to today

    Returns:
        Dict with recovery score info or error message
    """
    try:
        # Parse target date
        if target_date:
            calc_date = date.fromisoformat(target_date)
        else:
            calc_date = date.today()

        logger.info(f"Calculating recovery score for user {user_id} on {calc_date}")

        with get_sync_db_session() as db:
            # Verify user exists
            user = db.execute(
                select(User).where(User.id == user_id)
            ).scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                return {"error": "User not found"}

            # Fetch today's health metrics
            today_metrics = db.execute(
                select(HealthMetrics).where(
                    HealthMetrics.user_id == user_id, HealthMetrics.date == calc_date
                )
            ).scalar_one_or_none()

            if not today_metrics:
                logger.warning(f"No health metrics for user {user_id} on {calc_date}")
                return {"error": "No health metrics available for target date"}

            # Fetch historical health metrics (last 7 days for rolling averages)
            start_date = calc_date - timedelta(days=7)
            historical_metrics = (
                db.execute(
                    select(HealthMetrics)
                    .where(
                        HealthMetrics.user_id == user_id,
                        HealthMetrics.date >= start_date,
                        HealthMetrics.date < calc_date,
                    )
                    .order_by(HealthMetrics.date)
                )
                .scalars()
                .all()
            )

            # Fetch workout history (last 28 days for ACWR)
            workout_start_date = calc_date - timedelta(days=28)
            workout_history = (
                db.execute(
                    select(Workout)
                    .where(
                        Workout.user_id == user_id,
                        Workout.date >= workout_start_date,
                        Workout.date <= calc_date,
                    )
                    .order_by(Workout.date)
                )
                .scalars()
                .all()
            )

            # Calculate component scores
            component_scores = _calculate_components(
                today_metrics=today_metrics,
                historical_metrics=historical_metrics,
                workout_history=workout_history,
            )

            # Aggregate final score
            aggregator = RecoveryAggregator()
            final_score = aggregator.calculate_final_score(component_scores)

            if final_score is None:
                logger.warning(
                    f"Could not calculate recovery score for user {user_id} - insufficient data"
                )
                return {"error": "Insufficient data for recovery score calculation"}

            # Detect anomalies and generate warnings
            detector = AnomalyDetector()
            today_metrics_dict = {
                "hrv_ms": today_metrics.hrv_ms,
                "resting_hr": today_metrics.resting_hr,
                "total_sleep_seconds": today_metrics.total_sleep_seconds,
            }
            historical_metrics_dict = [
                {"hrv_ms": m.hrv_ms, "resting_hr": m.resting_hr, "date": m.date}
                for m in historical_metrics
            ]
            anomaly_result = detector.detect_anomalies(
                today_metrics=today_metrics_dict,
                historical_metrics=historical_metrics_dict,
                component_scores=component_scores,
            )

            # Generate explanation text
            explanation = _generate_explanation(
                final_score=final_score,
                component_scores=component_scores,
                anomaly_result=anomaly_result,
            )

            # Determine status (green/yellow/red)
            status = _determine_status(final_score, anomaly_result)

            # Calculate cache expiration (24 hours from now)
            from datetime import datetime, timedelta

            cached_at = datetime.utcnow()
            cache_expires_at = cached_at + timedelta(hours=24)

            # Check for existing record
            existing = db.execute(
                select(RecoveryScore).where(
                    RecoveryScore.user_id == user_id, RecoveryScore.date == calc_date
                )
            ).scalar_one_or_none()

            if existing:
                # Update existing record
                existing.overall_score = final_score
                existing.hrv_component = component_scores.get("hrv_score")
                existing.hr_component = component_scores.get("hr_score")
                existing.sleep_component = component_scores.get("sleep_score")
                existing.acwr_component = component_scores.get("acwr_score")
                existing.status = status
                existing.explanation = explanation
                existing.cached_at = cached_at
                existing.cache_expires_at = cache_expires_at
            else:
                # Create new record
                recovery_score = RecoveryScore(
                    user_id=user_id,
                    date=calc_date,
                    overall_score=final_score,
                    hrv_component=component_scores.get("hrv_score"),
                    hr_component=component_scores.get("hr_score"),
                    sleep_component=component_scores.get("sleep_score"),
                    acwr_component=component_scores.get("acwr_score"),
                    status=status,
                    explanation=explanation,
                    cached_at=cached_at,
                    cache_expires_at=cache_expires_at,
                )
                db.add(recovery_score)

            db.commit()

            logger.info(
                f"Recovery score calculated for user {user_id}: {final_score} "
                f"(HRV={component_scores.get('hrv_score')}, "
                f"HR={component_scores.get('hr_score')}, "
                f"Sleep={component_scores.get('sleep_score')}, "
                f"ACWR={component_scores.get('acwr_score')})"
            )

            return {
                "user_id": user_id,
                "date": str(calc_date),
                "score": final_score,
                "components": component_scores,
            }

    except Exception as e:
        logger.error(f"Error calculating recovery score for user {user_id}: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(name="calculate_all_users_recovery_scores")
def calculate_all_users_recovery_scores():
    """
    Calculate recovery scores for all active users.

    This task is scheduled to run daily (via Celery Beat at 6:30 AM).
    It triggers individual calculation tasks for each user.

    Returns:
        Dict with summary of tasks triggered
    """
    try:
        with get_sync_db_session() as db:
            # Get all active users with Garmin connected
            users = (
                db.execute(
                    select(User).where(
                        User.is_active == True, User.garmin_access_token.isnot(None)
                    )
                )
                .scalars()
                .all()
            )

            logger.info(f"Starting recovery score calculation for {len(users)} users")

            # Trigger individual tasks for each user
            task_ids = []
            for user in users:
                task = calculate_user_recovery_score.delay(str(user.id))
                task_ids.append(task.id)

            return {
                "total_users": len(users),
                "tasks_triggered": len(task_ids),
                "task_ids": task_ids,
            }

    except Exception as e:
        logger.error(f"Error triggering recovery score calculations: {str(e)}")
        return {"error": str(e)}


def _calculate_components(
    today_metrics: HealthMetrics,
    historical_metrics: List[HealthMetrics],
    workout_history: List[Workout],
) -> Dict[str, Optional[int]]:
    """
    Calculate all component scores.

    Args:
        today_metrics: Today's health metrics
        historical_metrics: Historical health metrics (7+ days)
        workout_history: Workout history (28+ days)

    Returns:
        Dict with component scores (may contain None for missing components)
    """
    components = {}

    # HRV Component (40% weight)
    hrv_calc = HRVCalculator()
    historical_hrv = [{"date": m.date, "hrv_ms": m.hrv_ms} for m in historical_metrics]
    components["hrv_score"] = hrv_calc.calculate_component(
        current_hrv=today_metrics.hrv_ms, historical_data=historical_hrv
    )

    # HR Component (30% weight)
    hr_calc = HRCalculator()
    historical_hr = [
        {"date": m.date, "resting_hr": m.resting_hr} for m in historical_metrics
    ]
    components["hr_score"] = hr_calc.calculate_component(
        current_hr=today_metrics.resting_hr, historical_data=historical_hr
    )

    # Sleep Component (20% weight)
    sleep_calc = SleepCalculator()
    sleep_data = {
        "date": today_metrics.date,
        "total_sleep_seconds": today_metrics.total_sleep_seconds,
        "sleep_quality_score": today_metrics.sleep_quality_score,
    }
    components["sleep_score"] = sleep_calc.calculate_component(sleep_data)

    # ACWR Component (10% weight)
    acwr_calc = ACWRCalculator()
    workout_data = [
        {"date": w.date, "training_stress_score": w.training_stress_score}
        for w in workout_history
    ]
    components["acwr_score"] = acwr_calc.calculate_component(workout_data)

    return components


def _generate_explanation(
    final_score: int,
    component_scores: Dict[str, Optional[int]],
    anomaly_result: Dict[str, any],
) -> str:
    """
    Generate human-readable explanation of recovery score.

    Args:
        final_score: Overall recovery score
        component_scores: Individual component scores
        anomaly_result: Anomaly detection results

    Returns:
        Explanation text for the recovery score
    """
    lines = []

    # Overall score interpretation
    if final_score >= 90:
        lines.append(f"✓ Excellent recovery (Score: {final_score}/100)")
        lines.append(
            "You're well-recovered and ready for high-intensity training or racing."
        )
    elif final_score >= 70:
        lines.append(f"✓ Good recovery (Score: {final_score}/100)")
        lines.append("You're recovered and ready for normal training loads.")
    elif final_score >= 50:
        lines.append(f"⚠ Moderate recovery (Score: {final_score}/100)")
        lines.append("Consider easier training or active recovery today.")
    elif final_score >= 30:
        lines.append(f"⚠ Poor recovery (Score: {final_score}/100)")
        lines.append("Light activity or rest is recommended to avoid overtraining.")
    else:
        lines.append(f"✗ Critical - Low recovery (Score: {final_score}/100)")
        lines.append("Complete rest is strongly recommended.")

    # Component breakdown
    lines.append("\nComponent Scores:")
    if component_scores.get("hrv_score") is not None:
        lines.append(f"  • HRV: {component_scores['hrv_score']}/100 (40% weight)")
    if component_scores.get("hr_score") is not None:
        lines.append(f"  • Resting HR: {component_scores['hr_score']}/100 (30% weight)")
    if component_scores.get("sleep_score") is not None:
        lines.append(f"  • Sleep: {component_scores['sleep_score']}/100 (20% weight)")
    if component_scores.get("acwr_score") is not None:
        lines.append(
            f"  • Training Load: {component_scores['acwr_score']}/100 (10% weight)"
        )

    # Anomaly warnings
    if anomaly_result.get("has_anomalies"):
        lines.append("\n⚠ HEALTH ALERTS:")
        for warning in anomaly_result.get("warnings", []):
            lines.append(f"  • {warning}")

    # Recommendations
    if anomaly_result.get("recommendations"):
        lines.append("\nRecommendations:")
        for rec in anomaly_result.get("recommendations", []):
            lines.append(f"  • {rec}")

    return "\n".join(lines)


def _determine_status(final_score: int, anomaly_result: Dict[str, any]) -> str:
    """
    Determine status color (green/yellow/red) from score and anomalies.

    Args:
        final_score: Overall recovery score
        anomaly_result: Anomaly detection results

    Returns:
        Status: 'green', 'yellow', or 'red'
    """
    # Critical anomalies override score-based status
    if anomaly_result.get("severity") == "critical":
        return "red"

    # Score-based status
    if final_score >= 70:
        # But downgrade to yellow if there are warnings
        if anomaly_result.get("severity") == "warning":
            return "yellow"
        return "green"
    elif final_score >= 40:
        return "yellow"
    else:
        return "red"
