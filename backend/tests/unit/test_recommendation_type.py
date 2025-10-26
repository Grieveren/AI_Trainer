"""
Unit tests for Workout Type Selection.

Workout Type Selection Algorithm:
Selects specific workout types based on:
- Intensity level (hard/moderate/rest)
- Sport type (cycling, running, swimming, triathlon)
- Recent training history (avoid repetition)
- Periodization goals (build/peak/taper)

Hard Intensity Types:
- Intervals (VO2max, threshold, sprint)
- Hill repeats
- Tempo runs/rides

Moderate Intensity Types:
- Steady-state aerobic
- Tempo (lower end)
- Long slow distance

Rest/Recovery Types:
- Easy/recovery pace
- Active recovery
- Complete rest
- Cross-training (yoga, swimming)
"""

from datetime import date, timedelta

from src.services.recommendations.type_recommender import TypeRecommender


class TestWorkoutTypeByIntensity:
    """Test workout type selection based on intensity."""

    def test_hard_intensity_selects_intervals(self):
        """Test that hard intensity can select interval workouts."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="cycling", recent_workouts=[]
        )

        assert workout_type in ["intervals", "threshold", "vo2max", "hills"]

    def test_moderate_intensity_selects_steady_state(self):
        """Test that moderate intensity selects steady-state work."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="moderate", sport="running", recent_workouts=[]
        )

        assert workout_type in ["tempo", "steady", "aerobic", "long_run"]

    def test_rest_intensity_selects_recovery(self):
        """Test that rest intensity selects recovery activities."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="rest", sport="triathlon", recent_workouts=[]
        )

        assert workout_type in [
            "recovery",
            "easy",
            "rest",
            "active_recovery",
            "yoga",
            "swim_recovery",
        ]


class TestSportSpecificWorkouts:
    """Test that workout types are appropriate for each sport."""

    def test_cycling_hard_includes_cycling_specific(self):
        """Test cycling hard workouts include cycling-specific types."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="cycling", recent_workouts=[]
        )

        cycling_types = ["intervals", "threshold", "climbs", "criterium", "sweet_spot"]
        assert workout_type in cycling_types

    def test_running_hard_includes_running_specific(self):
        """Test running hard workouts include running-specific types."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="running", recent_workouts=[]
        )

        running_types = [
            "intervals",
            "threshold",
            "tempo",
            "hill_repeats",
            "fartlek",
            "track_workout",
        ]
        assert workout_type in running_types

    def test_swimming_moderate_includes_swimming_specific(self):
        """Test swimming moderate workouts include swimming-specific types."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="moderate", sport="swimming", recent_workouts=[]
        )

        swimming_types = ["steady_swim", "technique", "endurance_swim", "pull_sets"]
        assert workout_type in swimming_types

    def test_triathlon_provides_multisport_options(self):
        """Test triathlon provides options across all three sports."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="moderate", sport="triathlon", recent_workouts=[]
        )

        # Should be valid for one of the three sports
        assert workout_type is not None


class TestWorkoutVariety:
    """Test that workout type selection avoids repetition."""

    def test_avoids_recent_workout_type(self):
        """Test that recommender avoids recently done workout types."""
        recommender = TypeRecommender()

        recent_workouts = [
            {"date": date.today() - timedelta(days=1), "workout_type": "intervals"},
            {"date": date.today() - timedelta(days=2), "workout_type": "tempo"},
        ]

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="cycling", recent_workouts=recent_workouts
        )

        # Should not recommend intervals again immediately
        assert workout_type != "intervals"

    def test_provides_variety_over_week(self):
        """Test that recommendations provide variety over a week."""
        recommender = TypeRecommender()

        # Simulate week of workouts
        recent_workouts = [
            {"date": date.today() - timedelta(days=i), "workout_type": f"type_{i}"}
            for i in range(1, 6)
        ]

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="running", recent_workouts=recent_workouts
        )

        # Should select different type not in recent 5 days
        recent_types = [w["workout_type"] for w in recent_workouts]
        assert workout_type not in recent_types

    def test_allows_repetition_after_sufficient_gap(self):
        """Test that workout types can repeat after 7+ days."""
        recommender = TypeRecommender()

        recent_workouts = [
            {"date": date.today() - timedelta(days=8), "workout_type": "intervals"}
        ]

        # After 8 days, intervals should be selectable again
        possible_types = []
        for _ in range(10):  # Try multiple times
            workout_type = recommender.select_workout_type(
                intensity="hard", sport="cycling", recent_workouts=recent_workouts
            )
            possible_types.append(workout_type)

        # Intervals should be possible again
        assert "intervals" in possible_types or len(set(possible_types)) > 1


class TestWorkoutStructure:
    """Test that workout types include structural details."""

    def test_intervals_include_interval_structure(self):
        """Test that interval workouts include interval details."""
        recommender = TypeRecommender()

        workout_details = recommender.get_workout_details(
            workout_type="intervals", intensity="hard", sport="cycling"
        )

        assert "intervals" in workout_details or "structure" in workout_details
        assert workout_details.get("work_duration") is not None
        assert workout_details.get("rest_duration") is not None
        assert workout_details.get("num_intervals") is not None

    def test_tempo_includes_duration_guidance(self):
        """Test that tempo workouts include duration guidance."""
        recommender = TypeRecommender()

        workout_details = recommender.get_workout_details(
            workout_type="tempo", intensity="moderate", sport="running"
        )

        assert workout_details.get("duration") is not None
        assert workout_details.get("pace_guidance") is not None

    def test_recovery_includes_guidelines(self):
        """Test that recovery workouts include recovery guidelines."""
        recommender = TypeRecommender()

        workout_details = recommender.get_workout_details(
            workout_type="recovery", intensity="rest", sport="running"
        )

        assert workout_details.get("duration") is not None
        assert workout_details.get("intensity_cap") is not None


class TestPeriodizationAwareness:
    """Test that workout selection considers periodization phase."""

    def test_base_phase_emphasizes_aerobic(self):
        """Test that base building phase emphasizes aerobic work."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="moderate", sport="cycling", recent_workouts=[], phase="base"
        )

        base_types = ["steady", "aerobic", "endurance", "long_ride"]
        assert workout_type in base_types

    def test_build_phase_includes_more_intensity(self):
        """Test that build phase includes more intense work."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="running", recent_workouts=[], phase="build"
        )

        build_types = ["intervals", "threshold", "tempo", "vo2max"]
        assert workout_type in build_types

    def test_peak_phase_maintains_sharpness(self):
        """Test that peak phase maintains sharpness with reduced volume."""
        recommender = TypeRecommender()

        workout_details = recommender.get_workout_details(
            workout_type="intervals", intensity="hard", sport="cycling", phase="peak"
        )

        # Peak phase should have shorter, sharper workouts
        assert workout_details.get("total_duration") is not None
        # Duration should be shorter than build phase
        assert workout_details["total_duration"] < 90  # Less than 90 minutes

    def test_taper_phase_reduces_volume(self):
        """Test that taper phase reduces volume while maintaining intensity."""
        recommender = TypeRecommender()

        workout_details = recommender.get_workout_details(
            workout_type="intervals", intensity="hard", sport="running", phase="taper"
        )

        # Taper maintains intensity but reduces volume
        assert workout_details.get("num_intervals") is not None
        # Fewer intervals than normal
        assert workout_details["num_intervals"] <= 6


class TestWorkoutDifficulty:
    """Test that workout difficulty matches recovery status."""

    def test_excellent_recovery_enables_harder_variants(self):
        """Test that excellent recovery enables harder workout variants."""
        recommender = TypeRecommender()

        workout_details = recommender.get_workout_details(
            workout_type="intervals",
            intensity="hard",
            sport="cycling",
            recovery_score=95,
        )

        # High recovery = more demanding workout
        assert (
            workout_details.get("num_intervals") >= 8
            or workout_details.get("work_duration") >= 5
        )

    def test_moderate_recovery_provides_scaled_version(self):
        """Test that moderate recovery provides scaled workout."""
        recommender = TypeRecommender()

        workout_details = recommender.get_workout_details(
            workout_type="tempo",
            intensity="moderate",
            sport="running",
            recovery_score=55,
        )

        # Moderate recovery = scaled back
        assert workout_details.get("duration") <= 60  # Not more than 60 min tempo


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unknown_sport_defaults_to_general(self):
        """Test that unknown sport uses general workout types."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="moderate", sport="unknown_sport", recent_workouts=[]
        )

        # Should still return valid workout type
        assert workout_type is not None
        assert workout_type in ["steady", "tempo", "intervals", "recovery", "rest"]

    def test_empty_recent_workouts_returns_valid_type(self):
        """Test that empty workout history returns valid type."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="cycling", recent_workouts=[]
        )

        assert workout_type is not None

    def test_none_intensity_defaults_to_moderate(self):
        """Test that None intensity defaults to safe moderate."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity=None, sport="running", recent_workouts=[]
        )

        # Should default to moderate intensity types
        moderate_types = ["tempo", "steady", "aerobic", "recovery", "easy"]
        assert workout_type in moderate_types


class TestRealWorldScenarios:
    """Test realistic workout selection scenarios."""

    def test_post_race_recovery_week(self):
        """Test workout selection for post-race recovery."""
        recommender = TypeRecommender()

        recent_workouts = [
            {
                "date": date.today() - timedelta(days=1),
                "workout_type": "race",
                "intensity": "hard",
            },
        ]

        workout_type = recommender.select_workout_type(
            intensity="rest", sport="triathlon", recent_workouts=recent_workouts
        )

        # Should recommend gentle recovery
        assert workout_type in ["recovery", "easy", "swim_recovery", "yoga", "rest"]

    def test_midweek_quality_session(self):
        """Test midweek quality session selection."""
        recommender = TypeRecommender()

        recent_workouts = [
            {"date": date.today() - timedelta(days=2), "workout_type": "long_run"},
            {"date": date.today() - timedelta(days=1), "workout_type": "recovery"},
        ]

        workout_type = recommender.select_workout_type(
            intensity="hard", sport="running", recent_workouts=recent_workouts
        )

        # Midweek quality could be intervals or tempo
        assert workout_type in ["intervals", "threshold", "tempo", "hill_repeats"]

    def test_weekend_long_workout(self):
        """Test weekend long workout selection."""
        recommender = TypeRecommender()

        recent_workouts = [
            {"date": date.today() - timedelta(days=3), "workout_type": "intervals"},
            {"date": date.today() - timedelta(days=1), "workout_type": "easy"},
        ]

        workout_type = recommender.select_workout_type(
            intensity="moderate",
            sport="cycling",
            recent_workouts=recent_workouts,
            day_of_week=6,  # Saturday
        )

        # Weekend = longer aerobic work
        assert workout_type in ["long_ride", "endurance", "steady", "group_ride"]

    def test_injured_athlete_cross_training(self):
        """Test cross-training recommendations for injured athletes."""
        recommender = TypeRecommender()

        workout_type = recommender.select_workout_type(
            intensity="rest",
            sport="running",
            recent_workouts=[],
            injury_status="lower_leg",
        )

        # Should recommend low-impact alternatives
        assert workout_type in ["swim", "bike", "pool_running", "yoga", "rest"]


class TestWorkoutProgression:
    """Test workout progression patterns."""

    def test_progressive_overload_over_weeks(self):
        """Test that workouts can progress in difficulty."""
        recommender = TypeRecommender()

        # Week 1: moderate intervals
        week1_details = recommender.get_workout_details(
            workout_type="intervals", intensity="hard", sport="cycling", week_number=1
        )

        # Week 4: should be more challenging
        week4_details = recommender.get_workout_details(
            workout_type="intervals", intensity="hard", sport="cycling", week_number=4
        )

        # Week 4 should have more volume or intensity
        assert (
            week4_details["num_intervals"] > week1_details["num_intervals"]
            or week4_details["work_duration"] > week1_details["work_duration"]
        )

    def test_recovery_week_reduces_load(self):
        """Test that recovery weeks reduce training load."""
        recommender = TypeRecommender()

        normal_week = recommender.get_workout_details(
            workout_type="intervals", intensity="hard", sport="running", week_number=3
        )

        recovery_week = recommender.get_workout_details(
            workout_type="intervals",
            intensity="hard",
            sport="running",
            week_number=4,
            is_recovery_week=True,
        )

        # Recovery week should have reduced load
        assert recovery_week["num_intervals"] < normal_week["num_intervals"]


class TestWorkoutAlternatives:
    """Test that workout recommendations include alternatives."""

    def test_provides_alternative_workout_types(self):
        """Test that recommendations include alternative options."""
        recommender = TypeRecommender()

        result = recommender.get_workout_recommendations(
            intensity="hard", sport="cycling", recent_workouts=[]
        )

        assert "primary" in result
        assert "alternatives" in result
        assert len(result["alternatives"]) >= 2

    def test_alternatives_match_intensity_level(self):
        """Test that alternatives match primary intensity."""
        recommender = TypeRecommender()

        result = recommender.get_workout_recommendations(
            intensity="moderate", sport="running", recent_workouts=[]
        )

        # All alternatives should be moderate intensity
        moderate_types = ["tempo", "steady", "aerobic", "long_run", "progression"]
        for alt in result["alternatives"]:
            assert alt["workout_type"] in moderate_types

    def test_alternatives_provide_variety(self):
        """Test that alternatives offer different workout styles."""
        recommender = TypeRecommender()

        result = recommender.get_workout_recommendations(
            intensity="hard", sport="triathlon", recent_workouts=[]
        )

        # Alternatives should be different from primary
        primary_type = result["primary"]["workout_type"]
        alt_types = [alt["workout_type"] for alt in result["alternatives"]]

        assert primary_type not in alt_types
        assert len(set(alt_types)) == len(alt_types)  # All unique
