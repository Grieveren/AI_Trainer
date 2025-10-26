"""
Contract tests for Garmin API integration.

These tests verify that our code correctly handles the Garmin Connect API contracts,
including OAuth2 PKCE authentication, health metrics retrieval, and workout data fetching.

Tests use mocked HTTP responses to validate request/response handling without
calling the actual Garmin API.
"""

import pytest
from datetime import date, datetime

from src.services.garmin.client import GarminClient
from src.services.garmin.oauth_service import GarminOAuthService
from src.services.garmin.health_service import GarminHealthService
from src.services.garmin.workout_service import GarminWorkoutService


class TestGarminOAuthContract:
    """Test OAuth2 PKCE flow contract with Garmin API."""

    @pytest.mark.asyncio
    async def test_authorization_url_generation(self):
        """Test that authorization URL is generated with correct parameters."""
        oauth_service = GarminOAuthService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/api/v1/garmin/callback",
        )

        auth_url, state, code_verifier = oauth_service.get_authorization_url()

        # Verify URL structure
        assert auth_url.startswith("https://connect.garmin.com/oauthConfirm")
        assert "oauth_consumer_key=test_client_id" in auth_url
        assert "oauth_callback=" in auth_url

        # Verify PKCE parameters
        assert state is not None
        assert len(state) >= 32  # State should be at least 32 characters
        assert code_verifier is not None
        assert len(code_verifier) >= 43  # PKCE verifier should be 43-128 chars

    @pytest.mark.asyncio
    async def test_token_exchange_success(self, httpx_mock):
        """Test successful OAuth token exchange."""
        oauth_service = GarminOAuthService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/api/v1/garmin/callback",
        )

        # Mock successful token response
        httpx_mock.add_response(
            method="POST",
            url="https://connectapi.garmin.com/oauth-service/oauth/access_token",
            json={
                "access_token": "test_access_token_12345",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "test_refresh_token_67890",
                "user_id": "garmin_user_123",
            },
            status_code=200,
        )

        # Exchange authorization code for tokens
        token_response = await oauth_service.exchange_code_for_token(
            auth_code="test_auth_code", code_verifier="test_code_verifier"
        )

        # Verify token response
        assert token_response["access_token"] == "test_access_token_12345"
        assert token_response["refresh_token"] == "test_refresh_token_67890"
        assert token_response["user_id"] == "garmin_user_123"
        assert token_response["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_token_refresh_success(self, httpx_mock):
        """Test successful token refresh."""
        oauth_service = GarminOAuthService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/api/v1/garmin/callback",
        )

        # Mock successful refresh response
        httpx_mock.add_response(
            method="POST",
            url="https://connectapi.garmin.com/oauth-service/oauth/access_token",
            json={
                "access_token": "new_access_token_99999",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            status_code=200,
        )

        # Refresh token
        new_tokens = await oauth_service.refresh_access_token(
            refresh_token="test_refresh_token_67890"
        )

        # Verify new access token
        assert new_tokens["access_token"] == "new_access_token_99999"
        assert new_tokens["expires_in"] == 3600


class TestGarminHealthMetricsContract:
    """Test Garmin health metrics API contract."""

    @pytest.mark.asyncio
    async def test_fetch_daily_health_metrics_success(self, httpx_mock):
        """Test successful retrieval of daily health metrics."""
        health_service = GarminHealthService(access_token="test_token")

        test_date = date(2025, 10, 24)

        # Mock Garmin API response for daily metrics
        httpx_mock.add_response(
            method="GET",
            url=f"https://apis.garmin.com/wellness-api/rest/dailies?uploadStartTimeInSeconds={int(datetime.combine(test_date, datetime.min.time()).timestamp())}&uploadEndTimeInSeconds={int(datetime.combine(test_date, datetime.max.time()).timestamp())}",
            json=[
                {
                    "calendarDate": "2025-10-24",
                    "restingHeartRateInBeatsPerMinute": 55,
                    "heartRateVariabilityInMilliseconds": 62,
                    "sleepDurationInSeconds": 28800,  # 8 hours
                    "sleepScores": {"overall": 85},
                    "averageStressLevel": 30,
                    "maxStressLevel": 65,
                }
            ],
            status_code=200,
        )

        # Fetch health metrics
        metrics = await health_service.get_daily_metrics(test_date)

        # Verify parsed metrics
        assert metrics["date"] == test_date
        assert metrics["hrv_ms"] == 62
        assert metrics["resting_hr"] == 55
        assert metrics["sleep_duration_minutes"] == 480  # 28800 seconds / 60
        assert metrics["sleep_score"] == 85
        assert metrics["stress_level"] == 30

    @pytest.mark.asyncio
    async def test_fetch_health_metrics_with_missing_data(self, httpx_mock):
        """Test handling of incomplete health metrics data."""
        health_service = GarminHealthService(access_token="test_token")

        test_date = date(2025, 10, 24)

        # Mock response with missing HRV data
        httpx_mock.add_response(
            method="GET",
            url=f"https://apis.garmin.com/wellness-api/rest/dailies?uploadStartTimeInSeconds={int(datetime.combine(test_date, datetime.min.time()).timestamp())}&uploadEndTimeInSeconds={int(datetime.combine(test_date, datetime.max.time()).timestamp())}",
            json=[
                {
                    "calendarDate": "2025-10-24",
                    "restingHeartRateInBeatsPerMinute": 55,
                    # HRV missing (not all devices support HRV)
                    "sleepDurationInSeconds": 25200,  # 7 hours
                    "averageStressLevel": 40,
                }
            ],
            status_code=200,
        )

        # Fetch metrics
        metrics = await health_service.get_daily_metrics(test_date)

        # Verify nullable fields are None
        assert metrics["hrv_ms"] is None
        assert metrics["resting_hr"] == 55
        assert metrics["sleep_duration_minutes"] == 420
        assert metrics["sleep_score"] is None
        assert metrics["stress_level"] == 40

    @pytest.mark.asyncio
    async def test_unauthorized_access_token(self, httpx_mock):
        """Test handling of expired or invalid access token."""
        health_service = GarminHealthService(access_token="expired_token")

        test_date = date(2025, 10, 24)

        # Mock 401 Unauthorized response
        httpx_mock.add_response(
            method="GET",
            url=f"https://apis.garmin.com/wellness-api/rest/dailies?uploadStartTimeInSeconds={int(datetime.combine(test_date, datetime.min.time()).timestamp())}&uploadEndTimeInSeconds={int(datetime.combine(test_date, datetime.max.time()).timestamp())}",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        # Expect exception on unauthorized access
        with pytest.raises(Exception) as exc_info:
            await health_service.get_daily_metrics(test_date)

        assert "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value)


class TestGarminWorkoutContract:
    """Test Garmin workout/activity API contract."""

    @pytest.mark.asyncio
    async def test_fetch_activities_list_success(self, httpx_mock):
        """Test successful retrieval of activities list."""
        workout_service = GarminWorkoutService(access_token="test_token")

        start_date = date(2025, 10, 20)
        end_date = date(2025, 10, 24)

        # Mock activities list response
        httpx_mock.add_response(
            method="GET",
            url=f"https://apis.garmin.com/fitness-api/rest/activityList?uploadStartTimeInSeconds={int(datetime.combine(start_date, datetime.min.time()).timestamp())}&uploadEndTimeInSeconds={int(datetime.combine(end_date, datetime.max.time()).timestamp())}",
            json=[
                {
                    "activityId": 12345678,
                    "activityName": "Morning Run",
                    "activityType": "running",
                    "startTimeInSeconds": 1729756800,
                    "durationInSeconds": 2400,  # 40 minutes
                    "distanceInMeters": 8000,
                },
                {
                    "activityId": 12345679,
                    "activityName": "Cycling",
                    "activityType": "cycling",
                    "startTimeInSeconds": 1729843200,
                    "durationInSeconds": 3600,  # 60 minutes
                    "distanceInMeters": 30000,
                },
            ],
            status_code=200,
        )

        # Fetch activities
        activities = await workout_service.get_activities(start_date, end_date)

        # Verify parsed activities
        assert len(activities) == 2
        assert activities[0]["garmin_activity_id"] == "12345678"
        assert activities[0]["workout_type"] == "running"
        assert activities[0]["duration_minutes"] == 40
        assert activities[1]["workout_type"] == "cycling"

    @pytest.mark.asyncio
    async def test_fetch_activity_details_success(self, httpx_mock):
        """Test successful retrieval of detailed activity data."""
        workout_service = GarminWorkoutService(access_token="test_token")

        activity_id = "12345678"

        # Mock detailed activity response
        httpx_mock.add_response(
            method="GET",
            url=f"https://apis.garmin.com/fitness-api/rest/activity/{activity_id}",
            json={
                "activityId": 12345678,
                "activityName": "Morning Run",
                "activityType": "running",
                "startTimeInSeconds": 1729756800,
                "durationInSeconds": 2400,
                "distanceInMeters": 8000,
                "averageHeartRateInBeatsPerMinute": 155,
                "maxHeartRateInBeatsPerMinute": 178,
                "trainingEffect": 3.2,
                "trainingLoad": 145,
                "heartRateZones": [
                    {"zoneName": "zone1", "timeInZoneInSeconds": 300},
                    {"zoneName": "zone2", "timeInZoneInSeconds": 900},
                    {"zoneName": "zone3", "timeInZoneInSeconds": 1200},
                ],
            },
            status_code=200,
        )

        # Fetch activity details
        details = await workout_service.get_activity_details(activity_id)

        # Verify detailed data
        assert details["garmin_activity_id"] == "12345678"
        assert details["training_load"] == 145
        assert details["heart_rate_zones"] is not None
        assert len(details["heart_rate_zones"]) == 3

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, httpx_mock):
        """Test proper handling of API rate limits."""
        workout_service = GarminWorkoutService(access_token="test_token")

        start_date = date(2025, 10, 24)
        end_date = date(2025, 10, 24)

        # Mock 429 Rate Limit response
        httpx_mock.add_response(
            method="GET",
            url=f"https://apis.garmin.com/fitness-api/rest/activityList?uploadStartTimeInSeconds={int(datetime.combine(start_date, datetime.min.time()).timestamp())}&uploadEndTimeInSeconds={int(datetime.combine(end_date, datetime.max.time()).timestamp())}",
            status_code=429,
            headers={"Retry-After": "60"},
            json={"error": "Rate limit exceeded"},
        )

        # Expect rate limit exception
        with pytest.raises(Exception) as exc_info:
            await workout_service.get_activities(start_date, end_date)

        assert (
            "429" in str(exc_info.value) or "rate limit" in str(exc_info.value).lower()
        )


class TestGarminClientIntegration:
    """Test high-level Garmin client integration."""

    @pytest.mark.asyncio
    async def test_client_initializes_with_valid_token(self):
        """Test that client can be initialized with access token."""
        client = GarminClient(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_expires_at=datetime.now(),
        )

        assert client.access_token == "test_access_token"
        assert client.refresh_token == "test_refresh_token"

    @pytest.mark.asyncio
    async def test_client_auto_refreshes_expired_token(self, httpx_mock):
        """Test that client automatically refreshes expired tokens."""
        # Mock token refresh endpoint
        httpx_mock.add_response(
            method="POST",
            url="https://connectapi.garmin.com/oauth-service/oauth/access_token",
            json={"access_token": "refreshed_token", "expires_in": 3600},
            status_code=200,
        )

        # Create client with expired token
        client = GarminClient(
            access_token="expired_token",
            refresh_token="valid_refresh_token",
            token_expires_at=datetime(2025, 10, 1),  # Past date
        )

        # Attempt to use client (should trigger refresh)
        new_token = await client.ensure_valid_token()

        assert new_token == "refreshed_token"
