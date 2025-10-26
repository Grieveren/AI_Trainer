"""
Unit tests for Resting Heart Rate component of recovery score.

HR Component Algorithm:
- Calculate 7-day rolling average resting HR
- Compare today's HR to average (INVERSE relationship - lower is better):
  - -5% or more below average = 100 (excellent recovery)
  - At average (0% deviation) = 50 (normal)
  - +5% above average = 25
  - +10% or more above average = 0 (poor recovery)
- Linear interpolation between points
"""

from datetime import date

from src.services.recovery.hr_calculator import HRCalculator


class TestHRComponentBasics:
    """Test basic HR component calculation."""

    def test_hr_5_percent_below_average_scores_100(self):
        """Test that HR 5% below average scores 100."""
        calculator = HRCalculator()

        # 7-day average = 60bpm, today = 57bpm (-5%)
        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 57  # -5% below 60

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 100

    def test_hr_at_average_scores_50(self):
        """Test that HR at average scores 50."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 60  # Exactly at average

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 50

    def test_hr_10_percent_above_average_scores_0(self):
        """Test that HR 10% above average scores 0."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 66  # +10% above 60

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 0


class TestHRLinearInterpolation:
    """Test linear interpolation for HR scoring."""

    def test_hr_2_5_percent_below_average(self):
        """Test HR 2.5% below average interpolates correctly."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 58  # -2.5% (rounded from 58.5)

        score = calculator.calculate_component(current_hr, historical_data)

        # Should interpolate between 50 (0%) and 100 (-5%)
        # -2.5% is halfway, so score should be 75
        assert score == 75

    def test_hr_2_5_percent_above_average(self):
        """Test HR 2.5% above average scores correctly."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 62  # +2.5% (rounded from 61.5)

        score = calculator.calculate_component(current_hr, historical_data)

        # Should interpolate between 50 (0%) and 25 (+5%)
        # +2.5% is halfway, so score should be 37 or 38
        assert 37 <= score <= 38

    def test_hr_5_percent_above_average(self):
        """Test HR 5% above average scores 25."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 63  # +5% above 60

        score = calculator.calculate_component(current_hr, historical_data)

        # At +5%, score should be 25 (halfway between 50 at 0% and 0 at +10%)
        assert score == 25

    def test_hr_10_percent_below_average_caps_at_100(self):
        """Test that HR below -5% caps at 100."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 54  # -10% below 60

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 100

    def test_hr_15_percent_above_average_caps_at_0(self):
        """Test that HR above +10% caps at 0."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 69  # +15% above 60

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 0


class TestHRRollingAverage:
    """Test 7-day rolling average calculation for HR."""

    def test_calculates_7_day_average_correctly(self):
        """Test that 7-day rolling average is calculated correctly."""
        calculator = HRCalculator()

        # Mix of values averaging to 60
        historical_data = [
            {"date": date(2025, 10, 17), "resting_hr": 55},
            {"date": date(2025, 10, 18), "resting_hr": 60},
            {"date": date(2025, 10, 19), "resting_hr": 65},
            {"date": date(2025, 10, 20), "resting_hr": 58},
            {"date": date(2025, 10, 21), "resting_hr": 62},
            {"date": date(2025, 10, 22), "resting_hr": 60},
            {"date": date(2025, 10, 23), "resting_hr": 60},
        ]
        # Average = (55+60+65+58+62+60+60) / 7 = 420/7 = 60

        current_hr = 60

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 50  # At average


class TestHREdgeCases:
    """Test edge cases and error handling for HR."""

    def test_insufficient_data_returns_none(self):
        """Test that insufficient historical data returns None."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, 22), "resting_hr": 60},
            {"date": date(2025, 10, 23), "resting_hr": 60},
        ]

        current_hr = 60

        score = calculator.calculate_component(current_hr, historical_data)

        assert score is None

    def test_missing_current_hr_returns_none(self):
        """Test that missing current HR returns None."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = None

        score = calculator.calculate_component(current_hr, historical_data)

        assert score is None

    def test_handles_missing_hr_values_in_history(self):
        """Test that days with missing HR are excluded from average."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, 17), "resting_hr": 60},
            {"date": date(2025, 10, 18), "resting_hr": None},
            {"date": date(2025, 10, 19), "resting_hr": 60},
            {"date": date(2025, 10, 20), "resting_hr": 60},
            {"date": date(2025, 10, 21), "resting_hr": None},
            {"date": date(2025, 10, 22), "resting_hr": 60},
            {"date": date(2025, 10, 23), "resting_hr": 60},
        ]

        current_hr = 60

        score = calculator.calculate_component(current_hr, historical_data)

        # Should calculate from 5 valid days
        assert score == 50

    def test_too_few_valid_days_returns_none(self):
        """Test that less than 4 valid days returns None."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, 17), "resting_hr": 60},
            {"date": date(2025, 10, 18), "resting_hr": None},
            {"date": date(2025, 10, 19), "resting_hr": None},
            {"date": date(2025, 10, 20), "resting_hr": 60},
            {"date": date(2025, 10, 21), "resting_hr": None},
            {"date": date(2025, 10, 22), "resting_hr": None},
            {"date": date(2025, 10, 23), "resting_hr": 60},
        ]

        current_hr = 60

        score = calculator.calculate_component(current_hr, historical_data)

        assert score is None


class TestHRInverseRelationship:
    """Test that HR has inverse relationship (lower is better)."""

    def test_lower_hr_better_score(self):
        """Test that lower HR gives better score than higher HR."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]

        score_lower = calculator.calculate_component(57, historical_data)  # -5%
        score_higher = calculator.calculate_component(66, historical_data)  # +10%

        assert score_lower > score_higher
        assert score_lower == 100
        assert score_higher == 0

    def test_hr_increase_decreases_score(self):
        """Test that increasing HR decreases score."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]

        scores = []
        for hr_offset in range(-5, 11):  # -5% to +10%
            hr = 60 + int(60 * hr_offset / 100)
            score = calculator.calculate_component(hr, historical_data)
            scores.append(score)

        # Scores should be monotonically decreasing
        for i in range(len(scores) - 1):
            assert (
                scores[i] >= scores[i + 1]
            ), f"Score at index {i} should be >= score at {i+1}"


class TestHRRealWorldScenarios:
    """Test realistic HR patterns."""

    def test_well_rested_athlete(self):
        """Test athlete with low resting HR indicating good recovery."""
        calculator = HRCalculator()

        # Athlete with stable HR around 55
        historical_data = [
            {"date": date(2025, 10, 17), "resting_hr": 55},
            {"date": date(2025, 10, 18), "resting_hr": 54},
            {"date": date(2025, 10, 19), "resting_hr": 56},
            {"date": date(2025, 10, 20), "resting_hr": 55},
            {"date": date(2025, 10, 21), "resting_hr": 55},
            {"date": date(2025, 10, 22), "resting_hr": 54},
            {"date": date(2025, 10, 23), "resting_hr": 56},
        ]
        # Average ≈ 55
        current_hr = 52  # Well below average

        score = calculator.calculate_component(current_hr, historical_data)

        # -5.5% below average, should score 100
        assert score == 100

    def test_fatigued_athlete(self):
        """Test athlete with elevated HR indicating fatigue."""
        calculator = HRCalculator()

        # Athlete with rising HR from fatigue
        historical_data = [
            {"date": date(2025, 10, 17), "resting_hr": 52},
            {"date": date(2025, 10, 18), "resting_hr": 53},
            {"date": date(2025, 10, 19), "resting_hr": 54},
            {"date": date(2025, 10, 20), "resting_hr": 55},
            {"date": date(2025, 10, 21), "resting_hr": 56},
            {"date": date(2025, 10, 22), "resting_hr": 57},
            {"date": date(2025, 10, 23), "resting_hr": 58},
        ]
        # Average ≈ 55
        current_hr = 62  # Elevated

        score = calculator.calculate_component(current_hr, historical_data)

        # +12.7% above average, should floor at 0
        assert score == 0

    def test_illness_detection_via_elevated_hr(self):
        """Test that illness causes elevated HR and low score."""
        calculator = HRCalculator()

        # Normal baseline
        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 55} for i in range(17, 24)
        ]

        # Sudden spike (illness)
        current_hr = 68  # +23.6% above normal

        score = calculator.calculate_component(current_hr, historical_data)

        # Should score 0 (strong signal to rest)
        assert score == 0


class TestHRScoreBounds:
    """Test that HR scores are properly bounded 0-100."""

    def test_score_never_exceeds_100(self):
        """Test that score caps at 100."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 80} for i in range(17, 24)
        ]
        current_hr = 40  # -50% below average

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 100
        assert score <= 100

    def test_score_never_below_0(self):
        """Test that score floors at 0."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 50} for i in range(17, 24)
        ]
        current_hr = 80  # +60% above average

        score = calculator.calculate_component(current_hr, historical_data)

        assert score == 0
        assert score >= 0

    def test_score_is_integer(self):
        """Test that score is always an integer."""
        calculator = HRCalculator()

        historical_data = [
            {"date": date(2025, 10, i), "resting_hr": 60} for i in range(17, 24)
        ]
        current_hr = 62  # Will produce fractional intermediate value

        score = calculator.calculate_component(current_hr, historical_data)

        assert isinstance(score, int)
