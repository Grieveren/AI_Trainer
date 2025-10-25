"""HealthMetrics model for daily physiological data."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Integer, CheckConstraint, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


if TYPE_CHECKING:
    from src.models.user import User


class HealthMetrics(Base):
    """Daily snapshot of physiological data from Garmin devices.

    Collected overnight and used for recovery score calculation.
    Each user can have one metrics record per day.
    """

    __tablename__ = "health_metrics"

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique metric record ID",
    )

    # Foreign Key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner of this data",
    )

    # Date
    date: Mapped[date] = mapped_column(
        Date, nullable=False, doc="Calendar date for this snapshot"
    )

    # Health Metrics
    hrv_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Heart Rate Variability in milliseconds (20-150 typical)",
    )
    resting_hr: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Resting heart rate in beats per minute (40-80 typical)",
    )
    sleep_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Total sleep duration in minutes (480 = 8 hours)",
    )
    sleep_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Garmin's sleep quality score 0-100",
    )
    stress_level: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Average stress level 0-100 from Garmin",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this record was created",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="health_metrics")

    # Table constraints
    __table_args__ = (
        # Compound index for fast time-series queries
        Index("ix_health_metrics_user_date", "user_id", "date"),
        # Unique constraint to prevent duplicate dates per user
        Index("uq_health_metrics_user_date", "user_id", "date", unique=True),
        # Check constraints for valid ranges
        CheckConstraint(
            "sleep_score >= 0 AND sleep_score <= 100", name="ck_sleep_score_range"
        ),
        CheckConstraint(
            "stress_level >= 0 AND stress_level <= 100", name="ck_stress_level_range"
        ),
        CheckConstraint(
            "sleep_duration_minutes >= 0", name="ck_sleep_duration_positive"
        ),
    )

    def __repr__(self) -> str:
        """String representation of HealthMetrics."""
        return f"<HealthMetrics(user_id={self.user_id}, date={self.date})>"

    @property
    def is_complete(self) -> bool:
        """Check if all required metrics are present."""
        return all(
            [
                self.hrv_ms is not None,
                self.resting_hr is not None,
                self.sleep_duration_minutes is not None,
                self.sleep_score is not None,
                self.stress_level is not None,
            ]
        )
