"""
Integration Test: User Story 1 - Daily Recovery & Recommendations.

Tests the complete end-to-end flow from data ingestion to API response,
verifying all 5 acceptance criteria:

AC1: Daily recovery score calculated from health metrics
AC2: Component scores shown with weighted contributions
AC3: Workout recommendation matches recovery status
AC4: Alternative workout options provided
AC5: User can force recalculation (rate-limited)
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch
from sqlalchemy import select

from src.db.models import User, HealthMetrics, Workout, RecoveryScore
from src.jobs.recovery_score import calculate_user_recovery_score


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(id="test-user-123", email="athlete@example.com", garmin_connected=True)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def excellent_recovery_data(db_session, test_user):
    """Create data representing excellent recovery (green status)."""
    today = date.today()

    # Historical baseline: 7 days of consistent metrics
    for i in range(1, 8):
        past_date = today - timedelta(days=i)
        metrics = HealthMetrics(
            user_id=test_user.id,
            date=past_date,
            hrv_ms=60,  # Baseline HRV
            resting_hr=50,  # Baseline HR
            total_sleep_seconds=8 * 3600,  # 8 hours
            sleep_quality_score=85,
        )
        db_session.add(metrics)

    # Today's metrics: EXCELLENT recovery
    today_metrics = HealthMetrics(
        user_id=test_user.id,
        date=today,
        hrv_ms=66,  # +10% above baseline = 100 score
        resting_hr=47,  # -6% below baseline = 100 score
        total_sleep_seconds=8 * 3600,  # Optimal = 100 score
        sleep_quality_score=90,
    )
    db_session.add(today_metrics)

    # Workout history: Balanced training load (ACWR ~1.0)
    for i in range(1, 29):
        past_date = today - timedelta(days=i)
        workout = Workout(
            user_id=test_user.id,
            workout_date=past_date,
            workout_type="endurance",
            intensity="moderate",
            training_stress_score=100,  # Consistent load
        )
        db_session.add(workout)

    db_session.commit()
    return test_user


@pytest.fixture
def poor_recovery_data(db_session, test_user):
    """Create data representing poor recovery (red status)."""
    today = date.today()

    # Historical baseline
    for i in range(1, 8):
        past_date = today - timedelta(days=i)
        metrics = HealthMetrics(
            user_id=test_user.id,
            date=past_date,
            hrv_ms=60,
            resting_hr=50,
            total_sleep_seconds=8 * 3600,
            sleep_quality_score=85,
        )
        db_session.add(metrics)

    # Today's metrics: POOR recovery
    today_metrics = HealthMetrics(
        user_id=test_user.id,
        date=today,
        hrv_ms=48,  # -20% below baseline = 0 score
        resting_hr=55,  # +10% above baseline = 0 score
        total_sleep_seconds=5 * 3600,  # 5 hours = 40 score
        sleep_quality_score=50,
    )
    db_session.add(today_metrics)

    # Workout history: High training load (ACWR ~2.0)
    # Recent 7 days: 200 TSS/day (acute = 200)
    for i in range(1, 8):
        past_date = today - timedelta(days=i)
        workout = Workout(
            user_id=test_user.id,
            workout_date=past_date,
            workout_type="intervals",
            intensity="hard",
            training_stress_score=200,
        )
        db_session.add(workout)

    # Days 8-28: 100 TSS/day (chronic = 100)
    for i in range(8, 29):
        past_date = today - timedelta(days=i)
        workout = Workout(
            user_id=test_user.id,
            workout_date=past_date,
            workout_type="endurance",
            intensity="moderate",
            training_stress_score=100,
        )
        db_session.add(workout)

    db_session.commit()
    return test_user


class TestUserStory1ExcellentRecovery:
    """AC1-AC4: Test excellent recovery scenario (green → hard training)."""

    def test_ac1_recovery_score_calculated_from_metrics(
        self, db_session, excellent_recovery_data
    ):
        """AC1: Recovery score is calculated from health metrics."""
        user_id = excellent_recovery_data.id
        today = date.today()

        # Execute calculation
        calculate_user_recovery_score(user_id, str(today))

        # Verify score exists
        result = db_session.execute(
            select(RecoveryScore).where(
                RecoveryScore.user_id == user_id, RecoveryScore.date == today
            )
        )
        recovery_score = result.scalar_one_or_none()

        assert recovery_score is not None, "Recovery score should be calculated"
        assert recovery_score.overall_score >= 70, "Should be excellent recovery"
        assert recovery_score.status == "green", "Status should be green"

    def test_ac2_component_scores_with_weighted_contributions(
        self, db_session, excellent_recovery_data
    ):
        """AC2: Component scores shown with proper weighting (40/30/20/10)."""
        user_id = excellent_recovery_data.id
        today = date.today()

        # Execute calculation
        calculate_user_recovery_score(user_id, str(today))

        # Fetch score
        result = db_session.execute(
            select(RecoveryScore).where(
                RecoveryScore.user_id == user_id, RecoveryScore.date == today
            )
        )
        recovery_score = result.scalar_one()

        # Verify all components present
        assert recovery_score.hrv_score is not None, "HRV score should be calculated"
        assert recovery_score.hr_score is not None, "HR score should be calculated"
        assert (
            recovery_score.sleep_score is not None
        ), "Sleep score should be calculated"
        assert recovery_score.acwr_score is not None, "ACWR score should be calculated"

        # Verify excellent components
        assert recovery_score.hrv_score >= 95, "HRV +10% should score ~100"
        assert recovery_score.hr_score >= 95, "HR -6% should score ~100"
        assert recovery_score.sleep_score >= 95, "8 hours should score 100"
        assert recovery_score.acwr_score >= 95, "Balanced load should score 100"

        # Verify weighted calculation (all ~100, so final should be ~100)
        expected_final = int(
            recovery_score.hrv_score * 0.4
            + recovery_score.hr_score * 0.3
            + recovery_score.sleep_score * 0.2
            + recovery_score.acwr_score * 0.1
        )
        assert (
            abs(recovery_score.overall_score - expected_final) <= 2
        ), "Final score should match weighted calculation"

    def test_ac3_green_status_recommends_hard_training(
        self, client, auth_headers, db_session, excellent_recovery_data
    ):
        """AC3: Green recovery status → hard training recommendation."""
        user_id = excellent_recovery_data.id
        today = date.today()

        # Calculate recovery
        calculate_user_recovery_score(user_id, str(today))

        # Fetch recommendation via API
        with patch(
            "src.api.routes.recovery.get_current_user",
            return_value=excellent_recovery_data,
        ):
            response = client.get("/api/recovery/today", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify recommendation matches status
        assert data["status"] == "green", "Status should be green"
        assert (
            data["recommendation"]["intensity"] == "hard"
        ), "Green status should recommend hard training"
        assert data["recommendation"]["workout_type"] is not None
        assert data["recommendation"]["rationale"] is not None
        assert "recovery" in data["recommendation"]["rationale"].lower()

    def test_ac4_alternative_workouts_provided(
        self, client, auth_headers, db_session, excellent_recovery_data
    ):
        """AC4: Alternative workout options are provided."""
        user_id = excellent_recovery_data.id
        today = date.today()

        # Calculate recovery
        calculate_user_recovery_score(user_id, str(today))

        # Fetch recommendation via API
        with patch(
            "src.api.routes.recovery.get_current_user",
            return_value=excellent_recovery_data,
        ):
            response = client.get("/api/recovery/today", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify alternatives exist
        assert "alternatives" in data
        assert isinstance(data["alternatives"], list)
        assert len(data["alternatives"]) > 0, "Should provide alternative workouts"

        # Verify alternative structure
        alt = data["alternatives"][0]
        assert "workout_type" in alt
        assert "intensity" in alt
        assert "rationale" in alt
        assert (
            alt["workout_type"] != data["recommendation"]["workout_type"]
        ), "Alternative should be different from primary"


class TestUserStory1PoorRecovery:
    """Test poor recovery scenario (red → rest)."""

    def test_red_status_recommends_rest(
        self, client, auth_headers, db_session, poor_recovery_data
    ):
        """AC3: Red recovery status → rest recommendation."""
        user_id = poor_recovery_data.id
        today = date.today()

        # Calculate recovery
        calculate_user_recovery_score(user_id, str(today))

        # Fetch recommendation via API
        with patch(
            "src.api.routes.recovery.get_current_user", return_value=poor_recovery_data
        ):
            response = client.get("/api/recovery/today", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify recommendation matches status
        assert data["overall_score"] < 40, "Should be poor recovery"
        assert data["status"] == "red", "Status should be red"
        assert data["recommendation"]["intensity"] in [
            "rest",
            "recovery",
        ], "Red status should recommend rest"


class TestUserStory1Recalculation:
    """AC5: Test forced recalculation with rate limiting."""

    def test_ac5_user_can_force_recalculation(
        self, client, auth_headers, db_session, excellent_recovery_data
    ):
        """AC5: User can trigger recalculation."""
        user_id = excellent_recovery_data.id
        today = date.today()

        # Calculate initial score
        calculate_user_recovery_score(user_id, str(today))

        # Trigger recalculation via API
        with patch(
            "src.api.routes.recovery.get_current_user",
            return_value=excellent_recovery_data,
        ):
            with patch(
                "src.api.routes.recovery.calculate_user_recovery_score.apply_async"
            ) as mock_task:
                mock_task.return_value.id = "task-123"

                response = client.post(
                    f"/api/recovery/{today}/recalculate", headers=auth_headers
                )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "triggered"
        assert data["task_id"] == "task-123"
        assert "recalculation triggered" in data["message"].lower()

    def test_ac5_recalculation_rate_limited(
        self, client, auth_headers, db_session, excellent_recovery_data
    ):
        """AC5: Recalculation is rate limited (5 minute cooldown)."""
        user_id = excellent_recovery_data.id
        today = date.today()

        # First recalculation
        with patch(
            "src.api.routes.recovery.get_current_user",
            return_value=excellent_recovery_data,
        ):
            with patch(
                "src.api.routes.recovery.calculate_user_recovery_score.apply_async"
            ) as mock_task:
                mock_task.return_value.id = "task-123"

                response1 = client.post(
                    f"/api/recovery/{today}/recalculate", headers=auth_headers
                )

        assert response1.status_code == 200

        # Immediate second recalculation (should be rate limited)
        with patch(
            "src.api.routes.recovery.get_current_user",
            return_value=excellent_recovery_data,
        ):
            response2 = client.post(
                f"/api/recovery/{today}/recalculate", headers=auth_headers
            )

        assert response2.status_code == 429, "Should be rate limited"
        data = response2.json()
        assert "rate limit" in data["detail"].lower()


class TestUserStory1EndToEnd:
    """Complete end-to-end integration test."""

    def test_complete_flow_from_metrics_to_recommendation(
        self, client, auth_headers, db_session, excellent_recovery_data
    ):
        """
        Complete User Story 1 flow:
        1. Health metrics + workout history exist
        2. Recovery score is calculated
        3. API returns score with recommendation
        4. Recommendation is personalized and actionable
        """
        user_id = excellent_recovery_data.id
        today = date.today()

        # Step 1: Verify data exists
        metrics_result = db_session.execute(
            select(HealthMetrics).where(
                HealthMetrics.user_id == user_id, HealthMetrics.date == today
            )
        )
        assert metrics_result.scalar_one_or_none() is not None

        workouts_result = db_session.execute(
            select(Workout).where(Workout.user_id == user_id)
        )
        assert len(workouts_result.scalars().all()) > 0

        # Step 2: Calculate recovery
        calculate_user_recovery_score(user_id, str(today))

        # Step 3: Fetch via API
        with patch(
            "src.api.routes.recovery.get_current_user",
            return_value=excellent_recovery_data,
        ):
            response = client.get("/api/recovery/today", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Step 4: Verify complete response structure
        assert "date" in data
        assert "overall_score" in data
        assert "status" in data
        assert "components" in data
        assert "explanation" in data
        assert "recommendation" in data
        assert "alternatives" in data

        # Verify recommendation is actionable
        rec = data["recommendation"]
        assert rec["intensity"] in ["hard", "moderate", "rest", "recovery"]
        assert rec["workout_type"] is not None
        assert rec["duration"] > 0
        assert len(rec["rationale"]) > 50, "Rationale should be detailed"

        # Verify component breakdown
        components = data["components"]
        assert components["hrv_score"] is not None
        assert components["hr_score"] is not None
        assert components["sleep_score"] is not None
        assert components["acwr_score"] is not None

        # Verify explanation exists
        assert len(data["explanation"]) > 20, "Explanation should be provided"
