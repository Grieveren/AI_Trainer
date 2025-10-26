"""
Sleep Component Calculator.

Calculates recovery score component based on sleep duration and quality.

Algorithm:
- Sleep Duration (60% weight):
  - 7-9 hours = 100 (optimal for most athletes)
  - 6 hours = 70 (sub-optimal but manageable)
  - 5 hours = 40 (poor, recovery compromised)
  - ≤4 hours = 0 (very poor, inadequate recovery)
  - ≥10 hours = 70 (excessive, may indicate fatigue)
  - Linear interpolation between points

- Sleep Quality (40% weight):
  - Uses Garmin sleep score (0-100) if available
  - Reflects sleep stages, restfulness, interruptions

- Combined Score:
  - If quality available: (duration_score * 0.6) + (quality_score * 0.4)
  - If quality missing: duration_score * 1.0 (100% weight on duration)
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SleepCalculator:
    """Calculator for sleep component of recovery score."""

    # Component weights
    DURATION_WEIGHT = 0.6
    QUALITY_WEIGHT = 0.4

    # Reference points for duration scoring (hours, score)
    DURATION_REFERENCE_POINTS = [
        (4, 0),  # ≤4 hours = 0 (very poor)
        (5, 40),  # 5 hours = 40 (poor)
        (6, 70),  # 6 hours = 70 (sub-optimal)
        (7, 100),  # 7 hours = 100 (optimal start)
        (9, 100),  # 9 hours = 100 (optimal end)
        (10, 70),  # 10 hours = 70 (excessive)
    ]

    def calculate_component(
        self, sleep_data: Optional[Dict[str, any]]
    ) -> Optional[int]:
        """
        Calculate sleep component score.

        Args:
            sleep_data: Dict with sleep information:
                - date: Date of sleep
                - total_sleep_seconds: Total sleep duration in seconds
                - sleep_quality_score: Optional Garmin sleep score (0-100)

        Returns:
            Integer score 0-100, or None if insufficient data

        Example:
            sleep_data = {
                "date": date(2025, 10, 24),
                "total_sleep_seconds": 28800,  # 8 hours
                "sleep_quality_score": 85
            }
        """
        if sleep_data is None:
            logger.debug("Sleep data is None")
            return None

        # Extract sleep duration
        total_seconds = sleep_data.get("total_sleep_seconds")

        if total_seconds is None or total_seconds < 0:
            logger.debug(f"Invalid sleep duration: {total_seconds}")
            return None

        # Convert seconds to hours
        sleep_hours = total_seconds / 3600

        # Calculate duration score
        duration_score = self._score_duration(sleep_hours)

        # Extract quality score if available
        quality_score = sleep_data.get("sleep_quality_score")

        # Calculate combined score
        if quality_score is not None:
            # Clamp quality score to 0-100 range
            quality_score = max(0, min(100, quality_score))

            # Weighted combination
            combined_score = (duration_score * self.DURATION_WEIGHT) + (
                quality_score * self.QUALITY_WEIGHT
            )

            logger.debug(
                f"Sleep: duration={sleep_hours:.1f}h (score={duration_score}), "
                f"quality={quality_score}, combined={combined_score:.1f}"
            )
        else:
            # No quality data - use duration only
            combined_score = duration_score

            logger.debug(
                f"Sleep: duration={sleep_hours:.1f}h (score={duration_score}), "
                f"no quality data"
            )

        return int(round(combined_score))

    def _score_duration(self, hours: float) -> int:
        """
        Score sleep duration using reference points.

        Args:
            hours: Sleep duration in hours

        Returns:
            Duration score 0-100
        """
        # Handle values beyond reference range
        if hours <= self.DURATION_REFERENCE_POINTS[0][0]:
            # ≤4 hours = 0
            return self.DURATION_REFERENCE_POINTS[0][1]

        if hours >= self.DURATION_REFERENCE_POINTS[-1][0]:
            # ≥10 hours = 70 (or continue declining)
            # For very excessive sleep (>10h), continue declining
            if hours > 10:
                # Decline linearly: 10h=70, 12h=50, 14h=30, 16h=0
                # Every 2 hours past 10 loses 20 points
                excess_hours = hours - 10
                penalty = (excess_hours / 2) * 20
                score = max(0, 70 - penalty)
                return int(round(score))
            return self.DURATION_REFERENCE_POINTS[-1][1]

        # Find the two reference points to interpolate between
        for i in range(len(self.DURATION_REFERENCE_POINTS) - 1):
            lower_hours, lower_score = self.DURATION_REFERENCE_POINTS[i]
            upper_hours, upper_score = self.DURATION_REFERENCE_POINTS[i + 1]

            if lower_hours <= hours <= upper_hours:
                # Special case: 7-9 hours all score 100 (optimal range)
                if lower_hours == 7 and upper_hours == 9:
                    return 100

                # Linear interpolation for other ranges
                range_size = upper_hours - lower_hours
                position = hours - lower_hours
                fraction = position / range_size

                # Interpolate score
                score_range = upper_score - lower_score
                score = lower_score + (score_range * fraction)

                return int(round(score))

        # Should never reach here due to bounds checking above
        logger.warning(f"Unexpected sleep duration: {hours}h")
        return 50  # Return neutral score as fallback
