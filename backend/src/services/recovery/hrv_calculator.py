"""
HRV (Heart Rate Variability) Component Calculator.

Calculates recovery score component based on HRV deviation from baseline.

Algorithm:
- Calculate 7-day rolling average HRV (baseline)
- Compare today's HRV to baseline percentage
- Score based on deviation:
  - +10% or more above average = 100 (excellent recovery)
  - At average (0% deviation) = 50 (normal)
  - -10% below average = 25 (below normal)
  - -20% or more below average = 0 (poor recovery)
- Linear interpolation between reference points
- Higher HRV = better recovery (parasympathetic dominance)
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class HRVCalculator:
    """Calculator for HRV component of recovery score."""

    # Minimum days with valid HRV data required
    MIN_VALID_DAYS = 4

    # Days to include in rolling average
    ROLLING_WINDOW_DAYS = 7

    # Reference points for scoring (deviation percentage, score)
    REFERENCE_POINTS = [
        (-20, 0),  # -20% or more below = 0 (very poor)
        (-10, 25),  # -10% below = 25 (poor)
        (0, 50),  # At average = 50 (normal)
        (10, 100),  # +10% or more above = 100 (excellent)
    ]

    def calculate_component(
        self, current_hrv: Optional[int], historical_data: List[Dict[str, any]]
    ) -> Optional[int]:
        """
        Calculate HRV component score.

        Args:
            current_hrv: Today's HRV in milliseconds
            historical_data: List of dicts with 'date' and 'hrv_ms' keys
                            for past 7+ days

        Returns:
            Integer score 0-100, or None if insufficient data

        Example:
            historical_data = [
                {"date": date(2025, 10, 17), "hrv_ms": 60},
                {"date": date(2025, 10, 18), "hrv_ms": 62},
                ...
            ]
        """
        # Validate current HRV
        if current_hrv is None:
            logger.debug("Current HRV is None")
            return None

        # Calculate 7-day rolling average
        avg_hrv = self._calculate_rolling_average(historical_data)

        if avg_hrv is None or avg_hrv == 0:
            logger.debug("Insufficient historical HRV data or zero average")
            return None

        # Calculate percentage deviation from average
        deviation_pct = ((current_hrv - avg_hrv) / avg_hrv) * 100

        # Calculate score using reference points
        score = self._interpolate_score(deviation_pct)

        logger.debug(
            f"HRV: current={current_hrv}ms, avg={avg_hrv:.1f}ms, "
            f"deviation={deviation_pct:.1f}%, score={score}"
        )

        return score

    def _calculate_rolling_average(
        self, historical_data: List[Dict[str, any]]
    ) -> Optional[float]:
        """
        Calculate 7-day rolling average HRV from historical data.

        Args:
            historical_data: List of dicts with 'date' and 'hrv_ms' keys

        Returns:
            Average HRV in ms, or None if insufficient valid data
        """
        if not historical_data:
            return None

        # Extract valid HRV values (not None, most recent 7 days)
        valid_values = []

        for entry in historical_data:
            hrv_value = entry.get("hrv_ms")
            if hrv_value is not None and hrv_value > 0:
                valid_values.append(hrv_value)

        # Take most recent 7 days
        valid_values = valid_values[-self.ROLLING_WINDOW_DAYS :]

        # Need at least MIN_VALID_DAYS for reliable average
        if len(valid_values) < self.MIN_VALID_DAYS:
            logger.debug(
                f"Insufficient valid HRV days: {len(valid_values)} < {self.MIN_VALID_DAYS}"
            )
            return None

        # Calculate average
        avg = sum(valid_values) / len(valid_values)

        return avg

    def _interpolate_score(self, deviation_pct: float) -> int:
        """
        Interpolate score based on deviation percentage.

        Uses linear interpolation between reference points.

        Args:
            deviation_pct: Percentage deviation from baseline
                         (positive = above average, negative = below)

        Returns:
            Integer score 0-100
        """
        # Handle values beyond reference range
        if deviation_pct >= self.REFERENCE_POINTS[-1][0]:
            # At or above +10% = 100 (cap at max)
            return self.REFERENCE_POINTS[-1][1]

        if deviation_pct <= self.REFERENCE_POINTS[0][0]:
            # At or below -20% = 0 (floor at min)
            return self.REFERENCE_POINTS[0][1]

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
