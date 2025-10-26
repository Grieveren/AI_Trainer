"""
Workout Type Recommender.

Selects specific workout types based on intensity, sport, training history,
and periodization goals.

Provides variety by avoiding recent workout types and considers:
- Intensity level (hard/moderate/rest)
- Sport-specific workouts (cycling, running, swimming, triathlon)
- Recent training history (avoid repetition)
- Periodization phase (base/build/peak/taper)
- Day of week patterns (weekend long workouts)
"""

from typing import List, Dict, Optional, Set
from datetime import date, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class TypeRecommender:
    """Recommends specific workout types based on multiple factors."""

    # Workout type definitions by intensity and sport
    WORKOUT_TYPES = {
        "hard": {
            "cycling": [
                "intervals",
                "threshold",
                "climbs",
                "sweet_spot",
                "vo2max",
                "criterium",
            ],
            "running": [
                "intervals",
                "threshold",
                "tempo",
                "hill_repeats",
                "fartlek",
                "track_workout",
            ],
            "swimming": ["intervals", "threshold_swim", "sprint_sets", "race_pace"],
            "triathlon": ["brick_workout", "intervals", "threshold", "race_simulation"],
            "general": ["intervals", "threshold", "tempo", "hills"],
        },
        "moderate": {
            "cycling": [
                "tempo",
                "steady_state",
                "long_ride",
                "endurance",
                "group_ride",
            ],
            "running": ["tempo", "steady", "long_run", "progression", "aerobic"],
            "swimming": ["steady_swim", "technique", "endurance_swim", "pull_sets"],
            "triathlon": ["long_bike", "long_run", "open_water_swim", "aerobic"],
            "general": ["tempo", "steady", "aerobic", "endurance"],
        },
        "rest": {
            "cycling": ["recovery_ride", "easy_spin", "rest"],
            "running": ["recovery_run", "easy", "rest"],
            "swimming": ["swim_recovery", "technique", "rest"],
            "triathlon": ["easy_swim", "recovery_ride", "yoga", "rest"],
            "general": ["recovery", "easy", "active_recovery", "yoga", "rest"],
        },
    }

    # Avoid repeating workout types within this many days
    VARIETY_WINDOW_DAYS = 5

    # Periodization phase influences
    PHASE_PREFERENCES = {
        "base": ["aerobic", "endurance", "steady", "long_ride", "long_run"],
        "build": ["intervals", "threshold", "tempo", "vo2max"],
        "peak": ["race_pace", "race_simulation", "threshold"],
        "taper": [
            "recovery",
            "easy",
            "short_intervals",
        ],  # Maintain intensity, reduce volume
    }

    def select_workout_type(
        self,
        intensity: str,
        sport: str,
        recent_workouts: List[Dict[str, any]],
        phase: Optional[str] = None,
        day_of_week: Optional[int] = None,
        injury_status: Optional[str] = None,
    ) -> str:
        """
        Select appropriate workout type.

        Args:
            intensity: Intensity level (hard/moderate/rest)
            sport: Sport type (cycling/running/swimming/triathlon/general)
            recent_workouts: List of recent workouts with 'date' and 'workout_type'
            phase: Optional periodization phase (base/build/peak/taper)
            day_of_week: Optional day of week (0=Mon, 6=Sun)
            injury_status: Optional injury location for cross-training

        Returns:
            Workout type string
        """
        # Default to moderate if intensity not recognized
        if intensity not in self.WORKOUT_TYPES:
            intensity = "moderate"

        # Default to general if sport not recognized
        if sport not in self.WORKOUT_TYPES[intensity]:
            sport = "general"

        # Get available workout types for this intensity/sport
        available_types = self.WORKOUT_TYPES[intensity][sport].copy()

        # Handle injury by suggesting cross-training
        if injury_status and intensity == "rest":
            if "lower_leg" in injury_status:
                # Low-impact alternatives
                return random.choice(["swim", "bike", "pool_running", "yoga", "rest"])

        # Filter out recently done workout types (avoid repetition)
        recent_types = self._get_recent_workout_types(recent_workouts)
        varied_types = [wt for wt in available_types if wt not in recent_types]

        # If all types have been done recently, use all available
        if not varied_types:
            varied_types = available_types

        # Apply periodization preferences if phase provided
        if phase and phase in self.PHASE_PREFERENCES:
            preferred = self.PHASE_PREFERENCES[phase]
            # Prioritize phase-appropriate workouts
            phase_matched = [
                wt for wt in varied_types if any(p in wt for p in preferred)
            ]
            if phase_matched:
                varied_types = phase_matched

        # Weekend pattern: prefer longer workouts on weekends
        if day_of_week is not None and day_of_week in [5, 6]:  # Sat/Sun
            weekend_types = [
                wt for wt in varied_types if "long" in wt or "endurance" in wt
            ]
            if weekend_types:
                varied_types = weekend_types

        # Select random workout from remaining options
        return random.choice(varied_types)

    def get_workout_details(
        self,
        workout_type: str,
        intensity: str,
        sport: str,
        recovery_score: Optional[int] = None,
        phase: Optional[str] = None,
        week_number: Optional[int] = None,
        is_recovery_week: bool = False,
    ) -> Dict[str, any]:
        """
        Get detailed workout structure and guidance.

        Args:
            workout_type: Type of workout
            intensity: Intensity level
            sport: Sport type
            recovery_score: Optional recovery score for scaling
            phase: Optional periodization phase
            week_number: Optional week number for progression
            is_recovery_week: Whether this is a recovery week

        Returns:
            Dict with workout details
        """
        if "intervals" in workout_type or workout_type == "vo2max":
            return self._get_interval_details(
                workout_type,
                intensity,
                sport,
                recovery_score,
                phase,
                week_number,
                is_recovery_week,
            )
        elif "tempo" in workout_type or "threshold" in workout_type:
            return self._get_tempo_details(
                workout_type, intensity, sport, recovery_score, phase, is_recovery_week
            )
        elif (
            "recovery" in workout_type
            or "easy" in workout_type
            or workout_type == "rest"
        ):
            return self._get_recovery_details(workout_type, intensity, sport)
        else:
            # Steady-state or other
            return self._get_steady_details(
                workout_type, intensity, sport, recovery_score, is_recovery_week
            )

    def get_workout_recommendations(
        self,
        intensity: str,
        sport: str,
        recent_workouts: List[Dict[str, any]],
        **kwargs,
    ) -> Dict[str, any]:
        """
        Get primary workout recommendation plus alternatives.

        Args:
            intensity: Intensity level
            sport: Sport type
            recent_workouts: Recent workout history
            **kwargs: Additional arguments passed to select_workout_type

        Returns:
            Dict with 'primary' and 'alternatives' workouts
        """
        # Select primary workout
        primary_type = self.select_workout_type(
            intensity, sport, recent_workouts, **kwargs
        )

        # Generate 2-3 alternatives
        alternatives = []
        used_types = {primary_type}

        for _ in range(3):
            # Temporarily add used types to recent workouts to avoid duplicates
            temp_recent = recent_workouts + [{"workout_type": t} for t in used_types]
            alt_type = self.select_workout_type(intensity, sport, temp_recent, **kwargs)

            if alt_type not in used_types:
                alternatives.append(
                    {
                        "workout_type": alt_type,
                        "details": self.get_workout_details(
                            alt_type,
                            intensity,
                            sport,
                            recovery_score=kwargs.get("recovery_score"),
                            phase=kwargs.get("phase"),
                        ),
                    }
                )
                used_types.add(alt_type)

            if len(alternatives) >= 2:
                break

        return {
            "primary": {
                "workout_type": primary_type,
                "details": self.get_workout_details(
                    primary_type,
                    intensity,
                    sport,
                    recovery_score=kwargs.get("recovery_score"),
                    phase=kwargs.get("phase"),
                ),
            },
            "alternatives": alternatives,
        }

    def _get_recent_workout_types(
        self, recent_workouts: List[Dict[str, any]]
    ) -> Set[str]:
        """Extract workout types from recent workouts within variety window."""
        recent_types = set()
        cutoff_date = date.today() - timedelta(days=self.VARIETY_WINDOW_DAYS)

        for workout in recent_workouts:
            workout_date = workout.get("date")
            workout_type = workout.get("workout_type")

            if workout_date and workout_type:
                if workout_date >= cutoff_date:
                    recent_types.add(workout_type)

        return recent_types

    def _get_interval_details(
        self,
        workout_type: str,
        intensity: str,
        sport: str,
        recovery_score: Optional[int],
        phase: Optional[str],
        week_number: Optional[int],
        is_recovery_week: bool,
    ) -> Dict[str, any]:
        """Get interval workout structure."""
        # Base interval structure
        if "vo2max" in workout_type or intensity == "hard":
            work_duration = 5  # 5 minutes
            rest_duration = 3  # 3 minutes
            num_intervals = 8
        else:
            work_duration = 3
            rest_duration = 2
            num_intervals = 6

        # Scale based on recovery score
        if recovery_score and recovery_score >= 90:
            num_intervals += 2  # More intervals when well-recovered
        elif recovery_score and recovery_score < 60:
            num_intervals = max(4, num_intervals - 2)  # Fewer when moderately recovered

        # Progression over weeks
        if week_number:
            num_intervals += min(week_number - 1, 3)  # Add up to 3 intervals

        # Recovery week reduces volume
        if is_recovery_week:
            num_intervals = max(4, int(num_intervals * 0.6))

        # Taper phase: shorter, sharper
        if phase == "taper":
            num_intervals = min(num_intervals, 6)
            work_duration = max(3, work_duration - 1)

        total_duration = (
            work_duration + rest_duration
        ) * num_intervals + 20  # +20 for warmup/cooldown

        return {
            "work_duration": work_duration,
            "rest_duration": rest_duration,
            "num_intervals": num_intervals,
            "total_duration": total_duration,
            "warmup": 10,
            "cooldown": 10,
            "zones": [4, 5],
            "structure": f"{num_intervals}x {work_duration}min @ Z4-5 / {rest_duration}min rest",
        }

    def _get_tempo_details(
        self,
        workout_type: str,
        intensity: str,
        sport: str,
        recovery_score: Optional[int],
        phase: Optional[str],
        is_recovery_week: bool,
    ) -> Dict[str, any]:
        """Get tempo/threshold workout structure."""
        # Base duration
        duration = 45 if "threshold" in workout_type else 30

        # Scale based on recovery
        if recovery_score and recovery_score >= 85:
            duration += 15
        elif recovery_score and recovery_score < 60:
            duration = max(20, duration - 15)

        # Recovery week reduces duration
        if is_recovery_week:
            duration = int(duration * 0.7)

        total_duration = duration + 20  # warmup/cooldown

        return {
            "duration": duration,
            "total_duration": total_duration,
            "warmup": 10,
            "cooldown": 10,
            "zones": [3, 4],
            "pace_guidance": "Comfortably hard - can speak short sentences",
            "structure": f"{duration}min @ Z3-4 (tempo/threshold pace)",
        }

    def _get_recovery_details(
        self, workout_type: str, intensity: str, sport: str
    ) -> Dict[str, any]:
        """Get recovery workout structure."""
        if workout_type == "rest":
            return {
                "duration": 0,
                "total_duration": 0,
                "zones": [],
                "intensity_cap": None,
                "structure": "Complete rest - no training",
            }

        # Easy/recovery workout
        duration = 45

        return {
            "duration": duration,
            "total_duration": duration,
            "zones": [1],
            "intensity_cap": "Zone 1 only - very easy conversational pace",
            "structure": f"{duration}min @ Z1 (recovery pace)",
        }

    def _get_steady_details(
        self,
        workout_type: str,
        intensity: str,
        sport: str,
        recovery_score: Optional[int],
        is_recovery_week: bool,
    ) -> Dict[str, any]:
        """Get steady-state workout structure."""
        # Base duration for aerobic work
        if "long" in workout_type:
            duration = 120  # 2 hours
        else:
            duration = 75

        # Scale based on recovery
        if recovery_score and recovery_score >= 85:
            duration += 30
        elif recovery_score and recovery_score < 60:
            duration = max(60, duration - 30)

        # Recovery week
        if is_recovery_week:
            duration = int(duration * 0.75)

        return {
            "duration": duration,
            "total_duration": duration,
            "zones": [2],
            "pace_guidance": "Conversational pace - can hold full conversation",
            "structure": f"{duration}min @ Z2 (aerobic/endurance pace)",
        }
