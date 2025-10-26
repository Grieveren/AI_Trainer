"""Recovery and recommendations routes."""
from datetime import date as date_type, datetime, timedelta
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.models.user import User
from src.models.recovery_score import RecoveryScore
from src.models.workout import Workout
from src.api.middleware.auth import get_current_user
from src.api.schemas.recovery import (
    RecoveryScoreResponse,
    RecoveryWithRecommendation,
    RecalculationResponse,
    WorkoutRecommendation,
    AlternativeWorkout,
    WorkoutDetails,
    ComponentScores,
)
from src.services.recommendations import (
    IntensityMapper,
    TypeRecommender,
    RationaleService,
    AlternativesService,
    OvertrainingPrevention,
)
from src.jobs.recovery_score import calculate_user_recovery_score

router = APIRouter()

# Rate limiting for recalculation (in-memory, simple implementation)
_recalculation_cooldown: Dict[str, datetime] = {}
RECALCULATION_COOLDOWN_SECONDS = 300  # 5 minutes


@router.get("/{date}", response_model=RecoveryScoreResponse)
async def get_recovery_score(
    date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get recovery score for a specific date.

    Returns recovery score with component breakdown but without workout recommendation.
    Use GET /recovery/today for recommendation.
    """
    # Parse date
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Fetch recovery score
    result = db.execute(
        select(RecoveryScore).where(
            RecoveryScore.user_id == current_user.id, RecoveryScore.date == target_date
        )
    )
    recovery_score = result.scalar_one_or_none()

    if not recovery_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery score not found for {date}",
        )

    # Check if cached score is expired (24 hours)
    is_expired = False
    if recovery_score.cached_at:
        age = datetime.utcnow() - recovery_score.cached_at
        is_expired = age > timedelta(hours=24)

    # Build response
    return RecoveryScoreResponse(
        date=recovery_score.date,
        overall_score=recovery_score.overall_score,
        status=recovery_score.status,
        components=ComponentScores(
            hrv_score=recovery_score.hrv_score,
            hr_score=recovery_score.hr_score,
            sleep_score=recovery_score.sleep_score,
            acwr_score=recovery_score.acwr_score,
        ),
        explanation=recovery_score.explanation or "",
        cached_at=recovery_score.cached_at or datetime.utcnow(),
        is_expired=is_expired,
    )


@router.get("/today", response_model=RecoveryWithRecommendation)
async def get_recovery_today(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get today's recovery score with workout recommendation.

    Returns recovery score plus personalized workout recommendation and alternatives.
    """
    target_date = date_type.today()

    # Fetch recovery score
    result = db.execute(
        select(RecoveryScore).where(
            RecoveryScore.user_id == current_user.id, RecoveryScore.date == target_date
        )
    )
    recovery_score = result.scalar_one_or_none()

    if not recovery_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recovery score not found for today. Calculation may still be in progress.",
        )

    # Check if cached score is expired
    is_expired = False
    if recovery_score.cached_at:
        age = datetime.utcnow() - recovery_score.cached_at
        is_expired = age > timedelta(hours=24)

    # Generate workout recommendation
    recommendation = await _generate_workout_recommendation(
        recovery_score, str(current_user.id), db
    )

    # Generate alternatives
    alternatives = await _generate_alternatives(
        recovery_score, recommendation, str(current_user.id), db
    )

    # Build response
    return RecoveryWithRecommendation(
        date=recovery_score.date,
        overall_score=recovery_score.overall_score,
        status=recovery_score.status,
        components=ComponentScores(
            hrv_score=recovery_score.hrv_score,
            hr_score=recovery_score.hr_score,
            sleep_score=recovery_score.sleep_score,
            acwr_score=recovery_score.acwr_score,
        ),
        explanation=recovery_score.explanation or "",
        cached_at=recovery_score.cached_at or datetime.utcnow(),
        is_expired=is_expired,
        recommendation=recommendation,
        alternatives=alternatives,
    )


@router.post("/{date}/recalculate", response_model=RecalculationResponse)
async def recalculate_recovery_score(
    date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Force recalculation of recovery score for a specific date.

    Rate limited to prevent abuse (5 minute cooldown per user).
    Triggers background Celery task for calculation.
    """
    # Parse date
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    # Check rate limiting
    cooldown_key = f"{current_user.id}:{date}"
    if cooldown_key in _recalculation_cooldown:
        last_request = _recalculation_cooldown[cooldown_key]
        time_since = (datetime.utcnow() - last_request).total_seconds()
        if time_since < RECALCULATION_COOLDOWN_SECONDS:
            remaining = int(RECALCULATION_COOLDOWN_SECONDS - time_since)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Recalculation rate limit exceeded. Try again in {remaining} seconds.",
            )

    # Trigger recalculation
    task = calculate_user_recovery_score.apply_async(
        args=[str(current_user.id), date], countdown=0
    )

    # Update cooldown
    _recalculation_cooldown[cooldown_key] = datetime.utcnow()

    return RecalculationResponse(
        task_id=task.id,
        message=f"Recovery score recalculation triggered for {date}",
        status="triggered",
    )


# Helper functions


async def _generate_workout_recommendation(
    recovery_score: RecoveryScore, user_id: str, db: Session
) -> WorkoutRecommendation:
    """Generate personalized workout recommendation based on recovery."""
    # Initialize services
    intensity_mapper = IntensityMapper()
    type_recommender = TypeRecommender()
    rationale_service = RationaleService()
    overtraining_prevention = OvertrainingPrevention()

    # Prepare recovery data
    recovery_data = {
        "overall_score": recovery_score.overall_score,
        "status": recovery_score.status,
        "anomaly_severity": recovery_score.anomaly_severity or "none",
        "component_scores": {
            "hrv_score": recovery_score.hrv_score,
            "hr_score": recovery_score.hr_score,
            "sleep_score": recovery_score.sleep_score,
            "acwr_score": recovery_score.acwr_score,
        },
    }

    # Map intensity
    recommended_intensity = intensity_mapper.map_intensity(recovery_data)

    # Get recent workouts for context
    recent_workouts = _get_recent_workouts(user_id, db, days=7)

    # Check overtraining risk
    (
        final_intensity,
        overtraining_warning,
    ) = overtraining_prevention.check_overtraining_risk(
        recommended_intensity=recommended_intensity,
        recent_workouts=recent_workouts,
        recovery_history=None,  # TODO: Add recovery history query
    )

    # Select workout type
    workout_type = type_recommender.select_workout_type(
        intensity=final_intensity,
        sport="cycling",  # TODO: Get from user profile
        recent_workouts=recent_workouts,
    )

    # Get workout details
    workout_details = type_recommender.get_workout_details(
        workout_type=workout_type,
        intensity=final_intensity,
        sport="cycling",
        recovery_score=recovery_score.overall_score,
    )

    # Generate rationale
    recommendation_data = {
        "intensity": final_intensity,
        "workout_type": workout_type,
        "recovery_score": recovery_score.overall_score,
        "recovery_status": recovery_score.status,
        "component_scores": recovery_data["component_scores"],
        "warnings": recovery_score.anomaly_warnings or [],
        "recent_workouts": recent_workouts,
    }
    rationale = rationale_service.generate_rationale(recommendation_data)

    # Collect warnings
    warnings = []
    if overtraining_warning:
        warnings.append(overtraining_warning)
    if recovery_score.anomaly_warnings:
        warnings.extend(recovery_score.anomaly_warnings)

    return WorkoutRecommendation(
        intensity=final_intensity,
        workout_type=workout_type,
        duration=workout_details.get("total_duration", 60),
        rationale=rationale,
        details=WorkoutDetails(
            duration=workout_details.get("total_duration"),
            zones=workout_details.get("zones"),
            structure=workout_details.get("structure"),
            warmup=workout_details.get("warmup_duration"),
            cooldown=workout_details.get("cooldown_duration"),
            work_duration=workout_details.get("work_duration"),
            rest_duration=workout_details.get("rest_duration"),
            num_intervals=workout_details.get("num_intervals"),
        )
        if workout_details
        else None,
        warnings=warnings if warnings else None,
    )


async def _generate_alternatives(
    recovery_score: RecoveryScore,
    primary_recommendation: WorkoutRecommendation,
    user_id: str,
    db: Session,
) -> List[AlternativeWorkout]:
    """Generate alternative workout options."""
    alternatives_service = AlternativesService()

    # Prepare data
    primary_rec_dict = {
        "intensity": primary_recommendation.intensity,
        "workout_type": primary_recommendation.workout_type,
        "duration": primary_recommendation.duration,
        "sport": "cycling",  # TODO: Get from user profile
    }

    recovery_data = {
        "overall_score": recovery_score.overall_score,
        "status": recovery_score.status,
        "component_scores": {
            "hrv_score": recovery_score.hrv_score,
            "hr_score": recovery_score.hr_score,
            "sleep_score": recovery_score.sleep_score,
            "acwr_score": recovery_score.acwr_score,
        },
    }

    # Generate alternatives
    alternatives = alternatives_service.generate_alternatives(
        primary_recommendation=primary_rec_dict,
        recovery_data=recovery_data,
        constraints=None,  # TODO: Add user constraints
    )

    # Convert to schema
    return [
        AlternativeWorkout(
            workout_type=alt["workout_type"],
            intensity=alt["intensity"],
            duration=alt.get("duration"),
            rationale=alt["rationale"],
            details=WorkoutDetails(
                duration=alt["details"].get("total_duration"),
                zones=alt["details"].get("zones"),
                structure=alt["details"].get("structure"),
                warmup=alt["details"].get("warmup_duration"),
                cooldown=alt["details"].get("cooldown_duration"),
                work_duration=alt["details"].get("work_duration"),
                rest_duration=alt["details"].get("rest_duration"),
                num_intervals=alt["details"].get("num_intervals"),
            )
            if alt.get("details")
            else None,
        )
        for alt in alternatives
    ]


def _get_recent_workouts(user_id: str, db: Session, days: int = 7) -> List[Dict]:
    """Fetch recent workout history for context."""
    cutoff_date = date_type.today() - timedelta(days=days)

    result = db.execute(
        select(Workout)
        .where(Workout.user_id == user_id, Workout.workout_date >= cutoff_date)
        .order_by(Workout.workout_date.desc())
    )
    workouts = result.scalars().all()

    return [
        {
            "date": workout.workout_date,
            "workout_type": workout.workout_type,
            "intensity": workout.intensity,
            "training_stress_score": workout.training_stress_score,
        }
        for workout in workouts
    ]
