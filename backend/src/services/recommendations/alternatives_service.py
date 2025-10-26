"""
Alternative Workout Generator (FR-014).

Generates alternative workout options when the primary recommendation
doesn't fit the athlete's schedule, preferences, or circumstances.

Alternatives maintain similar training stimulus while offering flexibility:
- Different workout types at same intensity
- Cross-training options for injured athletes
- Time-constrained alternatives
- Sport-specific variations
"""

from typing import List, Dict, Optional
import logging

from src.services.recommendations.type_recommender import TypeRecommender
from src.services.recommendations.intensity_mapper import IntensityMapper

logger = logging.getLogger(__name__)


class AlternativesService:
    """Generates alternative workout recommendations."""

    def __init__(self):
        self.type_recommender = TypeRecommender()
        self.intensity_mapper = IntensityMapper()

    def generate_alternatives(
        self,
        primary_recommendation: Dict[str, any],
        recovery_data: Dict[str, any],
        constraints: Optional[Dict[str, any]] = None,
    ) -> List[Dict[str, any]]:
        """
        Generate alternative workout options.

        Args:
            primary_recommendation: Primary workout recommendation with:
                - intensity: Intensity level
                - workout_type: Primary workout type
                - duration: Recommended duration
                - sport: Sport type
            recovery_data: Recovery score and component data
            constraints: Optional constraints:
                - time_available: Minutes available
                - injury_status: Injury location
                - equipment_available: Available equipment
                - weather_conditions: Weather constraints

        Returns:
            List of alternative workout dicts with rationale
        """
        intensity = primary_recommendation.get("intensity")
        primary_type = primary_recommendation.get("workout_type")
        sport = primary_recommendation.get("sport", "general")
        duration = primary_recommendation.get("duration", 60)

        alternatives = []

        # Alternative 1: Different workout type, same intensity
        alt1 = self._generate_same_intensity_alternative(
            intensity, sport, primary_type, duration, recovery_data
        )
        if alt1:
            alternatives.append(alt1)

        # Alternative 2: Lower intensity option (conservative)
        alt2 = self._generate_lower_intensity_alternative(
            intensity, sport, duration, recovery_data
        )
        if alt2:
            alternatives.append(alt2)

        # Alternative 3: Cross-training option
        if constraints and constraints.get("injury_status"):
            alt3 = self._generate_cross_training_alternative(
                intensity, constraints["injury_status"], duration
            )
            if alt3:
                alternatives.append(alt3)

        # Alternative 4: Time-constrained option
        if constraints and constraints.get("time_available"):
            alt4 = self._generate_time_constrained_alternative(
                intensity, sport, primary_type, constraints["time_available"]
            )
            if alt4:
                alternatives.append(alt4)

        # Alternative 5: Weather alternative
        if constraints and constraints.get("weather_conditions") == "bad":
            alt5 = self._generate_indoor_alternative(intensity, sport, duration)
            if alt5:
                alternatives.append(alt5)

        return alternatives[:4]  # Return max 4 alternatives

    def _generate_same_intensity_alternative(
        self,
        intensity: str,
        sport: str,
        primary_type: str,
        duration: int,
        recovery_data: Dict[str, any],
    ) -> Optional[Dict[str, any]]:
        """Generate alternative with same intensity, different workout type."""
        # Get workout recommendations (which includes alternatives)
        recommendations = self.type_recommender.get_workout_recommendations(
            intensity=intensity,
            sport=sport,
            recent_workouts=[{"workout_type": primary_type}],  # Exclude primary
            recovery_score=recovery_data.get("overall_score"),
        )

        if recommendations["alternatives"]:
            alt = recommendations["alternatives"][0]
            return {
                "workout_type": alt["workout_type"],
                "intensity": intensity,
                "duration": duration,
                "details": alt["details"],
                "rationale": (
                    f"Alternative {alt['workout_type']} workout providing similar "
                    f"training stimulus at {intensity} intensity."
                ),
            }

        return None

    def _generate_lower_intensity_alternative(
        self, intensity: str, sport: str, duration: int, recovery_data: Dict[str, any]
    ) -> Optional[Dict[str, any]]:
        """Generate more conservative, lower intensity alternative."""
        # Map to one intensity level lower
        intensity_map = {"hard": "moderate", "moderate": "rest", "rest": "rest"}

        lower_intensity = intensity_map.get(intensity, "moderate")

        if lower_intensity == intensity:
            return None  # Already at lowest

        workout_type = self.type_recommender.select_workout_type(
            intensity=lower_intensity, sport=sport, recent_workouts=[]
        )

        details = self.type_recommender.get_workout_details(
            workout_type=workout_type,
            intensity=lower_intensity,
            sport=sport,
            recovery_score=recovery_data.get("overall_score"),
        )

        return {
            "workout_type": workout_type,
            "intensity": lower_intensity,
            "duration": duration,
            "details": details,
            "rationale": (
                f"More conservative {lower_intensity} intensity option. "
                "Choose this if you're feeling more fatigued than expected or "
                "want to err on the side of caution."
            ),
        }

    def _generate_cross_training_alternative(
        self, intensity: str, injury_status: str, duration: int
    ) -> Optional[Dict[str, any]]:
        """Generate cross-training alternative for injured athletes."""
        # Map injuries to safe cross-training options
        cross_training_map = {
            "lower_leg": ["swimming", "pool_running", "bike"],
            "knee": ["swimming", "upper_body"],
            "hip": ["swimming", "upper_body"],
            "upper_body": ["running", "bike", "lower_body"],
            "foot": ["swimming", "bike"],
        }

        safe_options = cross_training_map.get(injury_status, ["swimming", "yoga"])

        return {
            "workout_type": "cross_training",
            "intensity": "rest" if intensity == "hard" else intensity,
            "duration": min(duration, 45),  # Shorter for cross-training
            "details": {
                "activities": safe_options,
                "duration": min(duration, 45),
                "zones": [1, 2],
                "structure": f"Low-impact cross-training: {', '.join(safe_options)}",
            },
            "rationale": (
                f"Low-impact cross-training alternative to work around your {injury_status} injury. "
                f"Options: {', '.join(safe_options)}. Keep intensity low to promote healing."
            ),
        }

    def _generate_time_constrained_alternative(
        self, intensity: str, sport: str, primary_type: str, time_available: int
    ) -> Optional[Dict[str, any]]:
        """Generate shorter, time-efficient alternative."""
        if time_available >= 60:
            return None  # No need for time-constrained alternative

        # For time-constrained: prefer intervals (higher intensity, shorter duration)
        if intensity != "hard":
            workout_type = "intervals"
            actual_intensity = "moderate"  # Moderate intervals
        else:
            workout_type = primary_type
            actual_intensity = intensity

        details = self.type_recommender.get_workout_details(
            workout_type=workout_type, intensity=actual_intensity, sport=sport
        )

        # Adjust duration to fit time constraint
        if details.get("total_duration", 60) > time_available:
            # Scale down workout
            scale_factor = time_available / details["total_duration"]
            if "num_intervals" in details:
                details["num_intervals"] = max(
                    3, int(details["num_intervals"] * scale_factor)
                )
            details["total_duration"] = time_available

        return {
            "workout_type": workout_type,
            "intensity": actual_intensity,
            "duration": time_available,
            "details": details,
            "rationale": (
                f"Time-efficient {time_available}-minute option maintaining training quality. "
                "Shorter duration compensated by focused execution."
            ),
        }

    def _generate_indoor_alternative(
        self, intensity: str, sport: str, duration: int
    ) -> Optional[Dict[str, any]]:
        """Generate indoor training alternative for bad weather."""
        # Map outdoor sports to indoor equivalents
        indoor_options = {
            "cycling": "trainer",
            "running": "treadmill",
            "triathlon": "trainer_or_treadmill",
            "swimming": "pool",  # Already indoor
        }

        indoor_type = indoor_options.get(sport, "trainer")

        workout_type = self.type_recommender.select_workout_type(
            intensity=intensity, sport=sport, recent_workouts=[]
        )

        details = self.type_recommender.get_workout_details(
            workout_type=workout_type, intensity=intensity, sport=sport
        )

        # Indoor workouts often more focused/intense, so may be shorter
        indoor_duration = min(duration, int(duration * 0.9))

        return {
            "workout_type": f"indoor_{workout_type}",
            "intensity": intensity,
            "duration": indoor_duration,
            "details": details,
            "rationale": (
                f"Indoor {indoor_type} option for adverse weather conditions. "
                "Maintain workout quality in a controlled environment."
            ),
        }
