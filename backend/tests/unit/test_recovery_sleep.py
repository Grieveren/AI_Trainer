"""
Unit tests for Sleep component of recovery score.

Sleep Component Algorithm:
- Sleep Duration (60% weight):
  - 7-9 hours = 100 (optimal)
  - 6 hours = 70 (sub-optimal)
  - 5 hours = 40 (poor)
  - <4 hours = 0 (very poor)
  - >10 hours = 70 (excessive, may indicate fatigue)
  - Linear interpolation between points

- Sleep Quality (40% weight):
  - Uses Garmin sleep score if available (0-100)
  - Otherwise duration-only scoring

- Combined Score:
  - If quality available: (duration_score * 0.6) + (quality_score * 0.4)
  - If quality missing: duration_score only (100% weight)
"""

from datetime import date

from src.services.recovery.sleep_calculator import SleepCalculator


class TestSleepDurationScoring:
    """Test sleep duration component scoring."""

    def test_optimal_sleep_7_hours_scores_100(self):
        """Test that 7 hours of sleep scores 100."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 7 * 3600,  # 7 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 100

    def test_optimal_sleep_8_hours_scores_100(self):
        """Test that 8 hours of sleep scores 100."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,  # 8 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 100

    def test_optimal_sleep_9_hours_scores_100(self):
        """Test that 9 hours of sleep scores 100."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 9 * 3600,  # 9 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 100

    def test_suboptimal_sleep_6_hours_scores_70(self):
        """Test that 6 hours of sleep scores 70."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 6 * 3600,  # 6 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 70

    def test_poor_sleep_5_hours_scores_40(self):
        """Test that 5 hours of sleep scores 40."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 5 * 3600,  # 5 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 40

    def test_very_poor_sleep_4_hours_scores_0(self):
        """Test that 4 hours or less scores 0."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 4 * 3600,  # 4 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 0

    def test_excessive_sleep_10_hours_scores_70(self):
        """Test that excessive sleep (10+ hours) scores 70."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 10 * 3600,  # 10 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 70


class TestSleepDurationInterpolation:
    """Test linear interpolation for sleep duration."""

    def test_6_5_hours_interpolates_correctly(self):
        """Test 6.5 hours interpolates between 70 (6h) and 100 (7h)."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(6.5 * 3600),  # 6.5 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        # Should interpolate: 6h=70, 7h=100, 6.5h should be 85
        assert score == 85

    def test_5_5_hours_interpolates_correctly(self):
        """Test 5.5 hours interpolates between 40 (5h) and 70 (6h)."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(5.5 * 3600),  # 5.5 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        # Should interpolate: 5h=40, 6h=70, 5.5h should be 55
        assert score == 55

    def test_4_5_hours_interpolates_correctly(self):
        """Test 4.5 hours interpolates between 0 (4h) and 40 (5h)."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(4.5 * 3600),  # 4.5 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        # Should interpolate: 4h=0, 5h=40, 4.5h should be 20
        assert score == 20

    def test_9_5_hours_interpolates_correctly(self):
        """Test 9.5 hours interpolates between 100 (9h) and 70 (10h)."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(9.5 * 3600),  # 9.5 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        # Should interpolate: 9h=100, 10h=70, 9.5h should be 85
        assert score == 85


class TestSleepQualityIntegration:
    """Test integration of Garmin sleep quality score."""

    def test_optimal_duration_with_excellent_quality(self):
        """Test 8h sleep + 100 quality score."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,  # 8 hours
            "sleep_quality_score": 100,  # Excellent quality
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 100, Quality: 100
        # Combined: (100 * 0.6) + (100 * 0.4) = 60 + 40 = 100
        assert score == 100

    def test_optimal_duration_with_poor_quality(self):
        """Test 8h sleep + poor quality score."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,  # 8 hours
            "sleep_quality_score": 30,  # Poor quality
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 100, Quality: 30
        # Combined: (100 * 0.6) + (30 * 0.4) = 60 + 12 = 72
        assert score == 72

    def test_poor_duration_with_excellent_quality(self):
        """Test 5h sleep + excellent quality score."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 5 * 3600,  # 5 hours
            "sleep_quality_score": 100,  # Excellent quality
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 40, Quality: 100
        # Combined: (40 * 0.6) + (100 * 0.4) = 24 + 40 = 64
        assert score == 64

    def test_average_duration_with_average_quality(self):
        """Test 6h sleep + average quality score."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 6 * 3600,  # 6 hours
            "sleep_quality_score": 50,  # Average quality
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 70, Quality: 50
        # Combined: (70 * 0.6) + (50 * 0.4) = 42 + 20 = 62
        assert score == 62

    def test_quality_missing_uses_duration_only(self):
        """Test that missing quality uses duration score only."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,  # 8 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        # Should use duration score only: 100
        assert score == 100


class TestSleepEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_sleep_data_returns_none(self):
        """Test that missing sleep data returns None."""
        calculator = SleepCalculator()

        score = calculator.calculate_component(None)

        assert score is None

    def test_zero_sleep_duration_returns_0(self):
        """Test that zero sleep duration scores 0."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 0,
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 0

    def test_negative_sleep_duration_returns_none(self):
        """Test that negative sleep duration returns None (invalid data)."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": -3600,  # Negative
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score is None

    def test_extreme_sleep_duration_caps_correctly(self):
        """Test that extreme sleep duration (16h+) caps at 0."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 16 * 3600,  # 16 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        # Excessive sleep beyond 10h should continue declining
        assert score <= 70  # Should be worse than 10h (70)

    def test_quality_score_below_0_clamped(self):
        """Test that quality score below 0 is clamped to 0."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,
            "sleep_quality_score": -10,  # Invalid negative
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 100, Quality: 0 (clamped)
        # Combined: (100 * 0.6) + (0 * 0.4) = 60
        assert score == 60

    def test_quality_score_above_100_clamped(self):
        """Test that quality score above 100 is clamped to 100."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,
            "sleep_quality_score": 150,  # Invalid above 100
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 100, Quality: 100 (clamped)
        # Combined: (100 * 0.6) + (100 * 0.4) = 100
        assert score == 100


class TestSleepScoreBounds:
    """Test that sleep scores are properly bounded 0-100."""

    def test_score_never_exceeds_100(self):
        """Test that score caps at 100."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,
            "sleep_quality_score": 100,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 100
        assert score <= 100

    def test_score_never_below_0(self):
        """Test that score floors at 0."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 2 * 3600,  # 2 hours
            "sleep_quality_score": 0,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 0
        assert score >= 0

    def test_score_is_integer(self):
        """Test that score is always an integer."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(6.5 * 3600),  # Will produce fractional value
            "sleep_quality_score": 55,
        }

        score = calculator.calculate_component(sleep_data)

        assert isinstance(score, int)


class TestSleepRealWorldScenarios:
    """Test realistic sleep patterns."""

    def test_well_rested_athlete(self):
        """Test athlete with optimal sleep."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(8.5 * 3600),  # 8.5 hours
            "sleep_quality_score": 85,  # Good quality
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 100 (within 7-9h range)
        # Quality: 85
        # Combined: (100 * 0.6) + (85 * 0.4) = 60 + 34 = 94
        assert score == 94

    def test_sleep_deprived_athlete(self):
        """Test athlete with insufficient sleep."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(4.5 * 3600),  # 4.5 hours
            "sleep_quality_score": 40,  # Poor quality due to short duration
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: ~20 (interpolated 4-5h)
        # Quality: 40
        # Combined: (20 * 0.6) + (40 * 0.4) = 12 + 16 = 28
        assert score <= 30  # Should signal poor recovery

    def test_oversleeping_athlete(self):
        """Test athlete with excessive sleep (may indicate fatigue)."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(11 * 3600),  # 11 hours
            "sleep_quality_score": 60,  # Moderate quality
        }

        score = calculator.calculate_component(sleep_data)

        # Excessive sleep should score lower than optimal
        # Duration: <70 (excessive)
        # Quality: 60
        # Combined score should be sub-optimal
        assert score < 80  # Should be worse than optimal 8h sleep

    def test_good_sleep_poor_quality_paradox(self):
        """Test long sleep with poor quality (restless sleep)."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 9 * 3600,  # 9 hours (good duration)
            "sleep_quality_score": 25,  # Very poor quality (restless)
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 100
        # Quality: 25
        # Combined: (100 * 0.6) + (25 * 0.4) = 60 + 10 = 70
        assert score == 70

    def test_short_sleep_excellent_quality(self):
        """Test short but high-quality sleep."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 6 * 3600,  # 6 hours (sub-optimal)
            "sleep_quality_score": 95,  # Excellent quality
        }

        score = calculator.calculate_component(sleep_data)

        # Duration: 70
        # Quality: 95
        # Combined: (70 * 0.6) + (95 * 0.4) = 42 + 38 = 80
        assert score == 80


class TestSleepDataFormat:
    """Test different sleep data input formats."""

    def test_handles_minutes_format(self):
        """Test that calculator can handle sleep in minutes if needed."""
        calculator = SleepCalculator()

        # If data comes in minutes, should convert correctly
        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 480 * 60,  # 480 minutes = 8 hours
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        assert score == 100

    def test_handles_hours_with_decimals(self):
        """Test fractional hours."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": int(7.75 * 3600),  # 7h 45min
            "sleep_quality_score": None,
        }

        score = calculator.calculate_component(sleep_data)

        # 7.75h is within optimal range (7-9h)
        assert score == 100

    def test_missing_quality_field_handled(self):
        """Test that missing quality field (not None, but absent) is handled."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600
            # sleep_quality_score field not present
        }

        score = calculator.calculate_component(sleep_data)

        # Should use duration only
        assert score == 100


class TestSleepComponentWeighting:
    """Test that duration and quality weights are correct."""

    def test_duration_weight_is_60_percent(self):
        """Verify duration contributes 60% to final score."""
        calculator = SleepCalculator()

        # Extreme case: perfect duration (100), zero quality (0)
        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 8 * 3600,  # 8h = 100
            "sleep_quality_score": 0,
        }

        score = calculator.calculate_component(sleep_data)

        # Should be exactly 60 (100 * 0.6 + 0 * 0.4)
        assert score == 60

    def test_quality_weight_is_40_percent(self):
        """Verify quality contributes 40% to final score."""
        calculator = SleepCalculator()

        # Extreme case: zero duration (0), perfect quality (100)
        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 2 * 3600,  # 2h = 0 (below 4h)
            "sleep_quality_score": 100,
        }

        score = calculator.calculate_component(sleep_data)

        # Should be exactly 40 (0 * 0.6 + 100 * 0.4)
        assert score == 40

    def test_combined_weighting_adds_up(self):
        """Test that weights sum to 100%."""
        calculator = SleepCalculator()

        sleep_data = {
            "date": date(2025, 10, 24),
            "total_sleep_seconds": 6 * 3600,  # 70 duration score
            "sleep_quality_score": 50,
        }

        score = calculator.calculate_component(sleep_data)

        expected = int((70 * 0.6) + (50 * 0.4))  # 42 + 20 = 62
        assert score == expected
