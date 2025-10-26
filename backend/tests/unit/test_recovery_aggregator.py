"""
Unit tests for Recovery Score Aggregator.

Recovery Score Algorithm:
- Combines multiple component scores into final 0-100 recovery score
- Component weights:
  - HRV: 40% (strongest indicator of recovery status)
  - HR: 30% (secondary physiological indicator)
  - Sleep: 20% (important but less immediate impact)
  - ACWR: 10% (training load management)

Final Score = (HRV * 0.4) + (HR * 0.3) + (Sleep * 0.2) + (ACWR * 0.1)

Graceful Degradation:
- If component missing, re-weight remaining components proportionally
- If all components missing, return None
- Minimum 2 components required for valid score
"""


from src.services.recovery.recovery_aggregator import RecoveryAggregator


class TestRecoveryScoreWeighting:
    """Test that component weights are correctly applied."""

    def test_all_perfect_scores_100(self):
        """Test that all perfect component scores yield 100."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 100,
            "hr_score": 100,
            "sleep_score": 100,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        assert final_score == 100

    def test_all_zero_scores_0(self):
        """Test that all zero component scores yield 0."""
        aggregator = RecoveryAggregator()

        components = {"hrv_score": 0, "hr_score": 0, "sleep_score": 0, "acwr_score": 0}

        final_score = aggregator.calculate_final_score(components)

        assert final_score == 0

    def test_hrv_weight_is_40_percent(self):
        """Verify HRV contributes 40% to final score."""
        aggregator = RecoveryAggregator()

        # Only HRV = 100, rest = 0
        components = {
            "hrv_score": 100,
            "hr_score": 0,
            "sleep_score": 0,
            "acwr_score": 0,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should be exactly 40 (100 * 0.4)
        assert final_score == 40

    def test_hr_weight_is_30_percent(self):
        """Verify HR contributes 30% to final score."""
        aggregator = RecoveryAggregator()

        # Only HR = 100, rest = 0
        components = {
            "hrv_score": 0,
            "hr_score": 100,
            "sleep_score": 0,
            "acwr_score": 0,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should be exactly 30 (100 * 0.3)
        assert final_score == 30

    def test_sleep_weight_is_20_percent(self):
        """Verify Sleep contributes 20% to final score."""
        aggregator = RecoveryAggregator()

        # Only Sleep = 100, rest = 0
        components = {
            "hrv_score": 0,
            "hr_score": 0,
            "sleep_score": 100,
            "acwr_score": 0,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should be exactly 20 (100 * 0.2)
        assert final_score == 20

    def test_acwr_weight_is_10_percent(self):
        """Verify ACWR contributes 10% to final score."""
        aggregator = RecoveryAggregator()

        # Only ACWR = 100, rest = 0
        components = {
            "hrv_score": 0,
            "hr_score": 0,
            "sleep_score": 0,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should be exactly 10 (100 * 0.1)
        assert final_score == 10

    def test_weights_sum_to_100_percent(self):
        """Test that all weights sum to 100%."""
        aggregator = RecoveryAggregator()

        # All components = 50
        components = {
            "hrv_score": 50,
            "hr_score": 50,
            "sleep_score": 50,
            "acwr_score": 50,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should be exactly 50 (50*0.4 + 50*0.3 + 50*0.2 + 50*0.1 = 50)
        assert final_score == 50


class TestMissingComponentHandling:
    """Test graceful degradation when components are missing."""

    def test_missing_hrv_reweights_remaining(self):
        """Test that missing HRV re-weights remaining components."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": None,
            "hr_score": 100,
            "sleep_score": 100,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # Without HRV (40%), remaining 60% should be re-weighted
        # HR: 30/60 = 50%, Sleep: 20/60 = 33.3%, ACWR: 10/60 = 16.7%
        # Score: 100*0.5 + 100*0.333 + 100*0.167 = 100
        assert final_score == 100

    def test_missing_hr_reweights_remaining(self):
        """Test that missing HR re-weights remaining components."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 100,
            "hr_score": None,
            "sleep_score": 100,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # Without HR (30%), remaining 70% should be re-weighted
        # HRV: 40/70 = 57%, Sleep: 20/70 = 28.6%, ACWR: 10/70 = 14.3%
        assert final_score == 100

    def test_missing_sleep_reweights_remaining(self):
        """Test that missing Sleep re-weights remaining components."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 100,
            "hr_score": 100,
            "sleep_score": None,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # Without Sleep (20%), remaining 80% should be re-weighted
        assert final_score == 100

    def test_missing_acwr_reweights_remaining(self):
        """Test that missing ACWR re-weights remaining components."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 100,
            "hr_score": 100,
            "sleep_score": 100,
            "acwr_score": None,
        }

        final_score = aggregator.calculate_final_score(components)

        # Without ACWR (10%), remaining 90% should be re-weighted
        assert final_score == 100

    def test_only_hrv_and_hr_available(self):
        """Test with only physiological components (HRV + HR)."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 80,
            "hr_score": 60,
            "sleep_score": None,
            "acwr_score": None,
        }

        final_score = aggregator.calculate_final_score(components)

        # HRV: 40/70 = 57.1%, HR: 30/70 = 42.9%
        # Score: 80*0.571 + 60*0.429 = 45.7 + 25.7 = 71.4 ≈ 71
        assert 70 <= final_score <= 72

    def test_minimum_two_components_required(self):
        """Test that at least 2 components are required."""
        aggregator = RecoveryAggregator()

        # Only 1 component available
        components = {
            "hrv_score": 100,
            "hr_score": None,
            "sleep_score": None,
            "acwr_score": None,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should return None (insufficient data)
        assert final_score is None

    def test_all_components_missing_returns_none(self):
        """Test that all missing components returns None."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": None,
            "hr_score": None,
            "sleep_score": None,
            "acwr_score": None,
        }

        final_score = aggregator.calculate_final_score(components)

        assert final_score is None


class TestRecoveryScoreBounds:
    """Test that final scores are properly bounded 0-100."""

    def test_score_never_exceeds_100(self):
        """Test that score caps at 100."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 100,
            "hr_score": 100,
            "sleep_score": 100,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        assert final_score == 100
        assert final_score <= 100

    def test_score_never_below_0(self):
        """Test that score floors at 0."""
        aggregator = RecoveryAggregator()

        components = {"hrv_score": 0, "hr_score": 0, "sleep_score": 0, "acwr_score": 0}

        final_score = aggregator.calculate_final_score(components)

        assert final_score == 0
        assert final_score >= 0

    def test_score_is_integer(self):
        """Test that score is always an integer."""
        aggregator = RecoveryAggregator()

        # Values that produce fractional intermediate result
        components = {
            "hrv_score": 73,
            "hr_score": 68,
            "sleep_score": 82,
            "acwr_score": 91,
        }

        final_score = aggregator.calculate_final_score(components)

        assert isinstance(final_score, int)


class TestRealWorldScenarios:
    """Test realistic recovery score scenarios."""

    def test_excellent_recovery(self):
        """Test athlete with excellent recovery across all metrics."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 100,  # HRV well above baseline
            "hr_score": 100,  # HR well below baseline
            "sleep_score": 94,  # Great sleep (8.5h + good quality)
            "acwr_score": 100,  # Optimal training load
        }

        final_score = aggregator.calculate_final_score(components)

        # Should be near 100: 100*0.4 + 100*0.3 + 94*0.2 + 100*0.1
        # = 40 + 30 + 18.8 + 10 = 98.8 ≈ 99
        assert final_score >= 98

    def test_poor_recovery(self):
        """Test athlete with poor recovery (overreached/ill)."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 0,  # HRV crashed
            "hr_score": 0,  # HR elevated
            "sleep_score": 28,  # Poor sleep (5h)
            "acwr_score": 30,  # High training load
        }

        final_score = aggregator.calculate_final_score(components)

        # Should be low: 0*0.4 + 0*0.3 + 28*0.2 + 30*0.1
        # = 0 + 0 + 5.6 + 3 = 8.6 ≈ 9
        assert final_score <= 10

    def test_mixed_signals(self):
        """Test mixed recovery signals (some good, some bad)."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 75,  # Decent HRV
            "hr_score": 40,  # Elevated HR (warning)
            "sleep_score": 100,  # Excellent sleep
            "acwr_score": 70,  # Slightly elevated load
        }

        final_score = aggregator.calculate_final_score(components)

        # 75*0.4 + 40*0.3 + 100*0.2 + 70*0.1
        # = 30 + 12 + 20 + 7 = 69
        assert 68 <= final_score <= 70

    def test_physiological_override(self):
        """Test that poor physiology overrides good sleep/training."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 0,  # Critical HRV
            "hr_score": 0,  # Critical HR
            "sleep_score": 100,  # Perfect sleep (doesn't override)
            "acwr_score": 100,  # Perfect training load
        }

        final_score = aggregator.calculate_final_score(components)

        # 0*0.4 + 0*0.3 + 100*0.2 + 100*0.1
        # = 0 + 0 + 20 + 10 = 30
        # Even with perfect sleep/training, physiology pulls score down
        assert final_score == 30

    def test_new_athlete_no_training_history(self):
        """Test new athlete (no ACWR data yet)."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 75,
            "hr_score": 75,
            "sleep_score": 80,
            "acwr_score": None,  # No training history yet
        }

        final_score = aggregator.calculate_final_score(components)

        # Without ACWR, reweight: HRV 44.4%, HR 33.3%, Sleep 22.2%
        # 75*0.444 + 75*0.333 + 80*0.222 = 33.3 + 25 + 17.8 = 76.1
        assert 75 <= final_score <= 77

    def test_wearable_malfunction(self):
        """Test partial data due to wearable issues."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": None,  # HRV sensor failed
            "hr_score": 80,
            "sleep_score": 75,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # Without HRV (most important), reweight remaining 60%
        # HR: 50%, Sleep: 33.3%, ACWR: 16.7%
        # 80*0.5 + 75*0.333 + 100*0.167 = 40 + 25 + 16.7 = 81.7
        assert 81 <= final_score <= 82


class TestComponentValidation:
    """Test validation of component score inputs."""

    def test_rejects_scores_above_100(self):
        """Test that component scores above 100 are clamped or rejected."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 150,  # Invalid
            "hr_score": 100,
            "sleep_score": 100,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should clamp to 100 or reject
        assert final_score <= 100

    def test_rejects_scores_below_0(self):
        """Test that component scores below 0 are clamped or rejected."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": -10,  # Invalid
            "hr_score": 100,
            "sleep_score": 100,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should clamp to 0 or reject
        assert final_score is not None
        assert final_score >= 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_components_dict_returns_none(self):
        """Test that empty components dict returns None."""
        aggregator = RecoveryAggregator()

        components = {}

        final_score = aggregator.calculate_final_score(components)

        assert final_score is None

    def test_none_components_dict_returns_none(self):
        """Test that None components dict returns None."""
        aggregator = RecoveryAggregator()

        final_score = aggregator.calculate_final_score(None)

        assert final_score is None

    def test_handles_fractional_component_scores(self):
        """Test handling of fractional component scores."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 75.7,  # Fractional
            "hr_score": 68.3,  # Fractional
            "sleep_score": 82.9,
            "acwr_score": 91.2,
        }

        final_score = aggregator.calculate_final_score(components)

        # Should handle and produce integer result
        assert isinstance(final_score, int)
        assert 0 <= final_score <= 100


class TestRecoveryInterpretation:
    """Test recovery score interpretation thresholds."""

    def test_score_90_plus_is_excellent(self):
        """Test that scores 90+ indicate excellent recovery."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 100,
            "hr_score": 90,
            "sleep_score": 85,
            "acwr_score": 100,
        }

        final_score = aggregator.calculate_final_score(components)

        # 100*0.4 + 90*0.3 + 85*0.2 + 100*0.1 = 40+27+17+10 = 94
        assert final_score >= 90  # Excellent recovery

    def test_score_70_89_is_good(self):
        """Test that scores 70-89 indicate good recovery."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 75,
            "hr_score": 75,
            "sleep_score": 75,
            "acwr_score": 75,
        }

        final_score = aggregator.calculate_final_score(components)

        # All 75s = 75
        assert 70 <= final_score < 90  # Good recovery

    def test_score_50_69_is_moderate(self):
        """Test that scores 50-69 indicate moderate recovery."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 60,
            "hr_score": 60,
            "sleep_score": 60,
            "acwr_score": 60,
        }

        final_score = aggregator.calculate_final_score(components)

        # All 60s = 60
        assert 50 <= final_score < 70  # Moderate recovery

    def test_score_30_49_is_poor(self):
        """Test that scores 30-49 indicate poor recovery."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 40,
            "hr_score": 40,
            "sleep_score": 40,
            "acwr_score": 40,
        }

        final_score = aggregator.calculate_final_score(components)

        # All 40s = 40
        assert 30 <= final_score < 50  # Poor recovery

    def test_score_below_30_is_critical(self):
        """Test that scores below 30 indicate critical recovery status."""
        aggregator = RecoveryAggregator()

        components = {
            "hrv_score": 20,
            "hr_score": 20,
            "sleep_score": 20,
            "acwr_score": 20,
        }

        final_score = aggregator.calculate_final_score(components)

        # All 20s = 20
        assert final_score < 30  # Critical - rest required


class TestReweightingLogic:
    """Test the re-weighting algorithm when components are missing."""

    def test_two_components_split_weight_correctly(self):
        """Test that with 2 components, weights are proportional."""
        aggregator = RecoveryAggregator()

        # Only HRV (40%) and HR (30%) available
        components = {
            "hrv_score": 100,
            "hr_score": 0,
            "sleep_score": None,
            "acwr_score": None,
        }

        final_score = aggregator.calculate_final_score(components)

        # HRV should contribute 40/70 = 57.1%
        # HR should contribute 30/70 = 42.9%
        # Score: 100*0.571 + 0*0.429 = 57.1 ≈ 57
        assert 56 <= final_score <= 58

    def test_three_components_split_weight_correctly(self):
        """Test that with 3 components, weights are proportional."""
        aggregator = RecoveryAggregator()

        # HRV (40%), HR (30%), Sleep (20%) available, no ACWR
        components = {
            "hrv_score": 90,
            "hr_score": 60,
            "sleep_score": 30,
            "acwr_score": None,
        }

        final_score = aggregator.calculate_final_score(components)

        # Total weight: 90%
        # HRV: 40/90 = 44.4%, HR: 30/90 = 33.3%, Sleep: 20/90 = 22.2%
        # Score: 90*0.444 + 60*0.333 + 30*0.222
        # = 40 + 20 + 6.67 = 66.67 ≈ 67
        assert 66 <= final_score <= 68
