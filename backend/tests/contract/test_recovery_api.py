"""
Contract tests for Recovery API endpoints.

Tests API contract compliance:
- Request/response schemas
- Status codes
- Error handling
- Authentication requirements
- Data validation

Endpoints tested:
- GET /api/recovery/{date} - Get recovery score for specific date
- GET /api/recovery/today - Get today's recovery score
- POST /api/recovery/{date}/recalculate - Force recalculation
"""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.main import app
from src.models.user import User
from src.models.recovery_score import RecoveryScore


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = Mock(spec=User)
    user.id = "550e8400-e29b-41d4-a716-446655440000"
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def auth_headers(mock_user):
    """Authentication headers."""
    return {"Authorization": "Bearer mock_token_12345"}


class TestGetRecoveryByDate:
    """Test GET /api/recovery/{date} endpoint."""

    def test_returns_recovery_score_for_valid_date(
        self, client, auth_headers, mock_user
    ):
        """Test that endpoint returns recovery score for valid date."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                # Mock recovery score
                mock_score = Mock(spec=RecoveryScore)
                mock_score.overall_score = 85
                mock_score.status = "green"
                mock_score.hrv_component = 90.0
                mock_score.hr_component = 85.0
                mock_score.sleep_component = 80.0
                mock_score.acwr_component = 85.0
                mock_score.explanation = "Excellent recovery"
                mock_score.cached_at = datetime.utcnow()
                mock_get.return_value = mock_score

                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "date" in data
                assert "overall_score" in data
                assert "status" in data
                assert "components" in data
                assert "explanation" in data

                # Verify data types
                assert isinstance(data["overall_score"], int)
                assert data["status"] in ["green", "yellow", "red"]
                assert isinstance(data["components"], dict)

    def test_returns_404_when_no_recovery_score_exists(
        self, client, auth_headers, mock_user
    ):
        """Test that endpoint returns 404 when no score exists."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score", return_value=None):
                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 404
                data = response.json()
                assert "detail" in data

    def test_requires_authentication(self, client):
        """Test that endpoint requires authentication."""
        target_date = date.today()

        response = client.get(f"/api/recovery/{target_date}")

        assert response.status_code == 401

    def test_validates_date_format(self, client, auth_headers, mock_user):
        """Test that endpoint validates date format."""
        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            response = client.get("/api/recovery/invalid-date", headers=auth_headers)

            assert response.status_code == 422  # Validation error

    def test_rejects_future_dates(self, client, auth_headers, mock_user):
        """Test that endpoint rejects future dates."""
        future_date = date.today() + timedelta(days=7)

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            response = client.get(f"/api/recovery/{future_date}", headers=auth_headers)

            assert response.status_code == 400
            data = response.json()
            assert "future" in data["detail"].lower()

    def test_includes_component_breakdown(self, client, auth_headers, mock_user):
        """Test that response includes component score breakdown."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                mock_score = Mock(spec=RecoveryScore)
                mock_score.overall_score = 75
                mock_score.status = "green"
                mock_score.hrv_component = 80.0
                mock_score.hr_component = 70.0
                mock_score.sleep_component = 75.0
                mock_score.acwr_component = 70.0
                mock_score.explanation = "Good recovery"
                mock_score.cached_at = datetime.utcnow()
                mock_get.return_value = mock_score

                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()

                components = data["components"]
                assert "hrv_score" in components
                assert "hr_score" in components
                assert "sleep_score" in components
                assert "acwr_score" in components

    def test_includes_cache_metadata(self, client, auth_headers, mock_user):
        """Test that response includes cache information."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                mock_score = Mock(spec=RecoveryScore)
                mock_score.overall_score = 85
                mock_score.status = "green"
                mock_score.hrv_component = 90.0
                mock_score.hr_component = 85.0
                mock_score.sleep_component = 80.0
                mock_score.acwr_component = 85.0
                mock_score.explanation = "Excellent"
                mock_score.cached_at = datetime.utcnow()
                mock_score.cache_expires_at = datetime.utcnow() + timedelta(hours=24)
                mock_score.is_expired = False
                mock_get.return_value = mock_score

                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()

                assert "cached_at" in data
                assert "is_expired" in data


class TestGetRecoveryToday:
    """Test GET /api/recovery/today endpoint."""

    def test_returns_todays_recovery_score(self, client, auth_headers, mock_user):
        """Test that endpoint returns today's recovery score."""
        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                mock_score = Mock(spec=RecoveryScore)
                mock_score.overall_score = 75
                mock_score.status = "green"
                mock_score.hrv_component = 80.0
                mock_score.hr_component = 75.0
                mock_score.sleep_component = 70.0
                mock_score.acwr_component = 75.0
                mock_score.explanation = "Good recovery"
                mock_score.cached_at = datetime.utcnow()
                mock_get.return_value = mock_score

                response = client.get("/api/recovery/today", headers=auth_headers)

                assert response.status_code == 200
                data = response.json()

                assert data["date"] == str(date.today())
                assert "overall_score" in data

    def test_triggers_calculation_if_not_cached(self, client, auth_headers, mock_user):
        """Test that endpoint triggers calculation if score not cached."""
        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score", return_value=None):
                with patch(
                    "src.api.routes.recovery.trigger_recovery_calculation"
                ) as mock_calc:
                    mock_calc.return_value = {"score": 80, "status": "triggered"}

                    response = client.get("/api/recovery/today", headers=auth_headers)

                    # Should return 202 Accepted while calculating
                    assert response.status_code == 202
                    data = response.json()
                    assert "message" in data

    def test_requires_authentication(self, client):
        """Test that endpoint requires authentication."""
        response = client.get("/api/recovery/today")

        assert response.status_code == 401

    def test_includes_workout_recommendation(self, client, auth_headers, mock_user):
        """Test that response includes workout recommendation."""
        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                with patch(
                    "src.api.routes.recovery.get_workout_recommendation"
                ) as mock_rec:
                    mock_score = Mock(spec=RecoveryScore)
                    mock_score.overall_score = 85
                    mock_score.status = "green"
                    mock_score.hrv_component = 90.0
                    mock_score.hr_component = 85.0
                    mock_score.sleep_component = 80.0
                    mock_score.acwr_component = 85.0
                    mock_score.explanation = "Excellent"
                    mock_score.cached_at = datetime.utcnow()
                    mock_get.return_value = mock_score

                    mock_rec.return_value = {
                        "intensity": "hard",
                        "workout_type": "intervals",
                        "rationale": "You're well-recovered",
                    }

                    response = client.get("/api/recovery/today", headers=auth_headers)

                    assert response.status_code == 200
                    data = response.json()

                    assert "recommendation" in data
                    rec = data["recommendation"]
                    assert "intensity" in rec
                    assert "workout_type" in rec
                    assert "rationale" in rec


class TestPostRecalculateRecovery:
    """Test POST /api/recovery/{date}/recalculate endpoint."""

    def test_triggers_recalculation(self, client, auth_headers, mock_user):
        """Test that endpoint triggers recalculation."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch(
                "src.api.routes.recovery.trigger_recovery_calculation"
            ) as mock_calc:
                mock_calc.return_value = {"task_id": "abc123", "status": "triggered"}

                response = client.post(
                    f"/api/recovery/{target_date}/recalculate", headers=auth_headers
                )

                assert response.status_code == 202  # Accepted
                data = response.json()

                assert "task_id" in data
                assert "message" in data
                mock_calc.assert_called_once()

    def test_requires_authentication(self, client):
        """Test that endpoint requires authentication."""
        target_date = date.today()

        response = client.post(f"/api/recovery/{target_date}/recalculate")

        assert response.status_code == 401

    def test_validates_date_format(self, client, auth_headers, mock_user):
        """Test that endpoint validates date format."""
        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            response = client.post(
                "/api/recovery/invalid-date/recalculate", headers=auth_headers
            )

            assert response.status_code == 422

    def test_rejects_future_dates(self, client, auth_headers, mock_user):
        """Test that endpoint rejects future dates."""
        future_date = date.today() + timedelta(days=7)

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            response = client.post(
                f"/api/recovery/{future_date}/recalculate", headers=auth_headers
            )

            assert response.status_code == 400

    def test_returns_calculation_status(self, client, auth_headers, mock_user):
        """Test that endpoint returns calculation status."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch(
                "src.api.routes.recovery.trigger_recovery_calculation"
            ) as mock_calc:
                mock_calc.return_value = {
                    "task_id": "task_12345",
                    "status": "pending",
                    "estimated_completion": 5,  # seconds
                }

                response = client.post(
                    f"/api/recovery/{target_date}/recalculate", headers=auth_headers
                )

                assert response.status_code == 202
                data = response.json()

                assert data["task_id"] == "task_12345"
                assert "status" in data

    def test_handles_missing_health_data_gracefully(
        self, client, auth_headers, mock_user
    ):
        """Test that endpoint handles missing health data."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch(
                "src.api.routes.recovery.trigger_recovery_calculation"
            ) as mock_calc:
                mock_calc.side_effect = ValueError("No health metrics for date")

                response = client.post(
                    f"/api/recovery/{target_date}/recalculate", headers=auth_headers
                )

                assert response.status_code == 400
                data = response.json()
                assert "health" in data["detail"].lower()

    def test_rate_limits_recalculation_requests(self, client, auth_headers, mock_user):
        """Test that endpoint rate limits frequent recalculation."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch(
                "src.api.routes.recovery.check_recalculation_rate_limit"
            ) as mock_limit:
                mock_limit.return_value = False  # Rate limit exceeded

                response = client.post(
                    f"/api/recovery/{target_date}/recalculate", headers=auth_headers
                )

                assert response.status_code == 429  # Too Many Requests


class TestRecoveryAPIErrorHandling:
    """Test error handling across recovery API."""

    def test_handles_database_errors_gracefully(self, client, auth_headers, mock_user):
        """Test that database errors are handled gracefully."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                mock_get.side_effect = Exception("Database connection error")

                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 500

    def test_handles_invalid_user_gracefully(self, client, auth_headers):
        """Test that invalid users are handled."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=None):
            response = client.get(f"/api/recovery/{target_date}", headers=auth_headers)

            assert response.status_code == 401

    def test_returns_appropriate_error_messages(self, client, auth_headers, mock_user):
        """Test that error messages are descriptive."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score", return_value=None):
                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 404
                data = response.json()
                assert len(data["detail"]) > 10  # Descriptive message


class TestRecoveryAPIDataValidation:
    """Test data validation in recovery API."""

    def test_validates_response_schema(self, client, auth_headers, mock_user):
        """Test that responses conform to schema."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                mock_score = Mock(spec=RecoveryScore)
                mock_score.overall_score = 85
                mock_score.status = "green"
                mock_score.hrv_component = 90.0
                mock_score.hr_component = 85.0
                mock_score.sleep_component = 80.0
                mock_score.acwr_component = 85.0
                mock_score.explanation = "Excellent"
                mock_score.cached_at = datetime.utcnow()
                mock_get.return_value = mock_score

                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()

                # Validate all required fields present
                required_fields = [
                    "date",
                    "overall_score",
                    "status",
                    "components",
                    "explanation",
                ]
                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"

    def test_validates_score_bounds(self, client, auth_headers, mock_user):
        """Test that scores are within valid bounds."""
        target_date = date.today()

        with patch("src.api.routes.recovery.get_current_user", return_value=mock_user):
            with patch("src.api.routes.recovery.get_recovery_score") as mock_get:
                mock_score = Mock(spec=RecoveryScore)
                mock_score.overall_score = 75
                mock_score.status = "green"
                mock_score.hrv_component = 80.0
                mock_score.hr_component = 75.0
                mock_score.sleep_component = 70.0
                mock_score.acwr_component = 75.0
                mock_score.explanation = "Good"
                mock_score.cached_at = datetime.utcnow()
                mock_get.return_value = mock_score

                response = client.get(
                    f"/api/recovery/{target_date}", headers=auth_headers
                )

                assert response.status_code == 200
                data = response.json()

                # Validate score bounds
                assert 0 <= data["overall_score"] <= 100

                components = data["components"]
                for component_name, score in components.items():
                    if score is not None:
                        assert 0 <= score <= 100, f"{component_name} out of bounds"
