"""User model for authentication and Garmin account linking."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base

if TYPE_CHECKING:
    from src.models.health_metrics import HealthMetrics
    from src.models.workout import Workout
    from src.models.recovery_score import RecoveryScore
    from src.models.workout_recommendation import WorkoutRecommendation
    from src.models.insight import Insight
    from src.models.goal import Goal
    from src.models.training_plan import TrainingPlan


class User(Base):
    """User account with Garmin integration.

    Represents an athlete using the system. Stores authentication credentials,
    Garmin account linkage, and profile information.

    State Transitions:
        1. Created → Garmin Connected (when OAuth flow completes)
        2. Garmin Connected → Garmin Disconnected (when user revokes or token invalid)
        3. Garmin Disconnected → Garmin Connected (when user re-authorizes)
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique user identifier",
    )

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User's email address (used for authentication)",
    )
    hashed_password: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Bcrypt hashed password"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="User's full name"
    )

    # Account Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, doc="Whether account is active"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="Whether email is verified"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Account creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # Garmin Integration
    garmin_user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="Garmin account ID (null until connected)",
    )
    garmin_access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Encrypted OAuth access token for Garmin API",
    )
    garmin_refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Encrypted OAuth refresh token",
    )
    garmin_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="When current access token expires",
    )

    # Relationships (will be populated as models are created)
    health_metrics: Mapped[list["HealthMetrics"]] = relationship(
        "HealthMetrics",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    workouts: Mapped[list["Workout"]] = relationship(
        "Workout",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recovery_scores: Mapped[list["RecoveryScore"]] = relationship(
        "RecoveryScore",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    workout_recommendations: Mapped[list["WorkoutRecommendation"]] = relationship(
        "WorkoutRecommendation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    insights: Mapped[list["Insight"]] = relationship(
        "Insight",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    goals: Mapped[list["Goal"]] = relationship(
        "Goal",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    training_plans: Mapped[list["TrainingPlan"]] = relationship(
        "TrainingPlan",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def is_garmin_connected(self) -> bool:
        """Check if user has an active Garmin connection."""
        return (
            self.garmin_user_id is not None
            and self.garmin_access_token is not None
            and self.garmin_token_expires_at is not None
            and self.garmin_token_expires_at > datetime.utcnow()
        )
