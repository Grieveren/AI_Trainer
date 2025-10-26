"""
Pydantic schemas for Recovery API responses.

Defines response models for:
- Recovery score data
- Component score breakdown
- Workout recommendations
- Calculation status
"""

from __future__ import annotations

from datetime import date as date_type, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ComponentScores(BaseModel):
    """Component score breakdown."""

    hrv_score: Optional[int] = Field(
        None, ge=0, le=100, description="HRV component score (0-100)"
    )
    hr_score: Optional[int] = Field(
        None, ge=0, le=100, description="Resting HR component score (0-100)"
    )
    sleep_score: Optional[int] = Field(
        None, ge=0, le=100, description="Sleep component score (0-100)"
    )
    acwr_score: Optional[int] = Field(
        None, ge=0, le=100, description="ACWR (training load) component score (0-100)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hrv_score": 85,
                "hr_score": 75,
                "sleep_score": 90,
                "acwr_score": 80,
            }
        }
    )


class WorkoutDetails(BaseModel):
    """Detailed workout structure."""

    duration: Optional[int] = Field(None, description="Workout duration in minutes")
    zones: Optional[List[int]] = Field(None, description="Heart rate zones")
    structure: Optional[str] = Field(None, description="Workout structure description")
    warmup: Optional[int] = Field(None, description="Warmup duration in minutes")
    cooldown: Optional[int] = Field(None, description="Cooldown duration in minutes")

    # Interval-specific fields
    work_duration: Optional[int] = Field(None, description="Work interval duration")
    rest_duration: Optional[int] = Field(None, description="Rest interval duration")
    num_intervals: Optional[int] = Field(None, description="Number of intervals")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "duration": 60,
                "zones": [4, 5],
                "structure": "8x 5min @ Z4-5 / 3min rest",
                "warmup": 10,
                "cooldown": 10,
                "work_duration": 5,
                "rest_duration": 3,
                "num_intervals": 8,
            }
        }
    )


class WorkoutRecommendation(BaseModel):
    """Workout recommendation based on recovery."""

    intensity: str = Field(..., description="Recommended intensity level")
    workout_type: str = Field(..., description="Recommended workout type")
    duration: Optional[int] = Field(None, description="Recommended duration in minutes")
    rationale: str = Field(..., description="Explanation for recommendation")
    details: Optional[WorkoutDetails] = Field(
        None, description="Detailed workout structure"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Safety warnings or cautions"
    )

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, v):
        """Validate intensity level."""
        valid_intensities = ["hard", "moderate", "rest", "recovery"]
        if v not in valid_intensities:
            raise ValueError(f"Intensity must be one of {valid_intensities}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intensity": "hard",
                "workout_type": "intervals",
                "duration": 75,
                "rationale": "Your recovery score of 85/100 indicates excellent recovery. You're ready for high-intensity training.",
                "details": {
                    "duration": 60,
                    "zones": [4, 5],
                    "structure": "8x 5min @ Z4-5 / 3min rest",
                },
                "warnings": [],
            }
        }
    )


class AlternativeWorkout(BaseModel):
    """Alternative workout option."""

    workout_type: str = Field(..., description="Alternative workout type")
    intensity: str = Field(..., description="Intensity level")
    duration: Optional[int] = Field(None, description="Duration in minutes")
    rationale: str = Field(..., description="Why this alternative is suitable")
    details: Optional[WorkoutDetails] = None


class RecoveryScoreResponse(BaseModel):
    """Recovery score response."""

    date: date_type = Field(..., description="Date of recovery score")
    overall_score: int = Field(
        ..., ge=0, le=100, description="Overall recovery score (0-100)"
    )
    status: str = Field(..., description="Recovery status color")
    components: ComponentScores = Field(..., description="Component score breakdown")
    explanation: str = Field(..., description="Human-readable explanation")
    cached_at: datetime = Field(..., description="When score was calculated")
    is_expired: bool = Field(..., description="Whether cached score has expired")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status color."""
        valid_statuses = ["green", "yellow", "red"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-10-24",
                "overall_score": 85,
                "status": "green",
                "components": {
                    "hrv_score": 90,
                    "hr_score": 85,
                    "sleep_score": 80,
                    "acwr_score": 85,
                },
                "explanation": "✓ Excellent recovery (Score: 85/100)\nYou're well-recovered and ready for high-intensity training.",
                "cached_at": "2025-10-24T06:30:00Z",
                "is_expired": False,
            }
        }
    )


class RecoveryWithRecommendation(RecoveryScoreResponse):
    """Recovery score with workout recommendation."""

    recommendation: WorkoutRecommendation = Field(
        ..., description="Workout recommendation based on recovery"
    )
    alternatives: List[AlternativeWorkout] = Field(
        default_factory=list, description="Alternative workout options"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-10-24",
                "overall_score": 85,
                "status": "green",
                "components": {
                    "hrv_score": 90,
                    "hr_score": 85,
                    "sleep_score": 80,
                    "acwr_score": 85,
                },
                "explanation": "Excellent recovery",
                "cached_at": "2025-10-24T06:30:00Z",
                "is_expired": False,
                "recommendation": {
                    "intensity": "hard",
                    "workout_type": "intervals",
                    "duration": 75,
                    "rationale": "You're well-recovered and ready for quality work",
                },
                "alternatives": [],
            }
        }
    )


class CalculationStatusResponse(BaseModel):
    """Recovery calculation status response."""

    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Calculation status")
    message: str = Field(..., description="Status message")
    estimated_completion: Optional[int] = Field(
        None, description="Estimated completion time in seconds"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc123-def456",
                "status": "pending",
                "message": "Recovery score calculation in progress",
                "estimated_completion": 5,
            }
        }
    )


class RecalculationResponse(BaseModel):
    """Recovery recalculation triggered response."""

    task_id: str = Field(..., description="Celery task ID")
    message: str = Field(..., description="Confirmation message")
    status: str = Field(default="triggered", description="Task status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task_12345",
                "message": "Recovery score recalculation triggered for 2025-10-24",
                "status": "triggered",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(..., description="Error message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": "Recovery score not found for the specified date"}
        }
    )
