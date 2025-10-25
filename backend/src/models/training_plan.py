"""TrainingPlan model for multi-week structured training programs."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Index,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.goal import Goal
    from src.models.planned_workout import PlannedWorkout


class TrainingPlan(Base):
    """Multi-week structured training program.

    Defines a series of planned workouts organized into weeks to help
    the athlete achieve a specific goal. Adapts based on actual performance
    and recovery status.
    """

    __tablename__ = "training_plans"

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique training plan record ID",
    )

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner of this training plan",
    )
    goal_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
        doc="Goal this plan is designed to achieve",
    )

    # Plan Details
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, doc="Name of the training plan"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Detailed description of the plan"
    )
    plan_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of plan: race_prep, base_building, recovery, custom",
    )

    # Timeline
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False, doc="When plan starts"
    )
    end_date: Mapped[date] = mapped_column(Date, nullable=False, doc="When plan ends")
    duration_weeks: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Total number of weeks in the plan"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        doc="Plan status: active, completed, paused, cancelled",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, doc="Whether plan is currently active"
    )

    # Adaptation Tracking
    last_adapted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="When plan was last adjusted based on performance",
    )
    adaptation_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Notes about how plan has been adapted"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this plan was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="training_plans")
    goal: Mapped[Optional["Goal"]] = relationship(
        "Goal", back_populates="training_plans"
    )
    planned_workouts: Mapped[list["PlannedWorkout"]] = relationship(
        "PlannedWorkout",
        back_populates="training_plan",
        cascade="all, delete-orphan",
        order_by="PlannedWorkout.scheduled_date",
    )

    # Table constraints
    __table_args__ = (
        # Index for filtering by user and status
        Index("ix_training_plans_user_status", "user_id", "status"),
        # Index for finding active plans
        Index("ix_training_plans_active", "is_active"),
    )

    def __repr__(self) -> str:
        """String representation of TrainingPlan."""
        return f"<TrainingPlan(user_id={self.user_id}, name={self.name}, status={self.status})>"

    @property
    def days_remaining(self) -> int:
        """Calculate days remaining in plan."""
        return (self.end_date - date.today()).days

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage based on dates."""
        total_days = (self.end_date - self.start_date).days
        days_elapsed = (date.today() - self.start_date).days
        if total_days > 0:
            return min(100.0, max(0.0, (days_elapsed / total_days) * 100))
        return 0.0
