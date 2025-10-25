"""PlannedWorkout model for scheduled training sessions within a plan."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    Integer,
    Float,
    String,
    Text,
    Boolean,
    ForeignKey,
    Index,
    TIMESTAMP,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base

if TYPE_CHECKING:
    from src.models.training_plan import TrainingPlan
    from src.models.workout import Workout


class PlannedWorkout(Base):
    """Scheduled workout within a training plan.

    Represents a workout that is planned for a specific date as part of a
    training plan. Can be linked to an actual Workout when completed.
    """

    __tablename__ = "planned_workouts"

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique planned workout record ID",
    )

    # Foreign Keys
    training_plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Training plan this workout belongs to",
    )

    # Scheduled Details
    scheduled_date: Mapped[date] = mapped_column(
        Date, nullable=False, doc="Date when this workout is scheduled"
    )
    week_number: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Week number within the training plan (1-based)"
    )
    day_of_week: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Day of week (0=Monday, 6=Sunday)"
    )

    # Workout Prescription
    workout_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of workout (e.g., easy_run, tempo, intervals, rest)",
    )
    target_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Target duration in minutes"
    )
    target_distance_km: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Target distance in kilometers"
    )
    intensity_guidance: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Intensity guidance (e.g., easy, moderate, hard, race_pace)",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Detailed workout description/instructions"
    )

    # Completion Status
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="Whether workout has been completed"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, doc="When workout was marked complete"
    )
    skipped: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether workout was intentionally skipped",
    )
    skip_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Reason for skipping workout"
    )

    # Adaptation Tracking
    was_adapted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this workout was adapted from original plan",
    )
    adaptation_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Reason for adapting the workout"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this planned workout was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # Relationships
    training_plan: Mapped["TrainingPlan"] = relationship(
        "TrainingPlan", back_populates="planned_workouts"
    )
    completed_workout: Mapped[Optional["Workout"]] = relationship(
        "Workout",
        back_populates="planned_workout",
        uselist=False,
    )

    # Table constraints
    __table_args__ = (
        # Compound index for fast queries by plan and date
        Index("ix_planned_workouts_plan_date", "training_plan_id", "scheduled_date"),
        # Index for finding incomplete workouts
        Index("ix_planned_workouts_completion", "is_completed"),
    )

    def __repr__(self) -> str:
        """String representation of PlannedWorkout."""
        status = (
            "completed"
            if self.is_completed
            else "skipped"
            if self.skipped
            else "pending"
        )
        return f"<PlannedWorkout(plan_id={self.training_plan_id}, date={self.scheduled_date}, type={self.workout_type}, status={status})>"

    @property
    def is_overdue(self) -> bool:
        """Check if workout is past its scheduled date and not completed."""
        if not self.is_completed and not self.skipped:
            return date.today() > self.scheduled_date
        return False

    @property
    def status(self) -> str:
        """Get human-readable status."""
        if self.is_completed:
            return "completed"
        elif self.skipped:
            return "skipped"
        elif self.is_overdue:
            return "overdue"
        elif self.scheduled_date == date.today():
            return "today"
        elif self.scheduled_date > date.today():
            return "upcoming"
        return "pending"
