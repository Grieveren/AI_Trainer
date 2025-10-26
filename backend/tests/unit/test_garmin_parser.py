"""
Unit tests for Garmin API response parsing.

Tests focus on transforming Garmin API JSON responses into our internal
data structures, handling missing fields, and data validation.
"""

import pytest
from datetime import date, datetime

from src.services.garmin.parsers import (
    HealthMetricsParser,
    WorkoutParser,
    HeartRateZoneParser,
)


class TestHealthMetricsParser:
    """Test parsing of Garmin health/wellness data."""

    def test_parse_complete_health_metrics(self):
        """Test parsing when all health metrics are present."""
        garmin_response = {
            "calendarDate": "2025-10-24",
            "restingHeartRateInBeatsPerMinute": 55,
            "heartRateVariabilityInMilliseconds": 62,
            "sleepDurationInSeconds": 28800,  # 8 hours
            "sleepScores": {"overall": 85, "quality": 80, "restlessness": 90},
            "averageStressLevel": 30,
            "maxStressLevel": 65,
            "bodyBatteryHighestValue": 95,
            "bodyBatteryLowestValue": 15,
        }

        parser = HealthMetricsParser()
        metrics = parser.parse(garmin_response)

        assert metrics["date"] == date(2025, 10, 24)
        assert metrics["hrv_ms"] == 62
        assert metrics["resting_hr"] == 55
        assert metrics["sleep_duration_minutes"] == 480
        assert metrics["sleep_score"] == 85
        assert metrics["stress_level"] == 30

    def test_parse_health_metrics_with_missing_hrv(self):
        """Test parsing when HRV is missing (not all devices support HRV)."""
        garmin_response = {
            "calendarDate": "2025-10-24",
            "restingHeartRateInBeatsPerMinute": 55,
            # HRV missing
            "sleepDurationInSeconds": 25200,  # 7 hours
            "averageStressLevel": 40,
        }

        parser = HealthMetricsParser()
        metrics = parser.parse(garmin_response)

        assert metrics["hrv_ms"] is None
        assert metrics["resting_hr"] == 55
        assert metrics["sleep_duration_minutes"] == 420
        assert metrics["stress_level"] == 40

    def test_parse_health_metrics_with_missing_sleep_score(self):
        """Test parsing when sleep score is missing."""
        garmin_response = {
            "calendarDate": "2025-10-24",
            "restingHeartRateInBeatsPerMinute": 58,
            "heartRateVariabilityInMilliseconds": 55,
            "sleepDurationInSeconds": 21600,  # 6 hours
            # Sleep score missing
            "averageStressLevel": 50,
        }

        parser = HealthMetricsParser()
        metrics = parser.parse(garmin_response)

        assert metrics["sleep_score"] is None
        assert metrics["sleep_duration_minutes"] == 360

    def test_parse_health_metrics_converts_units_correctly(self):
        """Test that units are converted properly (seconds to minutes)."""
        garmin_response = {
            "calendarDate": "2025-10-24",
            "sleepDurationInSeconds": 32400,  # 9 hours = 540 minutes
            "restingHeartRateInBeatsPerMinute": 52,
            "averageStressLevel": 25,
        }

        parser = HealthMetricsParser()
        metrics = parser.parse(garmin_response)

        # Verify seconds -> minutes conversion
        assert metrics["sleep_duration_minutes"] == 540
        assert garmin_response["sleepDurationInSeconds"] == 32400

    def test_parse_date_formats(self):
        """Test parsing of different date formats."""
        test_cases = [
            ("2025-10-24", date(2025, 10, 24)),
            ("2025-01-01", date(2025, 1, 1)),
            ("2025-12-31", date(2025, 12, 31)),
        ]

        parser = HealthMetricsParser()

        for date_str, expected_date in test_cases:
            garmin_response = {
                "calendarDate": date_str,
                "restingHeartRateInBeatsPerMinute": 60,
            }

            metrics = parser.parse(garmin_response)
            assert metrics["date"] == expected_date

    def test_parse_invalid_date_raises_error(self):
        """Test that invalid dates raise appropriate errors."""
        garmin_response = {
            "calendarDate": "invalid-date",
            "restingHeartRateInBeatsPerMinute": 60,
        }

        parser = HealthMetricsParser()

        with pytest.raises(ValueError):
            parser.parse(garmin_response)

    def test_parse_validates_hrv_range(self):
        """Test that HRV values are validated."""
        parser = HealthMetricsParser()

        # Valid HRV range: 20-150ms typical, 10-200ms extreme range
        valid_cases = [20, 62, 150, 200]
        for hrv_value in valid_cases:
            garmin_response = {
                "calendarDate": "2025-10-24",
                "heartRateVariabilityInMilliseconds": hrv_value,
                "restingHeartRateInBeatsPerMinute": 60,
            }
            metrics = parser.parse(garmin_response)
            assert metrics["hrv_ms"] == hrv_value

        # Invalid HRV (outside realistic range)
        invalid_cases = [-10, 0, 500, 1000]
        for hrv_value in invalid_cases:
            garmin_response = {
                "calendarDate": "2025-10-24",
                "heartRateVariabilityInMilliseconds": hrv_value,
                "restingHeartRateInBeatsPerMinute": 60,
            }
            with pytest.raises(ValueError):
                parser.parse(garmin_response)

    def test_parse_validates_heart_rate_range(self):
        """Test that heart rate values are validated."""
        parser = HealthMetricsParser()

        # Valid HR range: 30-120 bpm
        valid_cases = [30, 55, 80, 120]
        for hr_value in valid_cases:
            garmin_response = {
                "calendarDate": "2025-10-24",
                "restingHeartRateInBeatsPerMinute": hr_value,
            }
            metrics = parser.parse(garmin_response)
            assert metrics["resting_hr"] == hr_value

        # Invalid HR
        invalid_cases = [0, 20, 200, -5]
        for hr_value in invalid_cases:
            garmin_response = {
                "calendarDate": "2025-10-24",
                "restingHeartRateInBeatsPerMinute": hr_value,
            }
            with pytest.raises(ValueError):
                parser.parse(garmin_response)


class TestWorkoutParser:
    """Test parsing of Garmin workout/activity data."""

    def test_parse_complete_workout(self):
        """Test parsing of complete workout with all fields."""
        garmin_response = {
            "activityId": 12345678,
            "activityName": "Morning Run",
            "activityType": "running",
            "startTimeInSeconds": 1729756800,
            "durationInSeconds": 2400,  # 40 minutes
            "distanceInMeters": 8000,
            "averageHeartRateInBeatsPerMinute": 155,
            "maxHeartRateInBeatsPerMinute": 178,
            "trainingEffect": 3.2,
            "trainingLoad": 145,
            "averagePaceInMinutesPerKilometer": 5.0,
        }

        parser = WorkoutParser()
        workout = parser.parse(garmin_response)

        assert workout["garmin_activity_id"] == "12345678"
        assert workout["workout_type"] == "run"  # Normalized
        assert workout["duration_minutes"] == 40
        assert workout["training_load"] == 145

    def test_parse_workout_maps_activity_types(self):
        """Test that Garmin activity types are mapped to our workout types."""
        test_cases = [
            ("running", "run"),
            ("cycling", "bike"),
            ("swimming", "swim"),
            ("strength_training", "strength"),
            ("yoga", "yoga"),
            ("walking", "other"),
            ("hiking", "other"),
        ]

        parser = WorkoutParser()

        for garmin_type, expected_type in test_cases:
            garmin_response = {
                "activityId": 12345,
                "activityType": garmin_type,
                "startTimeInSeconds": 1729756800,
                "durationInSeconds": 1800,
            }

            workout = parser.parse(garmin_response)
            assert workout["workout_type"] == expected_type

    def test_parse_workout_converts_timestamps(self):
        """Test that Unix timestamps are converted to datetimes."""
        garmin_response = {
            "activityId": 12345,
            "activityType": "running",
            "startTimeInSeconds": 1729756800,  # 2024-10-24 06:00:00 UTC
            "durationInSeconds": 3600,
        }

        parser = WorkoutParser()
        workout = parser.parse(garmin_response)

        # Verify timestamp conversion
        expected_datetime = datetime.fromtimestamp(1729756800)
        assert workout["started_at"] == expected_datetime

    def test_parse_workout_with_manual_entry_flag(self):
        """Test parsing workout added manually (not from device)."""
        garmin_response = {
            "activityId": 12345,
            "activityType": "running",
            "startTimeInSeconds": 1729756800,
            "durationInSeconds": 1800,
            "manual": True,  # Manually entered activity
        }

        parser = WorkoutParser()
        workout = parser.parse(garmin_response)

        assert workout["manual_entry"] is True

    def test_parse_workout_with_missing_training_load(self):
        """Test parsing workout without training load (older activities)."""
        garmin_response = {
            "activityId": 12345,
            "activityType": "running",
            "startTimeInSeconds": 1729756800,
            "durationInSeconds": 1800
            # training_load missing
        }

        parser = WorkoutParser()
        workout = parser.parse(garmin_response)

        assert workout["training_load"] is None


class TestHeartRateZoneParser:
    """Test parsing of heart rate zone data."""

    def test_parse_heart_rate_zones(self):
        """Test parsing of HR zone time distribution."""
        garmin_zones = [
            {"zoneName": "zone1", "timeInZoneInSeconds": 300},  # 5 min
            {"zoneName": "zone2", "timeInZoneInSeconds": 900},  # 15 min
            {"zoneName": "zone3", "timeInZoneInSeconds": 1200},  # 20 min
            {"zoneName": "zone4", "timeInZoneInSeconds": 0},
            {"zoneName": "zone5", "timeInZoneInSeconds": 0},
        ]

        parser = HeartRateZoneParser()
        zones = parser.parse(garmin_zones)

        # Verify structure
        assert zones["zone1"] == 300
        assert zones["zone2"] == 900
        assert zones["zone3"] == 1200
        assert zones["zone4"] == 0
        assert zones["zone5"] == 0

    def test_parse_empty_heart_rate_zones(self):
        """Test parsing when no HR zones are available."""
        garmin_zones = []

        parser = HeartRateZoneParser()
        zones = parser.parse(garmin_zones)

        # Should return None or empty dict
        assert zones is None or zones == {}

    def test_parse_calculates_total_time_in_zones(self):
        """Test calculation of total time in HR zones."""
        garmin_zones = [
            {"zoneName": "zone1", "timeInZoneInSeconds": 600},
            {"zoneName": "zone2", "timeInZoneInSeconds": 1200},
            {"zoneName": "zone3", "timeInZoneInSeconds": 600},
        ]

        parser = HeartRateZoneParser()
        zones = parser.parse(garmin_zones)

        total_time = sum(zones.values())
        assert total_time == 2400  # 40 minutes total


class TestParserErrorHandling:
    """Test error handling in parsers."""

    def test_parser_handles_missing_required_field(self):
        """Test that parsers raise errors for missing required fields."""
        garmin_response = {
            # Missing calendarDate (required)
            "restingHeartRateInBeatsPerMinute": 60
        }

        parser = HealthMetricsParser()

        with pytest.raises(KeyError):
            parser.parse(garmin_response)

    def test_parser_handles_null_values(self):
        """Test that parsers handle null values gracefully."""
        garmin_response = {
            "calendarDate": "2025-10-24",
            "restingHeartRateInBeatsPerMinute": None,
            "heartRateVariabilityInMilliseconds": None,
        }

        parser = HealthMetricsParser()
        metrics = parser.parse(garmin_response)

        # Null values should be preserved as None
        assert metrics["resting_hr"] is None
        assert metrics["hrv_ms"] is None

    def test_parser_handles_unexpected_fields(self):
        """Test that parsers ignore unexpected fields."""
        garmin_response = {
            "calendarDate": "2025-10-24",
            "restingHeartRateInBeatsPerMinute": 60,
            "unexpectedField": "should be ignored",
            "anotherUnknownField": 12345,
        }

        parser = HealthMetricsParser()
        metrics = parser.parse(garmin_response)

        # Should parse successfully, ignoring unknown fields
        assert metrics["resting_hr"] == 60
        assert "unexpectedField" not in metrics

    def test_parser_validates_data_types(self):
        """Test that parsers validate data types."""
        garmin_response = {
            "calendarDate": "2025-10-24",
            "restingHeartRateInBeatsPerMinute": "sixty",  # Should be int
        }

        parser = HealthMetricsParser()

        with pytest.raises(TypeError):
            parser.parse(garmin_response)


class TestBatchParsing:
    """Test batch parsing of multiple records."""

    def test_parse_multiple_health_metrics(self):
        """Test parsing list of health metrics."""
        garmin_responses = [
            {
                "calendarDate": "2025-10-24",
                "restingHeartRateInBeatsPerMinute": 55,
                "heartRateVariabilityInMilliseconds": 62,
            },
            {
                "calendarDate": "2025-10-23",
                "restingHeartRateInBeatsPerMinute": 58,
                "heartRateVariabilityInMilliseconds": 59,
            },
        ]

        parser = HealthMetricsParser()
        metrics_list = [parser.parse(response) for response in garmin_responses]

        assert len(metrics_list) == 2
        assert metrics_list[0]["date"] == date(2025, 10, 24)
        assert metrics_list[1]["date"] == date(2025, 10, 23)

    def test_parse_multiple_workouts(self):
        """Test parsing list of workouts."""
        garmin_responses = [
            {
                "activityId": 111,
                "activityType": "running",
                "startTimeInSeconds": 1729756800,
                "durationInSeconds": 2400,
            },
            {
                "activityId": 222,
                "activityType": "cycling",
                "startTimeInSeconds": 1729843200,
                "durationInSeconds": 3600,
            },
        ]

        parser = WorkoutParser()
        workouts = [parser.parse(response) for response in garmin_responses]

        assert len(workouts) == 2
        assert workouts[0]["workout_type"] == "run"
        assert workouts[1]["workout_type"] == "bike"
