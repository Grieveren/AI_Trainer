"""
Parsers for Garmin API responses.

Transforms Garmin Connect API JSON responses into our internal data structures,
handles missing fields, validates data ranges, and normalizes units.
"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional


class HealthMetricsParser:
    """Parses Garmin health/wellness metrics."""

    # Validation ranges
    HRV_MIN = 10
    HRV_MAX = 200
    HR_MIN = 30
    HR_MAX = 120

    def parse(self, garmin_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Garmin daily health metrics response.

        Args:
            garmin_response: Raw JSON response from Garmin API

        Returns:
            Dict with normalized health metrics

        Raises:
            KeyError: If required fields are missing
            ValueError: If data validation fails
        """
        # Parse date (required field)
        date_str = garmin_response["calendarDate"]
        parsed_date = self._parse_date(date_str)

        # Extract and validate HRV (nullable)
        hrv_ms = garmin_response.get("heartRateVariabilityInMilliseconds")
        if hrv_ms is not None:
            hrv_ms = self._validate_hrv(hrv_ms)

        # Extract and validate resting HR (nullable)
        resting_hr = garmin_response.get("restingHeartRateInBeatsPerMinute")
        if resting_hr is not None:
            resting_hr = self._validate_heart_rate(resting_hr)

        # Convert sleep duration from seconds to minutes
        sleep_seconds = garmin_response.get("sleepDurationInSeconds")
        sleep_minutes = int(sleep_seconds / 60) if sleep_seconds else None

        # Extract sleep score
        sleep_score = None
        if "sleepScores" in garmin_response:
            sleep_score = garmin_response["sleepScores"].get("overall")

        # Extract stress level
        stress_level = garmin_response.get("averageStressLevel")

        return {
            "date": parsed_date,
            "hrv_ms": hrv_ms,
            "resting_hr": resting_hr,
            "sleep_duration_minutes": sleep_minutes,
            "sleep_score": sleep_score,
            "stress_level": stress_level,
        }

    def _parse_date(self, date_str: str) -> date:
        """
        Parse date string to date object.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            date object

        Raises:
            ValueError: If date format is invalid
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(f"Invalid date format: {date_str}") from e

    def _validate_hrv(self, hrv: int) -> int:
        """
        Validate HRV value is within realistic range.

        Args:
            hrv: HRV value in milliseconds

        Returns:
            Validated HRV value

        Raises:
            ValueError: If HRV is outside valid range
        """
        if not isinstance(hrv, int):
            raise TypeError(f"HRV must be an integer, got {type(hrv)}")

        if not (self.HRV_MIN <= hrv <= self.HRV_MAX):
            raise ValueError(
                f"HRV {hrv}ms outside valid range ({self.HRV_MIN}-{self.HRV_MAX}ms)"
            )

        return hrv

    def _validate_heart_rate(self, hr: int) -> int:
        """
        Validate heart rate value is within realistic range.

        Args:
            hr: Heart rate in beats per minute

        Returns:
            Validated heart rate

        Raises:
            ValueError: If HR is outside valid range
        """
        if not isinstance(hr, int):
            raise TypeError(f"Heart rate must be an integer, got {type(hr)}")

        if not (self.HR_MIN <= hr <= self.HR_MAX):
            raise ValueError(
                f"Heart rate {hr}bpm outside valid range ({self.HR_MIN}-{self.HR_MAX}bpm)"
            )

        return hr


class WorkoutParser:
    """Parses Garmin workout/activity data."""

    # Activity type mapping: Garmin type -> our workout type
    ACTIVITY_TYPE_MAP = {
        "running": "run",
        "cycling": "bike",
        "swimming": "swim",
        "strength_training": "strength",
        "yoga": "yoga",
        "walking": "other",
        "hiking": "other",
        "fitness_equipment": "other",
        "elliptical": "other",
        "stair_climbing": "other",
    }

    def parse(self, garmin_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Garmin activity/workout response.

        Args:
            garmin_response: Raw JSON response from Garmin API

        Returns:
            Dict with normalized workout data

        Raises:
            KeyError: If required fields are missing
        """
        # Required fields
        activity_id = str(garmin_response["activityId"])
        activity_type = garmin_response["activityType"]
        start_time = garmin_response["startTimeInSeconds"]
        duration_seconds = garmin_response["durationInSeconds"]

        # Map Garmin activity type to our workout type
        workout_type = self._map_activity_type(activity_type)

        # Convert duration to minutes
        duration_minutes = int(duration_seconds / 60)

        # Convert timestamp to datetime
        started_at = datetime.fromtimestamp(start_time)

        # Optional fields
        training_load = garmin_response.get("trainingLoad")
        perceived_exertion = garmin_response.get("perceivedExertion")
        avg_hr = garmin_response.get("averageHeartRateInBeatsPerMinute")
        max_hr = garmin_response.get("maxHeartRateInBeatsPerMinute")

        # Check if manually entered
        manual_entry = garmin_response.get("manual", False)

        return {
            "garmin_activity_id": activity_id,
            "workout_type": workout_type,
            "started_at": started_at,
            "duration_minutes": duration_minutes,
            "training_load": training_load,
            "perceived_exertion": perceived_exertion,
            "manual_entry": manual_entry,
            "average_hr": avg_hr,
            "max_hr": max_hr,
        }

    def _map_activity_type(self, garmin_type: str) -> str:
        """
        Map Garmin activity type to our workout type.

        Args:
            garmin_type: Garmin activity type

        Returns:
            Normalized workout type
        """
        normalized_type = garmin_type.lower().replace(" ", "_")
        return self.ACTIVITY_TYPE_MAP.get(normalized_type, "other")


class HeartRateZoneParser:
    """Parses heart rate zone distribution data."""

    def parse(self, garmin_zones: List[Dict[str, Any]]) -> Optional[Dict[str, int]]:
        """
        Parse heart rate zones into time distribution.

        Args:
            garmin_zones: List of zone objects with zoneName and timeInZoneInSeconds

        Returns:
            Dict mapping zone names to time in seconds, or None if no zones
        """
        if not garmin_zones:
            return None

        zones = {}
        for zone_data in garmin_zones:
            zone_name = zone_data.get("zoneName")
            time_in_zone = zone_data.get("timeInZoneInSeconds", 0)

            if zone_name:
                zones[zone_name] = time_in_zone

        return zones if zones else None
