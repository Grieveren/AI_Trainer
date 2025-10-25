"""Workout model for training session tracking."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Integer, Float, String, Text, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


if TYPE_CHECKING:
    from src.models.user import User
    from src.models.plannedworkout import PlannedWorkout


class Workout(Base):
    """Training session record from Garmin or manual entry.

    Tracks workout details including type, duration, intensity, and training load.
    Can be linked to a PlannedWorkout for training plan adherence tracking.
    """

    __tablename__ = "workouts"

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique workout record ID",
    )

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner of this workout",
    )
    planned_workout_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("planned_workouts.id", ondelete="SET NULL"),
        nullable=True,
        doc="Link to planned workout if this completes a plan",
    )

    # Workout Details
    date: Mapped[date] = mapped_column(
        Date, nullable=False, doc="Calendar date when workout occurred"
    )
    workout_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of workout (e.g., run, bike, swim, strength)",
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Total workout duration in minutes"
    )

    # Optional Metrics
    distance_km: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Distance covered in kilometers"
    )
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Average heart rate during workout (bpm)"
    )
    max_heart_rate: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="Maximum heart rate during workout (bpm)"
    )
    training_load: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Calculated training stress/load from Garmin (0-1000)",
    )
    perceived_exertion: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Self-reported RPE (Rate of Perceived Exertion) 1-10",
    )

    # Metadata
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="garmin",
        doc="Source of workout data (garmin or manual)",
    )
    garmin_activity_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        doc="Garmin's unique activity ID for synced workouts",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="User notes about the workout"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this record was created",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workouts")
    planned_workout: Mapped[Optional["PlannedWorkout"]] = relationship(
        "PlannedWorkout", back_populates="completed_workout"
    )

    # Table constraints
    __table_args__ = (
        # Compound index for fast time-series queries
        Index("ix_workouts_user_date", "user_id", "date"),
        # Index for Garmin activity lookups
        Index("ix_workouts_garmin_activity", "garmin_activity_id", unique=True),
    )

    def __repr__(self) -> str:
        """String representation of Workout."""
        return f"<Workout(user_id={self.user_id}, date={self.date}, type={self.workout_type})>"

    @property
    def pace_per_km(self) -> Optional[float]:
        """Calculate pace in minutes per kilometer."""
        if self.distance_km and self.distance_km > 0:
            return self.duration_minutes / self.distance_km
        return None
