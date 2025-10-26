"""
ACWR (Acute:Chronic Workload Ratio) Component Calculator.

Calculates recovery score component based on training load management.

Algorithm:
- Acute Load: 7-day average training stress score (TSS)
- Chronic Load: 28-day average training stress score (includes acute week)
- ACWR = Acute Load / Chronic Load

Scoring:
- 0.8-1.3 = 100 (sweet spot - optimal progression)
- 1.0 = 100 (balanced - maintaining fitness)
- 0.5-0.8 = 30-100 (detraining zone - interpolated)
- 1.3-1.5 = 100-30 (elevated - approaching overload, interpolated)
- <0.5 = 30 (significant detraining risk)
- 1.5-2.0 = 30-0 (high injury risk - interpolated)
- >2.0 = 0 (very high injury risk - dangerous spike)

This helps prevent:
- Overtraining injuries from excessive load spikes (ratio too high)
- Detraining from insufficient training volume (ratio too low)
- Optimizes progressive overload for fitness adaptation
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ACWRCalculator:
    """Calculator for ACWR component of recovery score."""

    # Days for acute and chronic load calculations
    ACUTE_DAYS = 7
    CHRONIC_DAYS = 28

    # Minimum days required for calculation
    MIN_DAYS_REQUIRED = CHRONIC_DAYS

    # Reference points for scoring (ACWR ratio, score)
    REFERENCE_POINTS = [
        (0.5, 30),  # 0.5 or below = 30 (significant detraining)
        (0.8, 100),  # 0.8 = 100 (low end of sweet spot)
        (1.3, 100),  # 1.3 = 100 (high end of sweet spot)
        (1.5, 30),  # 1.5 = 30 (high injury risk)
        (2.0, 0),  # 2.0 or above = 0 (very high injury risk)
    ]

    def calculate_component(self, workout_data: List[Dict[str, any]]) -> Optional[int]:
        """
        Calculate ACWR component score.

        Args:
            workout_data: List of dicts with workout information:
                - date: Date of workout
                - training_stress_score: TSS value (0-300+ typical range)

        Returns:
            Integer score 0-100, or None if insufficient data

        Example:
            workout_data = [
                {"date": date(2025, 10, 1), "training_stress_score": 100},
                {"date": date(2025, 10, 2), "training_stress_score": 80},
                ...
            ]
        """
        if not workout_data:
            logger.debug("No workout data provided")
            return None

        # Check for negative TSS values (invalid data)
        for entry in workout_data:
            tss = entry.get("training_stress_score")
            if tss is not None and tss < 0:
                logger.debug(f"Invalid negative TSS value: {tss}")
                return None

        # Calculate acute load (last 7 days average)
        acute_load = self._calculate_acute_load(workout_data)

        # Calculate chronic load (last 28 days average)
        chronic_load = self._calculate_chronic_load(workout_data)

        if acute_load is None or chronic_load is None:
            logger.debug("Insufficient data for ACWR calculation")
            return None

        if chronic_load == 0:
            logger.debug("Chronic load is zero - cannot calculate ACWR")
            return None

        # Calculate ACWR ratio
        acwr = acute_load / chronic_load

        # Calculate score using reference points
        score = self._interpolate_score(acwr)

        logger.debug(
            f"ACWR: acute={acute_load:.1f}, chronic={chronic_load:.1f}, "
            f"ratio={acwr:.2f}, score={score}"
        )

        return score

    def _calculate_acute_load(
        self, workout_data: List[Dict[str, any]]
    ) -> Optional[float]:
        """
        Calculate acute load (7-day average TSS).

        Args:
            workout_data: List of workout dicts

        Returns:
            Average TSS over last 7 days, or None if insufficient data
        """
        # Get most recent 7 days of data
        recent_data = (
            workout_data[-self.ACUTE_DAYS :]
            if len(workout_data) >= self.ACUTE_DAYS
            else workout_data
        )

        if len(recent_data) < self.ACUTE_DAYS:
            logger.debug(
                f"Insufficient data for acute load: {len(recent_data)} < {self.ACUTE_DAYS}"
            )
            return None

        # Extract TSS values (treat None as 0 - rest day)
        tss_values = []
        for entry in recent_data:
            tss = entry.get("training_stress_score")
            tss_values.append(tss if tss is not None else 0)

        # Calculate average
        avg_tss = sum(tss_values) / len(tss_values)

        return avg_tss

    def _calculate_chronic_load(
        self, workout_data: List[Dict[str, any]]
    ) -> Optional[float]:
        """
        Calculate chronic load (28-day average TSS).

        Args:
            workout_data: List of workout dicts

        Returns:
            Average TSS over last 28 days, or None if insufficient data
        """
        # Get most recent 28 days of data
        recent_data = (
            workout_data[-self.CHRONIC_DAYS :]
            if len(workout_data) >= self.CHRONIC_DAYS
            else workout_data
        )

        if len(recent_data) < self.CHRONIC_DAYS:
            logger.debug(
                f"Insufficient data for chronic load: {len(recent_data)} < {self.CHRONIC_DAYS}"
            )
            return None

        # Extract TSS values (treat None as 0 - rest day)
        tss_values = []
        for entry in recent_data:
            tss = entry.get("training_stress_score")
            tss_values.append(tss if tss is not None else 0)

        # Calculate average
        avg_tss = sum(tss_values) / len(tss_values)

        return avg_tss

    def _interpolate_score(self, acwr: float) -> int:
        """
        Interpolate score based on ACWR ratio.

        Uses linear interpolation between reference points.

        Args:
            acwr: Acute:Chronic Workload Ratio

        Returns:
            Integer score 0-100
        """
        # Handle values beyond reference range
        if acwr <= self.REFERENCE_POINTS[0][0]:
            # At or below 0.5 = 30 (significant detraining)
            return self.REFERENCE_POINTS[0][1]

        if acwr >= self.REFERENCE_POINTS[-1][0]:
            # At or above 2.0 = 0 (very high injury risk)
            return self.REFERENCE_POINTS[-1][1]

        # Find the two reference points to interpolate between
        for i in range(len(self.REFERENCE_POINTS) - 1):
            lower_acwr, lower_score = self.REFERENCE_POINTS[i]
            upper_acwr, upper_score = self.REFERENCE_POINTS[i + 1]

            if lower_acwr <= acwr <= upper_acwr:
                # Special case: 0.8-1.3 all score 100 (sweet spot)
                if lower_acwr == 0.8 and upper_acwr == 1.3:
                    return 100

                # Linear interpolation for other ranges
                range_size = upper_acwr - lower_acwr
                position = acwr - lower_acwr
                fraction = position / range_size

                # Interpolate score
                score_range = upper_score - lower_score
                score = lower_score + (score_range * fraction)

                return int(round(score))

        # Should never reach here due to bounds checking above
        logger.warning(f"Unexpected ACWR value: {acwr:.2f}")
        return 50  # Return neutral score as fallback
