"""Test utilities for mocking external APIs."""

from typing import Any, Dict, List, Optional


class MockGarminClient:
    """Mock Garmin API client for testing."""

    def __init__(self, fail: bool = False, data: Optional[Dict] = None):
        """Initialize mock Garmin client.

        Args:
            fail: If True, mock will raise exceptions
            data: Custom data to return instead of defaults
        """
        self.fail = fail
        self.custom_data = data or {}
        self.called_methods: List[str] = []

    async def get_health_metrics(self, date: str) -> Dict[str, Any]:
        """Mock get_health_metrics method."""
        self.called_methods.append("get_health_metrics")

        if self.fail:
            raise ConnectionError("Failed to connect to Garmin API")

        return self.custom_data.get(
            "health_metrics",
            {
                "date": date,
                "hrv_rmssd": 45.0,
                "resting_heart_rate": 58,
                "sleep_duration_hours": 7.5,
                "sleep_quality_score": 85,
                "stress_level": 30,
            },
        )

    async def get_workouts(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Mock get_workouts method."""
        self.called_methods.append("get_workouts")

        if self.fail:
            raise ConnectionError("Failed to connect to Garmin API")

        return self.custom_data.get(
            "workouts",
            [
                {
                    "date": start_date,
                    "workout_type": "run",
                    "duration_minutes": 45,
                    "distance_km": 8.5,
                    "avg_heart_rate": 155,
                    "max_heart_rate": 175,
                    "training_load": 125,
                }
            ],
        )

    async def authorize(self, code: str) -> Dict[str, str]:
        """Mock OAuth authorization."""
        self.called_methods.append("authorize")

        if self.fail:
            raise ValueError("Invalid authorization code")

        return self.custom_data.get(
            "auth_tokens",
            {
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token",
                "expires_at": "2025-11-24T00:00:00Z",
            },
        )


class MockClaudeClient:
    """Mock Claude AI client for testing."""

    def __init__(self, fail: bool = False, response: Optional[str] = None):
        """Initialize mock Claude client.

        Args:
            fail: If True, mock will raise exceptions
            response: Custom response text instead of default
        """
        self.fail = fail
        self.custom_response = response
        self.called_methods: List[str] = []
        self.call_count = 0

    async def generate_insight(self, metrics: Dict[str, Any]) -> str:
        """Mock insight generation."""
        self.called_methods.append("generate_insight")
        self.call_count += 1

        if self.fail:
            raise RuntimeError("Claude API request failed")

        return (
            self.custom_response
            or "Your recovery is excellent today. Consider a high-intensity workout."
        )

    async def generate_recommendation(
        self, recovery_score: float, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock workout recommendation generation."""
        self.called_methods.append("generate_recommendation")
        self.call_count += 1

        if self.fail:
            raise RuntimeError("Claude API request failed")

        if self.custom_response:
            return {"recommendation": self.custom_response}

        # Default recommendation based on recovery score
        if recovery_score >= 70:
            return {
                "intensity": "high",
                "workout_type": "interval_training",
                "duration_minutes": 60,
                "rationale": "High recovery score indicates readiness for intense training.",
            }
        elif recovery_score >= 40:
            return {
                "intensity": "moderate",
                "workout_type": "tempo_run",
                "duration_minutes": 45,
                "rationale": "Moderate recovery - steady-state training recommended.",
            }
        else:
            return {
                "intensity": "low",
                "workout_type": "active_recovery",
                "duration_minutes": 30,
                "rationale": "Low recovery - focus on recovery today.",
            }


class MockRedisClient:
    """Mock Redis client for testing."""

    def __init__(self):
        """Initialize mock Redis client."""
        self.data: Dict[str, str] = {}
        self.ttl_data: Dict[str, int] = {}

    async def get(self, key: str) -> Optional[str]:
        """Mock get method."""
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        """Mock set method."""
        self.data[key] = value
        if ex:
            self.ttl_data[key] = ex

    async def delete(self, key: str) -> None:
        """Mock delete method."""
        self.data.pop(key, None)
        self.ttl_data.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Mock exists method."""
        return key in self.data

    async def expire(self, key: str, seconds: int) -> None:
        """Mock expire method."""
        if key in self.data:
            self.ttl_data[key] = seconds

    async def ttl(self, key: str) -> int:
        """Mock ttl method."""
        return self.ttl_data.get(key, -1)

    async def flushdb(self) -> None:
        """Mock flushdb method."""
        self.data.clear()
        self.ttl_data.clear()


def create_mock_garmin_client(**kwargs) -> MockGarminClient:
    """Factory function to create mock Garmin client."""
    return MockGarminClient(**kwargs)


def create_mock_claude_client(**kwargs) -> MockClaudeClient:
    """Factory function to create mock Claude client."""
    return MockClaudeClient(**kwargs)


def create_mock_redis_client() -> MockRedisClient:
    """Factory function to create mock Redis client."""
    return MockRedisClient()
