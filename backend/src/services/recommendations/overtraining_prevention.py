"""
Overtraining Prevention Logic (FR-015).

Analyzes training patterns and prevents dangerous overtraining scenarios by:
- Limiting consecutive hard training days
- Enforcing recovery after high training loads
- Detecting cumulative fatigue patterns
- Overriding recommendations when overtraining risk is high

Prevention Rules:
- Maximum 3 consecutive hard days
- Force rest day after 3 hard days in 4 days
- Downgrade intensity if 5+ hard days in 7 days
- Consider recovery score trends
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class OvertrainingPrevention:
    """Prevents overtraining by analyzing training patterns."""

    # Maximum consecutive hard days before forcing rest
    MAX_CONSECUTIVE_HARD_DAYS = 3

    # Maximum hard days in a rolling window
    MAX_HARD_DAYS_IN_WEEK = 5
    HARD_DAYS_WINDOW = 7

    # Recovery score decline threshold
    RECOVERY_DECLINE_THRESHOLD = -15  # 15-point drop

    def check_overtraining_risk(
        self,
        recommended_intensity: str,
        recent_workouts: List[Dict[str, any]],
        recovery_history: Optional[List[Dict[str, any]]] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Check for overtraining risk and adjust recommendation if needed.

        Args:
            recommended_intensity: Proposed intensity (hard/moderate/rest)
            recent_workouts: List of recent workouts with date, intensity
            recovery_history: Optional recovery score history

        Returns:
            Tuple of (adjusted_intensity, warning_message)
        """
        # Only check if recommending hard intensity
        if recommended_intensity != "hard":
            return recommended_intensity, None

        # Check 1: Consecutive hard days
        consecutive_risk, consecutive_warning = self._check_consecutive_hard(
            recent_workouts
        )
        if consecutive_risk:
            return "moderate", consecutive_warning

        # Check 2: Hard days in rolling window
        frequency_risk, frequency_warning = self._check_hard_frequency(recent_workouts)
        if frequency_risk:
            return "moderate", frequency_warning

        # Check 3: Recovery score declining trend
        if recovery_history:
            trend_risk, trend_warning = self._check_recovery_trend(recovery_history)
            if trend_risk:
                return "moderate", trend_warning

        # Check 4: Post-race recovery period
        race_risk, race_warning = self._check_post_race_recovery(recent_workouts)
        if race_risk:
            return "rest", race_warning

        # No overtraining risk detected
        return recommended_intensity, None

    def _check_consecutive_hard(
        self, recent_workouts: List[Dict[str, any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for excessive consecutive hard days.

        Returns:
            Tuple of (is_risk, warning_message)
        """
        if not recent_workouts:
            return False, None

        # Count consecutive hard days leading up to today
        consecutive_count = 0
        for workout in reversed(recent_workouts):
            workout_date = workout.get("date")
            intensity = workout.get("intensity")

            # Stop if we hit a gap or non-hard workout
            if not workout_date or intensity != "hard":
                break

            # Check if this workout was yesterday or continuing streak
            days_ago = (date.today() - workout_date).days
            if days_ago > consecutive_count:
                break  # Gap in training

            consecutive_count += 1

        if consecutive_count >= self.MAX_CONSECUTIVE_HARD_DAYS:
            return True, (
                f"⚠️ Overtraining Prevention: You've completed {consecutive_count} "
                f"consecutive hard training days. Forcing recovery day to prevent "
                f"overtraining and injury."
            )

        return False, None

    def _check_hard_frequency(
        self, recent_workouts: List[Dict[str, any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for too many hard days in rolling window.

        Returns:
            Tuple of (is_risk, warning_message)
        """
        if not recent_workouts:
            return False, None

        # Count hard days in last 7 days
        cutoff_date = date.today() - timedelta(days=self.HARD_DAYS_WINDOW)
        hard_count = 0

        for workout in recent_workouts:
            workout_date = workout.get("date")
            intensity = workout.get("intensity")

            if workout_date and workout_date >= cutoff_date and intensity == "hard":
                hard_count += 1

        if hard_count >= self.MAX_HARD_DAYS_IN_WEEK:
            return True, (
                f"⚠️ Overtraining Prevention: You've completed {hard_count} hard "
                f"days in the last {self.HARD_DAYS_WINDOW} days. Reducing intensity "
                f"to allow adequate recovery."
            )

        return False, None

    def _check_recovery_trend(
        self, recovery_history: List[Dict[str, any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for declining recovery score trend.

        Returns:
            Tuple of (is_risk, warning_message)
        """
        if len(recovery_history) < 3:
            return False, None

        # Compare recent average to older average
        recent_scores = [
            r["score"] for r in recovery_history[-3:] if r.get("score") is not None
        ]
        older_scores = [
            r["score"] for r in recovery_history[-7:-3] if r.get("score") is not None
        ]

        if not recent_scores or not older_scores:
            return False, None

        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)

        decline = recent_avg - older_avg

        if decline <= self.RECOVERY_DECLINE_THRESHOLD:
            return True, (
                f"⚠️ Overtraining Prevention: Your recovery score has declined "
                f"{abs(int(decline))} points over recent days. This suggests "
                f"cumulative fatigue. Reducing intensity to prevent overtraining."
            )

        return False, None

    def _check_post_race_recovery(
        self, recent_workouts: List[Dict[str, any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if athlete needs post-race recovery.

        Returns:
            Tuple of (is_risk, warning_message)
        """
        if not recent_workouts:
            return False, None

        # Look for recent races (last 5 days)
        for workout in recent_workouts:
            workout_date = workout.get("date")
            workout_type = workout.get("workout_type", "")

            if not workout_date:
                continue

            days_ago = (date.today() - workout_date).days

            if "race" in workout_type.lower() and days_ago <= 5:
                return True, (
                    f"⚠️ Post-Race Recovery: You raced {days_ago} day{'s' if days_ago != 1 else ''} ago. "
                    f"Your body needs recovery time after race efforts. Forcing rest day."
                )

        return False, None

    def get_recommended_rest_duration(self, overtraining_severity: str) -> int:
        """
        Get recommended rest duration based on overtraining severity.

        Args:
            overtraining_severity: Severity level (low/medium/high)

        Returns:
            Number of recommended rest days
        """
        severity_map = {
            "low": 1,  # 1 day rest
            "medium": 2,  # 2 days rest
            "high": 3,  # 3+ days rest
        }

        return severity_map.get(overtraining_severity, 1)

    def assess_overtraining_severity(
        self,
        recent_workouts: List[Dict[str, any]],
        recovery_history: Optional[List[Dict[str, any]]] = None,
    ) -> str:
        """
        Assess overall overtraining severity.

        Args:
            recent_workouts: Recent workout history
            recovery_history: Optional recovery score history

        Returns:
            Severity level: 'none', 'low', 'medium', 'high'
        """
        risk_factors = 0

        # Factor 1: Consecutive hard days
        consecutive_risk, _ = self._check_consecutive_hard(recent_workouts)
        if consecutive_risk:
            risk_factors += 2

        # Factor 2: Hard day frequency
        frequency_risk, _ = self._check_hard_frequency(recent_workouts)
        if frequency_risk:
            risk_factors += 2

        # Factor 3: Recovery trend
        if recovery_history:
            trend_risk, _ = self._check_recovery_trend(recovery_history)
            if trend_risk:
                risk_factors += 3  # Recovery decline is serious

        # Classify severity
        if risk_factors == 0:
            return "none"
        elif risk_factors <= 2:
            return "low"
        elif risk_factors <= 4:
            return "medium"
        else:
            return "high"
