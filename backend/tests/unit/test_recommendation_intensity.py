"""
Unit tests for Workout Intensity Mapping.

Intensity Mapping Algorithm:
Maps recovery score status to appropriate training intensity:
- Green (70-100): Hard intensity - intervals, threshold, VO2max work
- Yellow (40-69): Moderate intensity - tempo, steady-state, aerobic work
- Red (0-39): Rest/Recovery - easy/recovery pace or complete rest

Additional considerations:
- Anomaly severity can downgrade intensity
- Critical warnings force rest regardless of score
- Recent training load affects intensity recommendation
"""


from src.services.recommendations.intensity_mapper import IntensityMapper


class TestIntensityMappingBasics:
    """Test basic intensity mapping from recovery status."""

    def test_green_status_maps_to_hard(self):
        """Test that green status (70-100) maps to hard intensity."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 85,
            "status": "green",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "hard"

    def test_yellow_status_maps_to_moderate(self):
        """Test that yellow status (40-69) maps to moderate intensity."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 55,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "moderate"

    def test_red_status_maps_to_rest(self):
        """Test that red status (0-39) maps to rest/recovery."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 25,
            "status": "red",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity in ["rest", "recovery"]


class TestIntensityBoundaries:
    """Test intensity mapping at score boundaries."""

    def test_score_70_maps_to_hard(self):
        """Test that score of exactly 70 maps to hard."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 70,
            "status": "green",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "hard"

    def test_score_69_maps_to_moderate(self):
        """Test that score of 69 maps to moderate."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 69,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "moderate"

    def test_score_40_maps_to_moderate(self):
        """Test that score of exactly 40 maps to moderate."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 40,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "moderate"

    def test_score_39_maps_to_rest(self):
        """Test that score of 39 maps to rest."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 39,
            "status": "red",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity in ["rest", "recovery"]

    def test_score_100_maps_to_hard(self):
        """Test that perfect score (100) maps to hard."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 100,
            "status": "green",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "hard"

    def test_score_0_maps_to_complete_rest(self):
        """Test that score of 0 maps to complete rest."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 0,
            "status": "red",
            "anomaly_severity": "critical",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "rest"


class TestAnomalyDowngrade:
    """Test that anomaly severity can downgrade intensity."""

    def test_green_with_warning_downgrades_to_moderate(self):
        """Test that green score with warning severity downgrades intensity."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 75,
            "status": "green",  # Would normally be hard
            "anomaly_severity": "warning",
        }

        intensity = mapper.map_intensity(recovery_data)

        # Should downgrade from hard to moderate due to warning
        assert intensity == "moderate"

    def test_green_with_critical_downgrades_to_rest(self):
        """Test that green score with critical anomaly forces rest."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 80,
            "status": "green",  # Would normally be hard
            "anomaly_severity": "critical",
        }

        intensity = mapper.map_intensity(recovery_data)

        # Critical anomaly forces rest regardless of score
        assert intensity in ["rest", "recovery"]

    def test_yellow_with_critical_downgrades_to_rest(self):
        """Test that yellow score with critical anomaly forces rest."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 50,
            "status": "yellow",
            "anomaly_severity": "critical",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity in ["rest", "recovery"]

    def test_red_with_critical_stays_rest(self):
        """Test that red score with critical stays rest."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 20,
            "status": "red",
            "anomaly_severity": "critical",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "rest"


class TestIntensityLevels:
    """Test intensity level details and metadata."""

    def test_hard_intensity_includes_workout_types(self):
        """Test that hard intensity includes appropriate workout types."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 90,
            "status": "green",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        assert result["intensity"] == "hard"
        assert (
            "intervals" in result["workout_types"]
            or "threshold" in result["workout_types"]
        )

    def test_moderate_intensity_includes_workout_types(self):
        """Test that moderate intensity includes steady-state workouts."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 55,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        assert result["intensity"] == "moderate"
        assert "tempo" in result["workout_types"] or "steady" in result["workout_types"]

    def test_rest_intensity_includes_recovery_types(self):
        """Test that rest intensity includes recovery activities."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 30,
            "status": "red",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        assert result["intensity"] in ["rest", "recovery"]
        assert (
            "recovery" in result["workout_types"] or "easy" in result["workout_types"]
        )


class TestIntensityGuidance:
    """Test that intensity mapping includes proper guidance."""

    def test_hard_intensity_provides_zones(self):
        """Test that hard intensity includes heart rate/power zones."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 85,
            "status": "green",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Should include zone guidance (Zone 4-5 for hard)
        assert result.get("zones") is not None
        assert 4 in result["zones"] or 5 in result["zones"]

    def test_moderate_intensity_provides_zones(self):
        """Test that moderate intensity includes appropriate zones."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 50,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Should include zone guidance (Zone 2-3 for moderate)
        assert result.get("zones") is not None
        assert 2 in result["zones"] or 3 in result["zones"]

    def test_rest_intensity_provides_zones(self):
        """Test that rest intensity includes low zones."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 25,
            "status": "red",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Should include zone guidance (Zone 1 for recovery)
        assert result.get("zones") is not None
        assert 1 in result["zones"]


class TestDurationRecommendations:
    """Test that intensity affects duration recommendations."""

    def test_hard_intensity_recommends_shorter_duration(self):
        """Test that hard workouts recommend shorter durations."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 90,
            "status": "green",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Hard workouts typically shorter (45-90 min)
        assert result.get("duration_range") is not None
        min_duration, max_duration = result["duration_range"]
        assert max_duration <= 120  # Not more than 2 hours for hard

    def test_moderate_intensity_recommends_medium_duration(self):
        """Test that moderate workouts recommend medium durations."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 55,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Moderate workouts medium duration (60-120 min)
        assert result.get("duration_range") is not None
        min_duration, max_duration = result["duration_range"]
        assert 60 <= min_duration <= max_duration <= 150

    def test_rest_intensity_recommends_flexible_duration(self):
        """Test that rest allows flexible or no duration."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 20,
            "status": "red",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Recovery can be flexible (30-60 min easy or complete rest)
        assert result.get("duration_range") is not None or result["intensity"] == "rest"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_recovery_data_returns_rest(self):
        """Test that missing recovery data defaults to rest."""
        mapper = IntensityMapper()

        intensity = mapper.map_intensity(None)

        assert intensity == "rest"

    def test_invalid_status_defaults_to_moderate(self):
        """Test that invalid status defaults to moderate."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 65,
            "status": "invalid_status",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        # Should default to safe option (moderate or rest)
        assert intensity in ["moderate", "rest"]

    def test_missing_anomaly_severity_treats_as_none(self):
        """Test that missing anomaly severity is treated as none."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 80,
            "status": "green"
            # No anomaly_severity provided
        }

        intensity = mapper.map_intensity(recovery_data)

        # Should still work, treating as no anomaly
        assert intensity == "hard"


class TestIntensityProgression:
    """Test intensity progression patterns."""

    def test_monotonic_intensity_with_score(self):
        """Test that higher scores don't decrease intensity."""
        mapper = IntensityMapper()

        scores = [20, 40, 70, 90]
        intensities = []

        for score in scores:
            status = "red" if score < 40 else "yellow" if score < 70 else "green"
            recovery_data = {
                "overall_score": score,
                "status": status,
                "anomaly_severity": "none",
            }
            intensity = mapper.map_intensity(recovery_data)
            intensities.append(intensity)

        # Map intensities to numeric values for comparison
        intensity_values = {
            "rest": 0,
            "recovery": 1,
            "easy": 1,
            "moderate": 2,
            "hard": 3,
        }

        numeric_intensities = [intensity_values.get(i, 0) for i in intensities]

        # Should be non-decreasing
        for i in range(len(numeric_intensities) - 1):
            assert numeric_intensities[i] <= numeric_intensities[i + 1]


class TestRealWorldScenarios:
    """Test realistic recovery and intensity scenarios."""

    def test_excellent_recovery_enables_hard_workout(self):
        """Test athlete with excellent recovery gets hard workout."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 95,
            "status": "green",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "hard"

    def test_moderate_recovery_limits_to_steady_state(self):
        """Test athlete with moderate recovery limited to steady work."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 60,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity == "moderate"

    def test_illness_warning_forces_rest(self):
        """Test that illness warning forces rest despite good score."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 75,  # Would normally be hard
            "status": "green",
            "anomaly_severity": "critical",  # But illness detected
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity in ["rest", "recovery"]

    def test_overreached_athlete_gets_recovery(self):
        """Test overreached athlete gets recovery intensity."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 35,
            "status": "red",
            "anomaly_severity": "warning",
        }

        intensity = mapper.map_intensity(recovery_data)

        assert intensity in ["rest", "recovery"]

    def test_taper_week_with_good_recovery(self):
        """Test taper week (high recovery) still allows hard work."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 88,
            "status": "green",
            "anomaly_severity": "none",
        }

        intensity = mapper.map_intensity(recovery_data)

        # High recovery in taper = can do quality work
        assert intensity == "hard"


class TestIntensityMetadata:
    """Test that intensity mapping includes useful metadata."""

    def test_includes_rationale(self):
        """Test that intensity details include rationale."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 75,
            "status": "green",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        assert "rationale" in result
        assert len(result["rationale"]) > 0

    def test_includes_warnings_when_applicable(self):
        """Test that warnings are included when anomalies present."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 70,
            "status": "green",
            "anomaly_severity": "warning",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Should include warning about anomaly
        assert "warnings" in result or "caution" in result.get("rationale", "").lower()

    def test_includes_alternatives(self):
        """Test that intensity details include alternative options."""
        mapper = IntensityMapper()

        recovery_data = {
            "overall_score": 65,
            "status": "yellow",
            "anomaly_severity": "none",
        }

        result = mapper.get_intensity_details(recovery_data)

        # Should suggest alternative intensity levels
        assert "alternatives" in result
        assert len(result["alternatives"]) > 0
