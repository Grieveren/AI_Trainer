"""
Garmin Workout Service.

Fetches workout/activity data from Garmin Connect API including:
- Activity list
- Detailed activity data (HR zones, training load, etc.)

Includes caching with different TTLs:
- Workout lists: 1 hour (may change frequently)
- Workout details: 7 days (historical data doesn't change)
"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional
import httpx
import logging

from src.services.garmin.parsers import WorkoutParser, HeartRateZoneParser
from src.services.garmin.cache import GarminCache

logger = logging.getLogger(__name__)


class GarminWorkoutService:
    """Service for fetching workout data from Garmin API."""

    BASE_URL = "https://apis.garmin.com/fitness-api/rest"

    def __init__(self, access_token: str, user_id: Optional[str] = None):
        """
        Initialize workout service with access token.

        Args:
            access_token: Valid OAuth access token
            user_id: Optional user ID for caching
        """
        self.access_token = access_token
        self.user_id = user_id
        self.workout_parser = WorkoutParser()
        self.hr_zone_parser = HeartRateZoneParser()
        self.cache = GarminCache()

    async def get_activities(
        self, start_date: date, end_date: date, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch list of activities within date range with caching.

        Checks cache first (1-hour TTL), fetches from API if cache miss.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of activities to return

        Returns:
            List of parsed workout data

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Try cache first if user_id available
        if self.user_id:
            cached_data = await self.cache.get_workout_list(
                self.user_id, start_date, end_date
            )
            if cached_data is not None:
                return cached_data

        # Cache miss - fetch from API
        activities = await self._fetch_activities(start_date, end_date, limit)

        # Cache the result if user_id available
        if self.user_id and activities:
            await self.cache.set_workout_list(
                self.user_id, start_date, end_date, activities
            )

        return activities

    async def _fetch_activities(
        self, start_date: date, end_date: date, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Internal method to fetch activities from Garmin API.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of activities to return

        Returns:
            List of parsed workout data

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Convert dates to timestamps
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        start_timestamp = int(start_datetime.timestamp())
        end_timestamp = int(end_datetime.timestamp())

        # Build API URL
        url = f"{self.BASE_URL}/activityList"
        params = {
            "uploadStartTimeInSeconds": start_timestamp,
            "uploadEndTimeInSeconds": end_timestamp,
            "limit": limit,
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

            # Handle rate limiting
            if response.status_code == 429:
                raise Exception("Rate limit exceeded - too many requests")

            # Handle unauthorized
            if response.status_code == 401:
                raise Exception("Unauthorized - access token expired or invalid")

            response.raise_for_status()

            # Parse activities
            data = response.json()
            return [self.workout_parser.parse(activity) for activity in data]

    async def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """
        Fetch detailed data for a specific activity with caching.

        Checks cache first (7-day TTL), fetches from API if cache miss.
        Historical workout data doesn't change, so longer cache is appropriate.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Dict with detailed workout data including HR zones

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Try cache first if user_id available
        if self.user_id:
            cached_data = await self.cache.get_workout_details(
                self.user_id, activity_id
            )
            if cached_data is not None:
                return cached_data

        # Cache miss - fetch from API
        details = await self._fetch_activity_details(activity_id)

        # Cache the result if user_id available
        if self.user_id and details:
            await self.cache.set_workout_details(self.user_id, activity_id, details)

        return details

    async def _fetch_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """
        Internal method to fetch activity details from Garmin API.

        Args:
            activity_id: Garmin activity ID

        Returns:
            Dict with detailed workout data including HR zones

        Raises:
            httpx.HTTPError: If API request fails
        """
        url = f"{self.BASE_URL}/activity/{activity_id}"

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 401:
                raise Exception("Unauthorized - access token expired or invalid")

            if response.status_code == 404:
                raise Exception(f"Activity {activity_id} not found")

            response.raise_for_status()

            # Parse activity
            data = response.json()
            workout = self.workout_parser.parse(data)

            # Parse HR zones if available
            if "heartRateZones" in data:
                workout["heart_rate_zones"] = self.hr_zone_parser.parse(
                    data["heartRateZones"]
                )

            return workout
