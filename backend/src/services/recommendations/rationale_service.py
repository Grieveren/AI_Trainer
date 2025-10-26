"""
Workout Recommendation Rationale Generator.

Generates human-readable explanations for workout recommendations by analyzing:
- Recovery score and component breakdown
- Recent training history patterns
- Anomaly warnings and health concerns
- Periodization context
- Training progression

Rationale should be:
- Clear and concise (2-4 sentences)
- Explain WHY this recommendation was made
- Connect to recovery data
- Include safety warnings when needed
- Motivate appropriately (encouraging when ready, supportive when resting)
"""

from typing import Dict, List, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)


class RationaleService:
    """Generates explanatory rationale for workout recommendations."""

    def generate_rationale(self, recommendation_data: Dict[str, any]) -> str:
        """
        Generate comprehensive rationale for workout recommendation.

        Args:
            recommendation_data: Dict containing:
                - intensity: Recommended intensity level
                - workout_type: Recommended workout type
                - recovery_score: Overall recovery score
                - recovery_status: Recovery status (green/yellow/red)
                - component_scores: Optional component breakdown
                - anomaly_warnings: Optional list of warnings
                - recent_workouts: Optional recent workout history
                - phase: Optional periodization phase
                - days_until_race: Optional days until race
                - anomaly_severity: Optional severity level

        Returns:
            Human-readable rationale string
        """
        intensity = recommendation_data.get("intensity", "moderate")
        workout_type = recommendation_data.get("workout_type", "")
        score = recommendation_data.get("recovery_score", 50)
        status = recommendation_data.get("recovery_status", "yellow")

        # Build rationale components
        parts = []

        # 1. Opening statement based on recovery
        parts.append(self._generate_opening(score, status, intensity))

        # 2. Recovery component explanation (if available)
        component_explanation = self._explain_components(
            recommendation_data.get("component_scores")
        )
        if component_explanation:
            parts.append(component_explanation)

        # 3. Anomaly warnings (if any)
        anomaly_explanation = self._explain_anomalies(
            recommendation_data.get("anomaly_warnings", []),
            recommendation_data.get("anomaly_severity"),
        )
        if anomaly_explanation:
            parts.append(anomaly_explanation)

        # 4. Training context (if available)
        context_explanation = self._explain_training_context(
            recommendation_data.get("recent_workouts", []),
            recommendation_data.get("phase"),
            recommendation_data.get("days_until_race"),
        )
        if context_explanation:
            parts.append(context_explanation)

        # 5. Closing recommendation
        parts.append(self._generate_closing(intensity, workout_type, score))

        return " ".join(parts)

    def _generate_opening(self, score: int, status: str, intensity: str) -> str:
        """Generate opening statement based on recovery status."""
        if score >= 90:
            return (
                f"Excellent recovery (Score: {score}/100)! "
                "You're well-recovered and ready for high-intensity training."
            )
        elif score >= 70:
            return (
                f"Good recovery (Score: {score}/100). "
                "Your body is ready for quality training."
            )
        elif score >= 50:
            return (
                f"Moderate recovery (Score: {score}/100). "
                "Your body needs a more conservative approach today."
            )
        elif score >= 30:
            return (
                f"Low recovery (Score: {score}/100). "
                "Your body is showing signs of fatigue and needs easier training."
            )
        else:
            return (
                f"Very low recovery (Score: {score}/100). "
                "Your body urgently needs rest to avoid overtraining."
            )

    def _explain_components(
        self, component_scores: Optional[Dict[str, Optional[int]]]
    ) -> str:
        """Explain key component scores affecting recommendation."""
        if not component_scores:
            return ""

        explanations = []

        # Check for concerning components
        hrv_score = component_scores.get("hrv_score")
        if hrv_score is not None and hrv_score < 30:
            explanations.append(
                f"Your HRV is significantly suppressed (Score: {hrv_score}/100), "
                "indicating your nervous system needs recovery."
            )

        hr_score = component_scores.get("hr_score")
        if hr_score is not None and hr_score < 30:
            explanations.append(
                f"Your resting heart rate is elevated (Score: {hr_score}/100), "
                "which can indicate stress, fatigue, or illness."
            )

        sleep_score = component_scores.get("sleep_score")
        if sleep_score is not None and sleep_score < 40:
            explanations.append(
                f"Poor sleep quality (Score: {sleep_score}/100) is limiting your recovery capacity."
            )

        acwr_score = component_scores.get("acwr_score")
        if acwr_score is not None and acwr_score < 30:
            explanations.append(
                f"Your training load ratio (Score: {acwr_score}/100) indicates "
                "high injury risk from rapid training increases."
            )

        return " ".join(explanations)

    def _explain_anomalies(self, warnings: List[str], severity: Optional[str]) -> str:
        """Explain anomaly warnings."""
        if not warnings:
            return ""

        if severity == "critical":
            return (
                "⚠️ CRITICAL WARNING: " + warnings[0] + " "
                "Training is strongly discouraged until metrics improve."
            )
        elif severity == "warning" and warnings:
            return "⚠️ " + warnings[0]

        return ""

    def _explain_training_context(
        self,
        recent_workouts: List[Dict[str, any]],
        phase: Optional[str],
        days_until_race: Optional[int],
    ) -> str:
        """Explain training context and patterns."""
        explanations = []

        # Check for recent hard training
        if recent_workouts:
            recent_hard = [
                w for w in recent_workouts[-3:] if w.get("intensity") == "hard"
            ]
            if len(recent_hard) >= 2:
                explanations.append(
                    "You've completed multiple hard sessions recently, so be cautious "
                    "about adding another consecutive high-intensity day."
                )

            # Check for recent race
            recent_race = [
                w for w in recent_workouts[-7:] if w.get("workout_type") == "race"
            ]
            if recent_race:
                days_since_race = (
                    date.today() - recent_race[0].get("date", date.today())
                ).days
                if days_since_race <= 3:
                    explanations.append(
                        f"You raced {days_since_race} day{'s' if days_since_race > 1 else ''} ago, "
                        "so prioritizing recovery is essential."
                    )

        # Periodization phase context
        if phase == "base":
            explanations.append(
                "During base building, focus on developing aerobic capacity through "
                "consistent, moderate-intensity training."
            )
        elif phase == "build":
            explanations.append(
                "In the build phase, incorporate quality intensity work while managing fatigue."
            )
        elif phase == "taper":
            explanations.append(
                "Taper week: maintain intensity but reduce volume to arrive fresh for your event."
            )

        # Race proximity
        if days_until_race is not None and days_until_race <= 7:
            explanations.append(
                f"With {days_until_race} days until your race, prioritize freshness over fitness gains."
            )

        return " ".join(explanations)

    def _generate_closing(self, intensity: str, workout_type: str, score: int) -> str:
        """Generate closing recommendation statement."""
        if intensity == "hard":
            return (
                f"Today is a great day for a challenging {workout_type} workout "
                "to build fitness and push your limits."
            )
        elif intensity == "moderate":
            if score >= 60:
                return (
                    f"A {workout_type} session at moderate intensity will build fitness "
                    "while allowing continued recovery."
                )
            else:
                return (
                    f"Keep it moderate with {workout_type} today, erring on the side of easier "
                    "effort if you feel fatigued."
                )
        else:  # rest/recovery
            if score < 30:
                return (
                    "Complete rest is your best training today. Recovery is when adaptation happens, "
                    "and pushing through fatigue will only delay your progress."
                )
            else:
                return (
                    f"Easy {workout_type} activity or complete rest will help you bounce back stronger. "
                    "Listen to your body and don't hesitate to take full rest if needed."
                )
