"""Database models module."""
# Import all models here so Alembic can discover them
from .user import User
from .health_metrics import HealthMetrics
from .workout import Workout
from .recovery_score import RecoveryScore
from .workout_recommendation import WorkoutRecommendation
from .insight import Insight
from .goal import Goal
from .training_plan import TrainingPlan
from .planned_workout import PlannedWorkout

__all__ = [
    "User",
    "HealthMetrics",
    "Workout",
    "RecoveryScore",
    "WorkoutRecommendation",
    "Insight",
    "Goal",
    "TrainingPlan",
    "PlannedWorkout",
]
