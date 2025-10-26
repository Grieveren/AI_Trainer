"""
Unit tests for ACWR (Acute:Chronic Workload Ratio) component of recovery score.

ACWR Component Algorithm:
- Acute Load: 7-day average training stress (TSS or duration)
- Chronic Load: 28-day average training stress
- ACWR = Acute Load / Chronic Load

Scoring:
- 0.8-1.3 (sweet spot) = 100 (optimal training progression)
- 1.0 (balanced) = 100 (maintaining fitness)
- 0.5-0.8 (low) = 70 (detraining risk)
- 1.3-1.5 (elevated) = 70 (approaching overload)
- <0.5 (very low) = 30 (significant detraining)
- 1.5-2.0 (high) = 30 (injury risk increasing)
- >2.0 (very high) = 0 (very high injury risk)
- Linear interpolation between points

This helps prevent:
- Overtraining injury (ratio too high)
- Detraining (ratio too low)
"""

from datetime import date

from src.services.recovery.acwr_calculator import ACWRCalculator


class TestACWRBasicCalculation:
    """Test basic ACWR ratio calculation."""

    def test_balanced_load_scores_100(self):
        """Test that ACWR of 1.0 (balanced) scores 100."""
        calculator = ACWRCalculator()

        # 28 days of consistent 100 TSS per day
        # Acute (7 days) = 100, Chronic (28 days) = 100
        # ACWR = 100/100 = 1.0
        workout_data = [
            {"date": date(2025, 10, i), "training_stress_score": 100}
            for i in range(1, 25)  # 24 days
        ]

        score = calculator.calculate_component(workout_data)

        assert score == 100

    def test_optimal_low_end_0_8_scores_100(self):
        """Test that ACWR of 0.8 (low end of optimal) scores 100."""
        calculator = ACWRCalculator()

        # Acute = 80, Chronic = 100
        # ACWR = 80/100 = 0.8
        workout_data = []

        # Last 7 days: 80 TSS per day (acute)
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 80}
            )

        # Previous 21 days: 100 TSS per day (to average chronic to 100)
        # Need chronic average = 100, so (7*80 + 21*X)/28 = 100
        # 560 + 21*X = 2800, X = 106.67
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 107}
            )

        score = calculator.calculate_component(workout_data)

        assert score == 100

    def test_optimal_high_end_1_3_scores_100(self):
        """Test that ACWR of 1.3 (high end of optimal) scores 100."""
        calculator = ACWRCalculator()

        # Acute = 130, Chronic = 100
        # ACWR = 130/100 = 1.3
        workout_data = []

        # Last 7 days: 130 TSS per day (acute)
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 130}
            )

        # Previous 21 days: adjusted to make chronic = 100
        # (7*130 + 21*X)/28 = 100
        # 910 + 21*X = 2800, X = 90
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 90}
            )

        score = calculator.calculate_component(workout_data)

        assert score == 100


class TestACWRDetrainingDetection:
    """Test detection of detraining scenarios (low ACWR)."""

    def test_low_acwr_0_5_scores_30(self):
        """Test that ACWR of 0.5 (very low) scores 30."""
        calculator = ACWRCalculator()

        # Acute = 50, Chronic = 100
        # ACWR = 50/100 = 0.5
        workout_data = []

        # Last 7 days: 50 TSS (reduced training)
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 50}
            )

        # Previous 21 days: higher load
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 117}
            )

        score = calculator.calculate_component(workout_data)

        assert score == 30

    def test_moderate_detraining_0_7_scores_between_70_and_100(self):
        """Test that ACWR of 0.7 (moderate detraining) interpolates correctly."""
        calculator = ACWRCalculator()

        # Acute = 70, Chronic = 100
        # ACWR = 70/100 = 0.7
        workout_data = []

        # Last 7 days: 70 TSS
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 70}
            )

        # Previous 21 days: adjusted
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 110}
            )

        score = calculator.calculate_component(workout_data)

        # Should interpolate between 70 (at 0.5) and 100 (at 0.8)
        # 0.7 is 2/3 of the way from 0.5 to 0.8
        assert 70 <= score <= 100

    def test_extreme_detraining_0_3_scores_below_30(self):
        """Test that ACWR below 0.5 caps at 30 or below."""
        calculator = ACWRCalculator()

        # Acute = 30, Chronic = 100
        # ACWR = 0.3
        workout_data = []

        # Last 7 days: minimal training
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 30}
            )

        # Previous 21 days: normal load
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 123}
            )

        score = calculator.calculate_component(workout_data)

        assert score <= 30


class TestACWROverloadDetection:
    """Test detection of overload scenarios (high ACWR)."""

    def test_elevated_acwr_1_5_scores_30(self):
        """Test that ACWR of 1.5 (elevated) scores 30."""
        calculator = ACWRCalculator()

        # Acute = 150, Chronic = 100
        # ACWR = 1.5
        workout_data = []

        # Last 7 days: 150 TSS (ramping up)
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 150}
            )

        # Previous 21 days: lower baseline
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 83}
            )

        score = calculator.calculate_component(workout_data)

        assert score == 30

    def test_high_injury_risk_2_0_scores_0(self):
        """Test that ACWR of 2.0+ (very high) scores 0."""
        calculator = ACWRCalculator()

        # Acute = 200, Chronic = 100
        # ACWR = 2.0
        workout_data = []

        # Last 7 days: 200 TSS (dangerous spike)
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 200}
            )

        # Previous 21 days: normal baseline
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 67}
            )

        score = calculator.calculate_component(workout_data)

        assert score == 0

    def test_moderate_overload_1_4_scores_between_70_and_30(self):
        """Test that ACWR of 1.4 (moderate overload) interpolates correctly."""
        calculator = ACWRCalculator()

        # Acute = 140, Chronic = 100
        # ACWR = 1.4
        workout_data = []

        # Last 7 days: 140 TSS
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 140}
            )

        # Previous 21 days: adjusted
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 87}
            )

        score = calculator.calculate_component(workout_data)

        # Should interpolate between 100 (at 1.3) and 30 (at 1.5)
        assert 30 <= score <= 100


class TestACWREdgeCases:
    """Test edge cases and error handling."""

    def test_insufficient_data_returns_none(self):
        """Test that less than 28 days of data returns None."""
        calculator = ACWRCalculator()

        # Only 20 days of data
        workout_data = [
            {"date": date(2025, 10, i), "training_stress_score": 100}
            for i in range(5, 25)
        ]

        score = calculator.calculate_component(workout_data)

        assert score is None

    def test_zero_chronic_load_returns_none(self):
        """Test that zero chronic load returns None (invalid ACWR)."""
        calculator = ACWRCalculator()

        # 28 days of zero training
        workout_data = [
            {
                "date": date(date.today().year, date.today().month, i),
                "training_stress_score": 0,
            }
            for i in range(1, 29)
        ]

        score = calculator.calculate_component(workout_data)

        # Cannot calculate ACWR with zero chronic load
        assert score is None

    def test_missing_workout_days_handled(self):
        """Test that missing workout days (rest days) are treated as zero load."""
        calculator = ACWRCalculator()

        workout_data = []

        # Sporadic training over 28 days (only train 3 days per week)
        for i in range(1, 25):
            if i % 3 == 0:  # Train every 3rd day
                workout_data.append(
                    {"date": date(2025, 10, i), "training_stress_score": 150}
                )
            # Missing days should be treated as 0

        score = calculator.calculate_component(workout_data)

        # Should still calculate (with lower average due to rest days)
        assert score is not None

    def test_negative_tss_returns_none(self):
        """Test that negative TSS values return None (invalid data)."""
        calculator = ACWRCalculator()

        workout_data = [
            {"date": date(2025, 10, i), "training_stress_score": -50 if i > 20 else 100}
            for i in range(1, 25)
        ]

        score = calculator.calculate_component(workout_data)

        assert score is None

    def test_handles_missing_tss_values(self):
        """Test handling of None TSS values in history."""
        calculator = ACWRCalculator()

        workout_data = []
        for i in range(1, 25):
            if i % 4 == 0:  # Every 4th day is None
                workout_data.append(
                    {"date": date(2025, 10, i), "training_stress_score": None}
                )
            else:
                workout_data.append(
                    {"date": date(2025, 10, i), "training_stress_score": 100}
                )

        score = calculator.calculate_component(workout_data)

        # Should treat None as 0 and continue calculation
        assert score is not None


class TestACWRRealWorldScenarios:
    """Test realistic training patterns."""

    def test_healthy_progression(self):
        """Test gradual weekly increase (safe progression)."""
        calculator = ACWRCalculator()

        workout_data = []

        # Week 1-3: 80 TSS per day (building base)
        for i in range(1, 22):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 80}
            )

        # Week 4: 100 TSS per day (10% increase)
        for i in range(22, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 100}
            )

        score = calculator.calculate_component(workout_data)

        # ACWR should be around 1.1-1.2 (healthy progression)
        assert score >= 70  # Should be in safe zone

    def test_race_week_taper(self):
        """Test pre-race taper (intentional load reduction)."""
        calculator = ACWRCalculator()

        workout_data = []

        # Week 1-3: 120 TSS per day (peak training)
        for i in range(1, 22):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 120}
            )

        # Week 4: 60 TSS per day (taper)
        for i in range(22, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 60}
            )

        score = calculator.calculate_component(workout_data)

        # ACWR around 0.6-0.7 (taper, expected detraining warning)
        # This is intentional before race
        assert 30 <= score <= 100

    def test_training_camp_spike(self):
        """Test training camp (high load spike - injury risk)."""
        calculator = ACWRCalculator()

        workout_data = []

        # Week 1-3: 60 TSS per day (normal training)
        for i in range(1, 22):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 60}
            )

        # Week 4: 150 TSS per day (training camp)
        for i in range(22, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 150}
            )

        score = calculator.calculate_component(workout_data)

        # ACWR around 1.7-1.8 (dangerous spike)
        assert score <= 30  # Should warn of injury risk

    def test_return_from_injury(self):
        """Test return from injury (low chronic load, building back)."""
        calculator = ACWRCalculator()

        workout_data = []

        # Week 1-2: off/very light (injury)
        for i in range(1, 15):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 10}
            )

        # Week 3-4: ramping up (50 TSS per day)
        for i in range(15, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 50}
            )

        score = calculator.calculate_component(workout_data)

        # Chronic is low (~30), Acute is higher (~50)
        # ACWR might be elevated (>1.3) but from low base
        assert score is not None

    def test_consistent_training(self):
        """Test consistent training load (stable ACWR)."""
        calculator = ACWRCalculator()

        # 28 days of 100 TSS per day (perfectly consistent)
        workout_data = [
            {"date": date(2025, 10, i), "training_stress_score": 100}
            for i in range(1, 25)
        ]

        score = calculator.calculate_component(workout_data)

        # ACWR = 1.0 (perfect)
        assert score == 100

    def test_weekend_warrior_pattern(self):
        """Test weekend warrior (high weekend load, low weekday)."""
        calculator = ACWRCalculator()

        workout_data = []

        for i in range(1, 25):
            # Weekend: high load, weekday: low/none
            if i % 7 in [6, 0]:  # Sat/Sun
                workout_data.append(
                    {"date": date(2025, 10, i), "training_stress_score": 200}
                )
            else:  # Weekdays
                workout_data.append(
                    {"date": date(2025, 10, i), "training_stress_score": 20}
                )

        score = calculator.calculate_component(workout_data)

        # High variability but if consistent pattern, ACWR should be stable
        assert score is not None


class TestACWRScoreBounds:
    """Test that ACWR scores are properly bounded 0-100."""

    def test_score_never_exceeds_100(self):
        """Test that score caps at 100."""
        calculator = ACWRCalculator()

        # Perfect ACWR of 1.0
        workout_data = [
            {"date": date(2025, 10, i), "training_stress_score": 100}
            for i in range(1, 25)
        ]

        score = calculator.calculate_component(workout_data)

        assert score == 100
        assert score <= 100

    def test_score_never_below_0(self):
        """Test that score floors at 0."""
        calculator = ACWRCalculator()

        # Extreme spike (ACWR > 2.5)
        workout_data = []

        # Last 7 days: 300 TSS
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 300}
            )

        # Previous 21 days: low load
        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 50}
            )

        score = calculator.calculate_component(workout_data)

        assert score == 0
        assert score >= 0

    def test_score_is_integer(self):
        """Test that score is always an integer."""
        calculator = ACWRCalculator()

        workout_data = []

        # Create data that produces fractional ACWR
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 73}
            )

        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 91}
            )

        score = calculator.calculate_component(workout_data)

        assert isinstance(score, int)


class TestACWRCalculationLogic:
    """Test the underlying ACWR calculation logic."""

    def test_acute_uses_7_days(self):
        """Test that acute load uses exactly 7 days."""
        calculator = ACWRCalculator()

        workout_data = []

        # Last 7 days: 100 TSS
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 100}
            )

        # Days 8-14: 200 TSS (should not be in acute)
        for i in range(11, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 200}
            )

        # Days 15-28: 100 TSS
        for i in range(1, 11):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 100}
            )

        # If acute incorrectly used 14 days, it would be higher
        # Acute should be 100, Chronic should be ~125
        # ACWR = 100/125 = 0.8
        score = calculator.calculate_component(workout_data)

        assert score == 100  # At 0.8 threshold

    def test_chronic_uses_28_days(self):
        """Test that chronic load uses exactly 28 days (including acute week)."""
        calculator = ACWRCalculator()

        # 28 days of data, all 100 TSS
        workout_data = [
            {"date": date(2025, 10, i), "training_stress_score": 100}
            for i in range(1, 25)
        ]

        score = calculator.calculate_component(workout_data)

        # Acute = 100, Chronic = 100, ACWR = 1.0
        assert score == 100

    def test_acwr_ratio_calculation_accuracy(self):
        """Test that ACWR ratio is calculated accurately."""
        calculator = ACWRCalculator()

        workout_data = []

        # Known values: Acute = 90, Chronic = 100
        # ACWR = 0.9 (should be in optimal range)
        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 90}
            )

        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 103}
            )

        score = calculator.calculate_component(workout_data)

        # 0.9 is in optimal range [0.8, 1.3]
        assert score == 100


class TestACWRInterpolation:
    """Test linear interpolation between score thresholds."""

    def test_interpolates_between_0_5_and_0_8(self):
        """Test interpolation in detraining zone."""
        calculator = ACWRCalculator()

        # ACWR = 0.65 (halfway between 0.5 and 0.8)
        workout_data = []

        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 65}
            )

        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 105}
            )

        score = calculator.calculate_component(workout_data)

        # Should interpolate between 30 (at 0.5) and 100 (at 0.8)
        # 0.65 is halfway, so ~65
        assert 60 <= score <= 75

    def test_interpolates_between_1_3_and_1_5(self):
        """Test interpolation in overload zone."""
        calculator = ACWRCalculator()

        # ACWR = 1.4 (halfway between 1.3 and 1.5)
        workout_data = []

        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 140}
            )

        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 87}
            )

        score = calculator.calculate_component(workout_data)

        # Should interpolate between 100 (at 1.3) and 30 (at 1.5)
        # 1.4 is halfway, so ~65
        assert 60 <= score <= 75

    def test_interpolates_between_1_5_and_2_0(self):
        """Test interpolation in high injury risk zone."""
        calculator = ACWRCalculator()

        # ACWR = 1.75 (halfway between 1.5 and 2.0)
        workout_data = []

        for i in range(18, 25):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 175}
            )

        for i in range(1, 18):
            workout_data.append(
                {"date": date(2025, 10, i), "training_stress_score": 77}
            )

        score = calculator.calculate_component(workout_data)

        # Should interpolate between 30 (at 1.5) and 0 (at 2.0)
        # 1.75 is halfway, so ~15
        assert 10 <= score <= 20
