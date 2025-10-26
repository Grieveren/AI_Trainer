"""
Unit tests for Workout Recommendation Rationale Generation.

Rationale Generation Algorithm:
Generates human-readable explanations for workout recommendations based on:
- Recovery score and component breakdown
- Recent training history
- Anomaly warnings
- Periodization phase
- Training goals

Rationale should:
- Explain WHY this workout was recommended
- Connect recommendation to recovery data
- Provide context for training decisions
- Include safety warnings when applicable
- Motivate the athlete when appropriate
"""

from datetime import date, timedelta

from src.services.recommendations.rationale_service import RationaleService


class TestBasicRationale:
    """Test basic rationale generation for different scenarios."""

    def test_excellent_recovery_rationale_is_encouraging(self):
        """Test that excellent recovery generates encouraging rationale."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "intervals",
            "recovery_score": 95,
            "recovery_status": "green",
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should be encouraging and explain why hard workout is appropriate
        assert "excellent" in rationale.lower() or "great" in rationale.lower()
        assert "recovery" in rationale.lower()
        assert "hard" in rationale.lower() or "interval" in rationale.lower()

    def test_poor_recovery_rationale_explains_rest(self):
        """Test that poor recovery explains need for rest."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "recovery",
            "recovery_score": 25,
            "recovery_status": "red",
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain why rest is needed
        assert "rest" in rationale.lower() or "recovery" in rationale.lower()
        assert "low" in rationale.lower() or "poor" in rationale.lower()

    def test_moderate_recovery_rationale_explains_steady_state(self):
        """Test that moderate recovery explains steady-state recommendation."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "tempo",
            "recovery_score": 60,
            "recovery_status": "yellow",
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain moderate approach
        assert "moderate" in rationale.lower() or "steady" in rationale.lower()
        assert len(rationale) > 50  # Should be substantive


class TestComponentExplanations:
    """Test that rationale explains recovery component scores."""

    def test_explains_low_hrv_component(self):
        """Test that rationale explains low HRV contribution."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "recovery",
            "recovery_score": 35,
            "component_scores": {
                "hrv_score": 10,  # Very low
                "hr_score": 50,
                "sleep_score": 70,
                "acwr_score": 80,
            },
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should mention HRV as key factor
        assert (
            "hrv" in rationale.lower() or "heart rate variability" in rationale.lower()
        )

    def test_explains_elevated_hr_component(self):
        """Test that rationale explains elevated resting HR."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "easy",
            "recovery_score": 40,
            "component_scores": {
                "hrv_score": 70,
                "hr_score": 15,  # Very low (elevated actual HR)
                "sleep_score": 60,
                "acwr_score": 70,
            },
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should mention elevated HR
        assert "heart rate" in rationale.lower() or "hr" in rationale.lower()

    def test_explains_poor_sleep_component(self):
        """Test that rationale explains poor sleep impact."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "easy",
            "recovery_score": 50,
            "component_scores": {
                "hrv_score": 70,
                "hr_score": 65,
                "sleep_score": 25,  # Very poor
                "acwr_score": 75,
            },
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should mention sleep deficit
        assert "sleep" in rationale.lower()

    def test_explains_high_acwr_component(self):
        """Test that rationale explains training load concerns."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "recovery",
            "recovery_score": 55,
            "component_scores": {
                "hrv_score": 75,
                "hr_score": 70,
                "sleep_score": 80,
                "acwr_score": 10,  # High load warning
            },
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should mention training load
        assert "load" in rationale.lower() or "training" in rationale.lower()


class TestAnomalyWarnings:
    """Test that rationale includes anomaly warnings."""

    def test_includes_illness_warning(self):
        """Test that illness warnings are included in rationale."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "rest",
            "recovery_score": 30,
            "anomaly_warnings": [
                "Critical HRV drop detected: -22% below baseline. Possible illness."
            ],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should include illness warning
        assert "illness" in rationale.lower() or "warning" in rationale.lower()

    def test_includes_overtraining_warning(self):
        """Test that overtraining warnings are included."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "recovery",
            "recovery_score": 35,
            "anomaly_warnings": [
                "Overtraining pattern detected: Persistent HRV suppression over multiple days."
            ],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should include overtraining context
        assert "overtraining" in rationale.lower() or "persistent" in rationale.lower()

    def test_includes_multiple_warnings(self):
        """Test that multiple warnings are all addressed."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "rest",
            "recovery_score": 20,
            "anomaly_warnings": [
                "Low HRV detected",
                "Elevated resting HR",
                "Poor sleep quality",
            ],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should mention multiple factors
        warnings_count = sum(
            [
                "hrv" in rationale.lower(),
                "heart rate" in rationale.lower() or "hr" in rationale.lower(),
                "sleep" in rationale.lower(),
            ]
        )

        assert warnings_count >= 2  # At least 2 of the 3 factors mentioned


class TestTrainingContext:
    """Test that rationale includes training context."""

    def test_explains_recent_hard_workout(self):
        """Test that rationale explains recent hard training."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "easy",
            "recovery_score": 55,
            "recent_workouts": [
                {
                    "date": date.today() - timedelta(days=1),
                    "workout_type": "intervals",
                    "intensity": "hard",
                }
            ],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should reference recent hard workout
        assert "recent" in rationale.lower() or "yesterday" in rationale.lower()

    def test_explains_consecutive_hard_days(self):
        """Test that rationale warns about consecutive hard days."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "intervals",
            "recovery_score": 75,
            "recent_workouts": [
                {
                    "date": date.today() - timedelta(days=1),
                    "workout_type": "threshold",
                    "intensity": "hard",
                },
                {
                    "date": date.today() - timedelta(days=2),
                    "workout_type": "hills",
                    "intensity": "hard",
                },
            ],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should caution about back-to-back hard days
        assert (
            "consecutive" in rationale.lower()
            or "careful" in rationale.lower()
            or "caution" in rationale.lower()
        )

    def test_explains_rest_day_pattern(self):
        """Test that rationale recognizes good rest patterns."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "intervals",
            "recovery_score": 90,
            "recent_workouts": [
                {
                    "date": date.today() - timedelta(days=1),
                    "workout_type": "recovery",
                    "intensity": "easy",
                },
                {
                    "date": date.today() - timedelta(days=2),
                    "workout_type": "rest",
                    "intensity": "rest",
                },
            ],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should acknowledge good recovery
        assert "ready" in rationale.lower() or "recovered" in rationale.lower()


class TestPeriodizationExplanations:
    """Test that rationale explains periodization context."""

    def test_explains_base_phase_aerobic_focus(self):
        """Test that rationale explains base building focus."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "aerobic",
            "recovery_score": 70,
            "phase": "base",
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain base building context
        assert (
            "base" in rationale.lower()
            or "aerobic" in rationale.lower()
            or "endurance" in rationale.lower()
        )

    def test_explains_build_phase_intensity(self):
        """Test that rationale explains build phase intensity."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "threshold",
            "recovery_score": 80,
            "phase": "build",
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain build phase progression
        assert "build" in rationale.lower() or "intensity" in rationale.lower()

    def test_explains_taper_phase_maintenance(self):
        """Test that rationale explains taper strategy."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "intervals",
            "recovery_score": 85,
            "phase": "taper",
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain taper approach
        assert (
            "taper" in rationale.lower()
            or "maintain" in rationale.lower()
            or "sharp" in rationale.lower()
        )


class TestMotivationalElements:
    """Test that rationale includes appropriate motivation."""

    def test_encourages_when_recovery_is_excellent(self):
        """Test that excellent recovery includes encouragement."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "vo2max",
            "recovery_score": 98,
        }

        rationale = service.generate_rationale(recommendation_data)

        encouraging_words = ["great", "excellent", "ready", "strong", "well-recovered"]
        has_encouragement = any(word in rationale.lower() for word in encouraging_words)

        assert has_encouragement

    def test_supportive_when_recovery_is_poor(self):
        """Test that poor recovery includes supportive messaging."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "rest",
            "recovery_score": 20,
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should be supportive, not discouraging
        supportive_words = ["rest", "recover", "important", "tomorrow", "patience"]
        has_support = any(word in rationale.lower() for word in supportive_words)

        assert has_support


class TestRationaleStructure:
    """Test that rationale has proper structure and completeness."""

    def test_rationale_has_minimum_length(self):
        """Test that rationale is substantive, not one-liners."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "tempo",
            "recovery_score": 65,
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should be at least a full sentence
        assert len(rationale) >= 50

    def test_rationale_includes_action_statement(self):
        """Test that rationale includes clear action."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "intervals",
            "recovery_score": 85,
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should have action words
        action_words = ["recommend", "suggest", "do", "perform", "complete"]
        has_action = any(word in rationale.lower() for word in action_words)

        assert has_action

    def test_rationale_includes_reasoning(self):
        """Test that rationale explains the "why"."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "steady",
            "recovery_score": 60,
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should have reasoning words
        reasoning_words = ["because", "since", "as", "given", "based on"]
        has_reasoning = any(word in rationale.lower() for word in reasoning_words)

        assert has_reasoning


class TestEdgeCases:
    """Test edge cases in rationale generation."""

    def test_handles_missing_component_scores(self):
        """Test rationale works without component score breakdown."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "tempo",
            "recovery_score": 65
            # No component_scores provided
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should still generate valid rationale
        assert rationale is not None
        assert len(rationale) > 0

    def test_handles_missing_recent_workouts(self):
        """Test rationale works without workout history."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "intervals",
            "recovery_score": 80
            # No recent_workouts provided
        }

        rationale = service.generate_rationale(recommendation_data)

        assert rationale is not None
        assert len(rationale) > 0

    def test_handles_missing_anomaly_warnings(self):
        """Test rationale works without anomaly data."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "steady",
            "recovery_score": 60
            # No anomaly_warnings
        }

        rationale = service.generate_rationale(recommendation_data)

        assert rationale is not None
        assert len(rationale) > 0


class TestRealWorldRationales:
    """Test realistic rationale scenarios."""

    def test_post_race_recovery_rationale(self):
        """Test rationale for post-race recovery week."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "easy",
            "recovery_score": 45,
            "recent_workouts": [
                {
                    "date": date.today() - timedelta(days=2),
                    "workout_type": "race",
                    "intensity": "race",
                }
            ],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should reference race and explain recovery need
        assert "race" in rationale.lower() or "event" in rationale.lower()
        assert "recover" in rationale.lower()

    def test_illness_detection_rationale(self):
        """Test rationale when illness is detected."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "rest",
            "recovery_score": 25,
            "anomaly_warnings": [
                "Critical HRV drop: -25% below baseline. Possible illness."
            ],
            "component_scores": {
                "hrv_score": 0,
                "hr_score": 10,
                "sleep_score": 50,
                "acwr_score": 80,
            },
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should clearly recommend rest and mention health
        assert "rest" in rationale.lower()
        assert (
            "health" in rationale.lower()
            or "illness" in rationale.lower()
            or "sick" in rationale.lower()
        )

    def test_taper_week_rationale(self):
        """Test rationale for pre-race taper."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "easy",
            "recovery_score": 70,
            "phase": "taper",
            "days_until_race": 5,
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain taper strategy
        assert "taper" in rationale.lower() or "race" in rationale.lower()
        assert "fresh" in rationale.lower() or "ready" in rationale.lower()

    def test_overreached_athlete_rationale(self):
        """Test rationale for overreached athlete."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "recovery",
            "recovery_score": 35,
            "component_scores": {
                "hrv_score": 20,
                "hr_score": 25,
                "sleep_score": 40,
                "acwr_score": 70,
            },
            "anomaly_warnings": ["Overtraining pattern: Persistent HRV suppression"],
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain recovery need and avoid burnout
        assert "recover" in rationale.lower() or "rest" in rationale.lower()
        assert len(rationale) > 100  # Should be detailed explanation


class TestRationaleConsistency:
    """Test that rationale is consistent with recommendation."""

    def test_rest_recommendation_has_rest_rationale(self):
        """Test that rest recommendation explains rest clearly."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "rest",
            "workout_type": "rest",
            "recovery_score": 30,
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should clearly state rest is needed
        assert "rest" in rationale.lower()

    def test_hard_recommendation_explains_readiness(self):
        """Test that hard recommendation explains athlete readiness."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "hard",
            "workout_type": "intervals",
            "recovery_score": 90,
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain why hard workout is appropriate
        assert (
            "ready" in rationale.lower()
            or "recovered" in rationale.lower()
            or "excellent" in rationale.lower()
        )

    def test_downgraded_intensity_explains_reason(self):
        """Test that intensity downgrades are explained."""
        service = RationaleService()

        recommendation_data = {
            "intensity": "moderate",
            "workout_type": "easy",
            "recovery_score": 72,  # Would normally be hard
            "anomaly_severity": "warning",  # But downgraded
        }

        rationale = service.generate_rationale(recommendation_data)

        # Should explain why intensity was reduced
        assert (
            "caution" in rationale.lower()
            or "warning" in rationale.lower()
            or "conservative" in rationale.lower()
        )
