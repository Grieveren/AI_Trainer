"""
Unit tests for HRV (Heart Rate Variability) component of recovery score.

HRV Component Algorithm:
- Calculate 7-day rolling average HRV
- Compare today's HRV to average:
  - +10% or more above average = 100 (excellent recovery)
  - At average (0% deviation) = 50 (normal)
  - -10% below average = 50 (slightly below)
  - -20% or more below average = 0 (poor recovery)
- Linear interpolation between points
"""

from datetime import date

from src.services.recovery.hrv_calculator import HRVCalculator


class TestHRVComponentBasics:
    """Test basic HRV component calculation."""

    def test_hrv_10_percent_above_average_scores_100(self):
        """Test that HRV 10% above average scores 100."""
        calculator = HRVCalculator()

        # 7-day average = 60ms, today = 66ms (+10%)
        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 60},
            {"date": date(2025, 10, 18), "hrv_ms": 59},
            {"date": date(2025, 10, 19), "hrv_ms": 61},
            {"date": date(2025, 10, 20), "hrv_ms": 60},
            {"date": date(2025, 10, 21), "hrv_ms": 60},
            {"date": date(2025, 10, 22), "hrv_ms": 59},
            {"date": date(2025, 10, 23), "hrv_ms": 61},
        ]
        current_hrv = 66  # 10% above 60

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 100

    def test_hrv_at_average_scores_50(self):
        """Test that HRV at average scores 50."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 60},
            {"date": date(2025, 10, 18), "hrv_ms": 60},
            {"date": date(2025, 10, 19), "hrv_ms": 60},
            {"date": date(2025, 10, 20), "hrv_ms": 60},
            {"date": date(2025, 10, 21), "hrv_ms": 60},
            {"date": date(2025, 10, 22), "hrv_ms": 60},
            {"date": date(2025, 10, 23), "hrv_ms": 60},
        ]
        current_hrv = 60  # Exactly at average

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 50

    def test_hrv_20_percent_below_average_scores_0(self):
        """Test that HRV 20% below average scores 0."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 60},
            {"date": date(2025, 10, 18), "hrv_ms": 60},
            {"date": date(2025, 10, 19), "hrv_ms": 60},
            {"date": date(2025, 10, 20), "hrv_ms": 60},
            {"date": date(2025, 10, 21), "hrv_ms": 60},
            {"date": date(2025, 10, 22), "hrv_ms": 60},
            {"date": date(2025, 10, 23), "hrv_ms": 60},
        ]
        current_hrv = 48  # -20% below 60

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 0


class TestHRVLinearInterpolation:
    """Test linear interpolation between reference points."""

    def test_hrv_5_percent_above_average(self):
        """Test HRV 5% above average interpolates correctly."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 60} for i in range(17, 24)
        ]
        current_hrv = 63  # +5% above 60

        score = calculator.calculate_component(current_hrv, historical_data)

        # Should interpolate between 50 (0%) and 100 (+10%)
        # 5% is halfway, so score should be 75
        assert score == 75

    def test_hrv_15_percent_above_average_caps_at_100(self):
        """Test that HRV above +10% caps at 100."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 60} for i in range(17, 24)
        ]
        current_hrv = 69  # +15% above 60

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 100

    def test_hrv_10_percent_below_average(self):
        """Test HRV 10% below average scores correctly."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 60} for i in range(17, 24)
        ]
        current_hrv = 54  # -10% below 60

        score = calculator.calculate_component(current_hrv, historical_data)

        # At -10%, score should be 25 (halfway between 50 at 0% and 0 at -20%)
        assert score == 25

    def test_hrv_25_percent_below_average_caps_at_0(self):
        """Test that HRV below -20% caps at 0."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 60} for i in range(17, 24)
        ]
        current_hrv = 45  # -25% below 60

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 0


class TestHRVRollingAverage:
    """Test 7-day rolling average calculation."""

    def test_calculates_7_day_average_correctly(self):
        """Test that 7-day rolling average is calculated correctly."""
        calculator = HRVCalculator()

        # Mix of values averaging to 60
        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 50},
            {"date": date(2025, 10, 18), "hrv_ms": 60},
            {"date": date(2025, 10, 19), "hrv_ms": 70},
            {"date": date(2025, 10, 20), "hrv_ms": 55},
            {"date": date(2025, 10, 21), "hrv_ms": 65},
            {"date": date(2025, 10, 22), "hrv_ms": 60},
            {"date": date(2025, 10, 23), "hrv_ms": 60},
        ]
        # Average = (50+60+70+55+65+60+60) / 7 = 420/7 = 60

        current_hrv = 60  # At average

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 50  # At average should score 50

    def test_uses_most_recent_7_days(self):
        """Test that only most recent 7 days are used."""
        calculator = HRVCalculator()

        # Include data older than 7 days (should be ignored)
        historical_data = [
            {"date": date(2025, 10, 10), "hrv_ms": 100},  # Too old, should be ignored
            {"date": date(2025, 10, 17), "hrv_ms": 60},
            {"date": date(2025, 10, 18), "hrv_ms": 60},
            {"date": date(2025, 10, 19), "hrv_ms": 60},
            {"date": date(2025, 10, 20), "hrv_ms": 60},
            {"date": date(2025, 10, 21), "hrv_ms": 60},
            {"date": date(2025, 10, 22), "hrv_ms": 60},
            {"date": date(2025, 10, 23), "hrv_ms": 60},
        ]

        current_hrv = 60

        score = calculator.calculate_component(current_hrv, historical_data)

        # Should use avg of last 7 days = 60, not including the 100
        assert score == 50


class TestHRVEdgeCases:
    """Test edge cases and error handling."""

    def test_insufficient_data_returns_none(self):
        """Test that insufficient historical data returns None."""
        calculator = HRVCalculator()

        # Only 3 days of data (need 7)
        historical_data = [
            {"date": date(2025, 10, 21), "hrv_ms": 60},
            {"date": date(2025, 10, 22), "hrv_ms": 60},
            {"date": date(2025, 10, 23), "hrv_ms": 60},
        ]

        current_hrv = 60

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score is None

    def test_missing_current_hrv_returns_none(self):
        """Test that missing current HRV returns None."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 60} for i in range(17, 24)
        ]
        current_hrv = None

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score is None

    def test_handles_missing_hrv_values_in_history(self):
        """Test that days with missing HRV are excluded from average."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 60},
            {"date": date(2025, 10, 18), "hrv_ms": None},  # Missing
            {"date": date(2025, 10, 19), "hrv_ms": 60},
            {"date": date(2025, 10, 20), "hrv_ms": 60},
            {"date": date(2025, 10, 21), "hrv_ms": None},  # Missing
            {"date": date(2025, 10, 22), "hrv_ms": 60},
            {"date": date(2025, 10, 23), "hrv_ms": 60},
        ]

        current_hrv = 60

        score = calculator.calculate_component(current_hrv, historical_data)

        # Should calculate average from 5 valid days (all 60s)
        # If less than 4 valid days, should return None
        # With 5 valid days, should proceed
        assert score == 50  # At average

    def test_too_few_valid_days_returns_none(self):
        """Test that less than 4 valid days returns None."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 60},
            {"date": date(2025, 10, 18), "hrv_ms": None},
            {"date": date(2025, 10, 19), "hrv_ms": None},
            {"date": date(2025, 10, 20), "hrv_ms": 60},
            {"date": date(2025, 10, 21), "hrv_ms": None},
            {"date": date(2025, 10, 22), "hrv_ms": None},
            {"date": date(2025, 10, 23), "hrv_ms": 60},
        ]

        current_hrv = 60

        score = calculator.calculate_component(current_hrv, historical_data)

        # Only 3 valid days, need at least 4
        assert score is None

    def test_zero_average_returns_none(self):
        """Test that zero average HRV returns None (invalid data)."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 0} for i in range(17, 24)
        ]
        current_hrv = 60

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score is None


class TestHRVScoreBounds:
    """Test that scores are properly bounded 0-100."""

    def test_score_never_exceeds_100(self):
        """Test that score caps at 100."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 50} for i in range(17, 24)
        ]
        current_hrv = 100  # +100% above average

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 100
        assert score <= 100

    def test_score_never_below_0(self):
        """Test that score floors at 0."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 100} for i in range(17, 24)
        ]
        current_hrv = 10  # -90% below average

        score = calculator.calculate_component(current_hrv, historical_data)

        assert score == 0
        assert score >= 0

    def test_score_is_integer(self):
        """Test that score is always an integer."""
        calculator = HRVCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "hrv_ms": 60} for i in range(17, 24)
        ]
        current_hrv = 63  # Should produce fractional intermediate value

        score = calculator.calculate_component(current_hrv, historical_data)

        assert isinstance(score, int)


class TestHRVRealWorldScenarios:
    """Test realistic HRV patterns."""

    def test_recovering_athlete_pattern(self):
        """Test pattern of improving HRV during recovery week."""
        calculator = HRVCalculator()

        # Athlete recovering from hard training
        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 55},  # Post-hard week
            {"date": date(2025, 10, 18), "hrv_ms": 56},  # Starting to recover
            {"date": date(2025, 10, 19), "hrv_ms": 58},
            {"date": date(2025, 10, 20), "hrv_ms": 60},
            {"date": date(2025, 10, 21), "hrv_ms": 62},
            {"date": date(2025, 10, 22), "hrv_ms": 64},
            {"date": date(2025, 10, 23), "hrv_ms": 66},
        ]
        # Average ≈ 60
        current_hrv = 70  # Well recovered

        score = calculator.calculate_component(current_hrv, historical_data)

        # +16.7% above average, should cap at 100
        assert score == 100

    def test_overtrained_athlete_pattern(self):
        """Test pattern of declining HRV in overtrained athlete."""
        calculator = HRVCalculator()

        # Athlete accumulating fatigue
        historical_data = [
            {"date": date(2025, 10, 17), "hrv_ms": 65},
            {"date": date(2025, 10, 18), "hrv_ms": 63},
            {"date": date(2025, 10, 19), "hrv_ms": 60},
            {"date": date(2025, 10, 20), "hrv_ms": 58},
            {"date": date(2025, 10, 21), "hrv_ms": 56},
            {"date": date(2025, 10, 22), "hrv_ms": 54},
            {"date": date(2025, 10, 23), "hrv_ms": 52},
        ]
        # Average ≈ 58
        current_hrv = 45  # Significantly suppressed

        score = calculator.calculate_component(current_hrv, historical_data)

        # -22.4% below average, should floor at 0
        assert score == 0
