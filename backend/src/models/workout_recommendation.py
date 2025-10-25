"""WorkoutRecommendation model for daily training suggestions."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Integer, String, Text, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


if TYPE_CHECKING:
    from src.models.user import User
    from src.models.recoveryscore import RecoveryScore


class WorkoutRecommendation(Base):
    """Daily workout recommendation based on recovery score.

    Generated automatically each day when recovery score is calculated.
    Provides intensity level, workout type, duration, and rationale.
    """

    __tablename__ = "workout_recommendations"

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique recommendation record ID",
    )

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner of this recommendation",
    )
    recovery_score_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recovery_scores.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        doc="Link to recovery score that generated this recommendation",
    )

    # Date
    date: Mapped[date] = mapped_column(
        Date, nullable=False, doc="Calendar date for this recommendation"
    )

    # Recommendation Details
    intensity_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Recommended intensity: high, moderate, low, rest",
    )
    workout_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Recommended workout type (e.g., interval_training, tempo_run, easy_run, active_recovery)",
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Recommended workout duration in minutes",
    )

    # Rationale
    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Human-readable explanation of why this workout is recommended",
    )

    # Alternative Options
    alternative_workout_1: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="First alternative workout type",
    )
    alternative_workout_2: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Second alternative workout type",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this recommendation was created",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="workout_recommendations"
    )
    recovery_score: Mapped["RecoveryScore"] = relationship(
        "RecoveryScore", back_populates="workout_recommendation"
    )

    # Table constraints
    __table_args__ = (
        # Compound index for fast time-series queries
        Index("ix_workout_recommendations_user_date", "user_id", "date"),
        # Unique constraint to ensure one recommendation per user per day
        Index("uq_workout_recommendations_user_date", "user_id", "date", unique=True),
    )

    def __repr__(self) -> str:
        """String representation of WorkoutRecommendation."""
        return f"<WorkoutRecommendation(user_id={self.user_id}, date={self.date}, intensity={self.intensity_level})>"

    @property
    def summary(self) -> str:
        """Get a one-line summary of the recommendation."""
        return f"{self.intensity_level.capitalize()} intensity - {self.workout_type.replace('_', ' ').title()} for {self.duration_minutes} minutes"
