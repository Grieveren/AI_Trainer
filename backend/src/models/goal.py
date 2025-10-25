"""Goal model for athlete objectives and targets."""

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
    from src.models.training_plan import TrainingPlan


class Goal(Base):
    """Athlete's training goal or objective.

    Defines targets for the athlete to achieve, such as completing a race,
    improving fitness, or maintaining consistency. Can be linked to training plans.
    """

    __tablename__ = "goals"

    # Primary Key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique goal record ID",
    )

    # Foreign Key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner of this goal",
    )

    # Goal Details
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, doc="Short title describing the goal"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Detailed description of the goal"
    )
    goal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of goal: race, fitness, consistency, recovery, custom",
    )

    # Timeline
    target_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, doc="Target completion date (e.g., race date)"
    )
    created_date: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today, doc="When goal was created"
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        doc="Goal status: active, completed, abandoned",
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="Whether goal has been achieved"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, doc="When goal was marked complete"
    )

    # Progress Tracking
    progress_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Notes about progress toward goal"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goals")
    training_plans: Mapped[list["TrainingPlan"]] = relationship(
        "TrainingPlan",
        back_populates="goal",
        cascade="all, delete-orphan",
    )

    # Table constraints
    __table_args__ = (
        # Index for filtering by user and status
        Index("ix_goals_user_status", "user_id", "status"),
        # Index for finding goals by target date
        Index("ix_goals_target_date", "target_date"),
    )

    def __repr__(self) -> str:
        """String representation of Goal."""
        return (
            f"<Goal(user_id={self.user_id}, title={self.title}, status={self.status})>"
        )

    @property
    def days_until_target(self) -> Optional[int]:
        """Calculate days remaining until target date."""
        if self.target_date:
            return (self.target_date - date.today()).days
        return None

    @property
    def is_overdue(self) -> bool:
        """Check if goal is past its target date and not completed."""
        if self.target_date and not self.is_completed:
            return date.today() > self.target_date
        return False
