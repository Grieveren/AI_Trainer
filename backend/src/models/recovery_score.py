"""RecoveryScore model for daily readiness assessment."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    Integer,
    Float,
    String,
    Text,
    CheckConstraint,
    ForeignKey,
    Index,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.health_metrics import HealthMetrics
    from src.models.workout_recommendation import WorkoutRecommendation


class RecoveryScore(Base):
    """Daily recovery score indicating athlete's readiness to train.

    Calculated from health metrics (HRV, HR, sleep, stress) and training history.
    Score ranges from 0-100 with color-coded interpretation:
    - 70-100 (Green): High readiness, ready for intense training
    - 40-69 (Yellow): Moderate readiness, steady-state training recommended
    - 0-39 (Red): Low readiness, recovery/rest recommended
    """

    __tablename__ = "recovery_scores"

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique recovery score record ID",
    )

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner of this recovery score",
    )
    health_metrics_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("health_metrics.id", ondelete="SET NULL"),
        nullable=True,
        doc="Link to the health metrics used for calculation",
    )

    # Date
    date: Mapped[date] = mapped_column(
        Date, nullable=False, doc="Calendar date for this recovery score"
    )

    # Recovery Score Components
    overall_score: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Overall recovery score 0-100"
    )
    hrv_component: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="HRV contribution to score (0-25)"
    )
    hr_component: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Resting HR contribution to score (0-25)"
    )
    sleep_component: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Sleep quality contribution to score (0-25)"
    )
    acwr_component: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Acute:Chronic Workload Ratio contribution (0-25)",
    )

    # Status Classification
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Color-coded status: green, yellow, red",
    )

    # Explanation
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Human-readable explanation of the score",
    )

    # Cache Metadata
    cached_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this score was calculated/cached",
    )
    cache_expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        doc="When this cached score expires (24 hours from calculation)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this record was created",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recovery_scores")
    health_metrics: Mapped[Optional["HealthMetrics"]] = relationship("HealthMetrics")
    workout_recommendation: Mapped[Optional["WorkoutRecommendation"]] = relationship(
        "WorkoutRecommendation",
        back_populates="recovery_score",
        uselist=False,
    )

    # Table constraints
    __table_args__ = (
        # Compound index for fast time-series queries
        Index("ix_recovery_scores_user_date", "user_id", "date"),
        # Unique constraint to ensure one score per user per day
        Index("uq_recovery_scores_user_date", "user_id", "date", unique=True),
        # Check constraints for valid ranges
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_overall_score_range",
        ),
        CheckConstraint(
            "status IN ('green', 'yellow', 'red')",
            name="ck_status_values",
        ),
    )

    def __repr__(self) -> str:
        """String representation of RecoveryScore."""
        return f"<RecoveryScore(user_id={self.user_id}, date={self.date}, score={self.overall_score}, status={self.status})>"

    @property
    def is_expired(self) -> bool:
        """Check if cached score has expired."""
        return datetime.utcnow() > self.cache_expires_at

    @property
    def readiness_level(self) -> str:
        """Get human-readable readiness level."""
        if self.overall_score >= 70:
            return "High readiness - ready for intense training"
        elif self.overall_score >= 40:
            return "Moderate readiness - steady-state training recommended"
        else:
            return "Low readiness - recovery/rest recommended"
