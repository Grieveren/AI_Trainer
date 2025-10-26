"""
Intensity Level Mapper.

Maps recovery score status to appropriate training intensity levels with
detailed guidance on zones, durations, and workout types.

Intensity Levels:
- Hard: High-intensity workouts (Zone 4-5, intervals, threshold, VO2max)
- Moderate: Steady-state aerobic (Zone 2-3, tempo, endurance)
- Rest/Recovery: Low intensity or complete rest (Zone 1, easy, rest)

Anomaly severity can downgrade intensity to prevent overtraining.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class IntensityMapper:
    """Maps recovery data to training intensity levels."""

    # Intensity mapping thresholds
    GREEN_THRESHOLD = 70  # Score >= 70 = green (hard intensity)
    YELLOW_THRESHOLD = 40  # Score >= 40 = yellow (moderate intensity)
    # Score < 40 = red (rest/recovery)

    def map_intensity(self, recovery_data: Optional[Dict[str, any]]) -> str:
        """
        Map recovery data to training intensity level.

        Args:
            recovery_data: Dict containing:
                - overall_score: Recovery score 0-100
                - status: Recovery status (green/yellow/red)
                - anomaly_severity: Anomaly severity (none/warning/critical)

        Returns:
            Intensity level: 'hard', 'moderate', or 'rest'
        """
        if recovery_data is None:
            logger.warning("No recovery data provided - defaulting to rest")
            return "rest"

        score = recovery_data.get("overall_score", 0)
        status = recovery_data.get("status", "red")
        anomaly_severity = recovery_data.get("anomaly_severity", "none")

        # Critical anomalies force rest regardless of score
        if anomaly_severity == "critical":
            return "rest"

        # Base intensity from score
        if score >= self.GREEN_THRESHOLD:
            base_intensity = "hard"
        elif score >= self.YELLOW_THRESHOLD:
            base_intensity = "moderate"
        else:
            base_intensity = "rest"

        # Anomaly warnings downgrade intensity
        if anomaly_severity == "warning":
            if base_intensity == "hard":
                return "moderate"  # Downgrade hard to moderate
            elif base_intensity == "moderate":
                return "recovery"  # Downgrade moderate to recovery

        return base_intensity

    def get_intensity_details(self, recovery_data: Dict[str, any]) -> Dict[str, any]:
        """
        Get detailed intensity information including zones and durations.

        Args:
            recovery_data: Recovery data dict

        Returns:
            Dict with intensity details:
                - intensity: Base intensity level
                - zones: Heart rate/power zones
                - duration_range: Recommended duration range (minutes)
                - workout_types: Appropriate workout types
                - rationale: Brief explanation
                - warnings: List of cautions if applicable
                - alternatives: Alternative intensity options
        """
        intensity = self.map_intensity(recovery_data)
        score = recovery_data.get("overall_score", 50)
        anomaly_severity = recovery_data.get("anomaly_severity", "none")

        if intensity == "hard":
            return self._get_hard_intensity_details(score, anomaly_severity)
        elif intensity == "moderate":
            return self._get_moderate_intensity_details(score, anomaly_severity)
        else:
            return self._get_rest_intensity_details(score, anomaly_severity)

    def _get_hard_intensity_details(
        self, score: int, anomaly_severity: str
    ) -> Dict[str, any]:
        """Get details for hard intensity workouts."""
        details = {
            "intensity": "hard",
            "zones": [4, 5],  # Zone 4 (threshold) and Zone 5 (VO2max)
            "duration_range": (45, 90),  # 45-90 minutes
            "workout_types": [
                "intervals",
                "threshold",
                "vo2max",
                "hills",
                "tempo_intervals",
            ],
            "rationale": (
                f"Your recovery score of {score}/100 indicates excellent recovery. "
                "You're ready for high-intensity training focusing on improving "
                "fitness and performance."
            ),
            "warnings": [],
            "alternatives": ["moderate", "recovery"],
        }

        # Add warnings if anomaly present (even if downgraded didn't trigger)
        if anomaly_severity == "warning":
            details["warnings"].append(
                "Minor recovery concerns detected. Consider slightly reducing "
                "workout volume or intensity if you feel fatigued."
            )

        return details

    def _get_moderate_intensity_details(
        self, score: int, anomaly_severity: str
    ) -> Dict[str, any]:
        """Get details for moderate intensity workouts."""
        details = {
            "intensity": "moderate",
            "zones": [2, 3],  # Zone 2 (aerobic) and Zone 3 (tempo)
            "duration_range": (60, 150),  # 1-2.5 hours
            "workout_types": [
                "tempo",
                "steady_state",
                "aerobic",
                "long_slow_distance",
                "endurance",
            ],
            "rationale": (
                f"Your recovery score of {score}/100 suggests moderate recovery. "
                "Focus on steady-state aerobic work to build fitness while "
                "allowing continued adaptation."
            ),
            "warnings": [],
            "alternatives": ["hard", "recovery"],
        }

        if anomaly_severity == "warning":
            details["warnings"].append(
                "Some recovery metrics are below normal. Err on the side of "
                "easier effort if in doubt."
            )
        elif anomaly_severity == "critical":
            details["warnings"].append(
                "Critical recovery warning detected. Consider resting instead."
            )

        return details

    def _get_rest_intensity_details(
        self, score: int, anomaly_severity: str
    ) -> Dict[str, any]:
        """Get details for rest/recovery intensity."""
        details = {
            "intensity": "rest",
            "zones": [1],  # Zone 1 (recovery)
            "duration_range": (0, 60),  # 0-60 minutes (or complete rest)
            "workout_types": [
                "recovery",
                "easy",
                "rest",
                "active_recovery",
                "mobility",
                "yoga",
            ],
            "rationale": (
                f"Your recovery score of {score}/100 indicates you need rest. "
                "Prioritize recovery to avoid overtraining and maximize long-term "
                "performance gains."
            ),
            "warnings": [],
            "alternatives": [],
        }

        if anomaly_severity == "critical":
            details["warnings"].append(
                "CRITICAL: Multiple warning signs detected. Complete rest is "
                "strongly recommended. Monitor for illness symptoms."
            )
            details["rationale"] = (
                f"Recovery score of {score}/100 with critical health warnings. "
                "Complete rest is essential. Do not train until metrics improve."
            )
            details["workout_types"] = ["rest"]
            details["duration_range"] = (0, 0)

        return details
