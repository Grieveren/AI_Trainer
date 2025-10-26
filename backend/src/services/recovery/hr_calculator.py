"""
Resting Heart Rate Component Calculator.

Calculates recovery score component based on resting HR deviation from baseline.

Algorithm:
- Calculate 7-day rolling average resting HR (baseline)
- Compare today's HR to baseline percentage
- Score based on deviation (INVERSE relationship - lower is better):
  - -5% or more below average = 100 (excellent recovery)
  - At average (0% deviation) = 50 (normal)
  - +5% above average = 25 (elevated)
  - +10% or more above average = 0 (poor recovery)
- Linear interpolation between reference points
- Lower HR = better recovery (parasympathetic dominance)
- Elevated HR can indicate fatigue, illness, or overtraining
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class HRCalculator:
    """Calculator for resting heart rate component of recovery score."""

    # Minimum days with valid HR data required
    MIN_VALID_DAYS = 4

    # Days to include in rolling average
    ROLLING_WINDOW_DAYS = 7

    # Reference points for scoring (deviation percentage, score)
    # NOTE: INVERSE relationship - negative deviation is good, positive is bad
    REFERENCE_POINTS = [
        (-5, 100),  # -5% or more below = 100 (excellent)
        (0, 50),  # At average = 50 (normal)
        (5, 25),  # +5% above = 25 (elevated warning)
        (10, 0),  # +10% or more above = 0 (poor)
    ]

    def calculate_component(
        self, current_hr: Optional[int], historical_data: List[Dict[str, any]]
    ) -> Optional[int]:
        """
        Calculate resting HR component score.

        Args:
            current_hr: Today's resting HR in bpm
            historical_data: List of dicts with 'date' and 'resting_hr' keys
                            for past 7+ days

        Returns:
            Integer score 0-100, or None if insufficient data

        Example:
            historical_data = [
                {"date": date(2025, 10, 17), "resting_hr": 60},
                {"date": date(2025, 10, 18), "resting_hr": 58},
                ...
            ]
        """
        # Validate current HR
        if current_hr is None:
            logger.debug("Current HR is None")
            return None

        # Calculate 7-day rolling average
        avg_hr = self._calculate_rolling_average(historical_data)

        if avg_hr is None or avg_hr == 0:
            logger.debug("Insufficient historical HR data or zero average")
            return None

        # Calculate percentage deviation from average
        deviation_pct = ((current_hr - avg_hr) / avg_hr) * 100

        # Calculate score using reference points
        score = self._interpolate_score(deviation_pct)

        logger.debug(
            f"HR: current={current_hr}bpm, avg={avg_hr:.1f}bpm, "
            f"deviation={deviation_pct:.1f}%, score={score}"
        )

        return score

    def _calculate_rolling_average(
        self, historical_data: List[Dict[str, any]]
    ) -> Optional[float]:
        """
        Calculate 7-day rolling average resting HR from historical data.

        Args:
            historical_data: List of dicts with 'date' and 'resting_hr' keys

        Returns:
            Average resting HR in bpm, or None if insufficient valid data
        """
        if not historical_data:
            return None

        # Extract valid HR values (not None, most recent 7 days)
        valid_values = []

        for entry in historical_data:
            hr_value = entry.get("resting_hr")
            if hr_value is not None and hr_value > 0:
                valid_values.append(hr_value)

        # Take most recent 7 days
        valid_values = valid_values[-self.ROLLING_WINDOW_DAYS :]

        # Need at least MIN_VALID_DAYS for reliable average
        if len(valid_values) < self.MIN_VALID_DAYS:
            logger.debug(
                f"Insufficient valid HR days: {len(valid_values)} < {self.MIN_VALID_DAYS}"
            )
            return None

        # Calculate average
        avg = sum(valid_values) / len(valid_values)

        return avg

    def _interpolate_score(self, deviation_pct: float) -> int:
        """
        Interpolate score based on deviation percentage.

        Uses linear interpolation between reference points.
        INVERSE relationship: negative deviation (lower HR) = better score.

        Args:
            deviation_pct: Percentage deviation from baseline
                         (negative = below average/better,
                          positive = above average/worse)

        Returns:
            Integer score 0-100
        """
        # Handle values beyond reference range
        if deviation_pct <= self.REFERENCE_POINTS[0][0]:
            # At or below -5% = 100 (cap at max)
            return self.REFERENCE_POINTS[0][1]

        if deviation_pct >= self.REFERENCE_POINTS[-1][0]:
            # At or above +10% = 0 (floor at min)
            return self.REFERENCE_POINTS[-1][1]

        # Find the two reference points to interpolate between
        for i in range(len(self.REFERENCE_POINTS) - 1):
            lower_dev, lower_score = self.REFERENCE_POINTS[i]
            upper_dev, upper_score = self.REFERENCE_POINTS[i + 1]

            if lower_dev <= deviation_pct <= upper_dev:
                # Linear interpolation
                # Calculate position between lower and upper
                range_size = upper_dev - lower_dev
                position = deviation_pct - lower_dev
                fraction = position / range_size

                # Interpolate score
                score_range = upper_score - lower_score
                score = lower_score + (score_range * fraction)

                return int(round(score))

        # Should never reach here due to bounds checking above
        logger.warning(f"Unexpected deviation value: {deviation_pct}%")
        return 50  # Return neutral score as fallback
