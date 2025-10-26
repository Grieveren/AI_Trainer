"""
Garmin Health Metrics Service.

Fetches daily health/wellness data from Garmin Connect API including:
- Heart Rate Variability (HRV)
- Resting Heart Rate
- Sleep duration and quality
- Stress levels

Includes retry logic and error handling for production reliability.
"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional
import httpx
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from src.services.garmin.parsers import HealthMetricsParser
from src.services.garmin.cache import GarminCache

logger = logging.getLogger(__name__)


class GarminAPIError(Exception):
    """Base exception for Garmin API errors."""

    pass


class GarminUnauthorizedError(GarminAPIError):
    """Raised when access token is invalid or expired."""

    pass


class GarminRateLimitError(GarminAPIError):
    """Raised when API rate limit is exceeded."""

    pass


class GarminHealthService:
    """Service for fetching health metrics from Garmin API."""

    BASE_URL = "https://apis.garmin.com/wellness-api/rest"
    MAX_RETRIES = 3
    RETRY_WAIT_MIN = 1  # seconds
    RETRY_WAIT_MAX = 10  # seconds
    REQUEST_TIMEOUT = 30  # seconds

    def __init__(self, access_token: str, user_id: Optional[str] = None):
        """
        Initialize health service with access token.

        Args:
            access_token: Valid OAuth access token
            user_id: Optional user ID for caching
        """
        self.access_token = access_token
        self.user_id = user_id
        self.parser = HealthMetricsParser()
        self.cache = GarminCache()

    async def get_daily_metrics(self, target_date: date) -> Dict[str, Any]:
        """
        Fetch health metrics for a specific date with caching and retry logic.

        Checks Redis cache first (24-hour TTL), fetches from API if cache miss.

        Args:
            target_date: Date to fetch metrics for

        Returns:
            Dict with parsed health metrics

        Raises:
            GarminUnauthorizedError: If access token is invalid
            GarminRateLimitError: If rate limit exceeded
            GarminAPIError: For other API errors
        """
        # Try cache first if user_id available
        if self.user_id:
            cached_data = await self.cache.get_health_metrics(self.user_id, target_date)
            if cached_data is not None:
                return cached_data

        # Cache miss - fetch from API
        metrics = await self._fetch_daily_metrics(target_date)

        # Cache the result if user_id available
        if self.user_id and metrics:
            await self.cache.set_health_metrics(self.user_id, target_date, metrics)

        return metrics

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _fetch_daily_metrics(self, target_date: date) -> Dict[str, Any]:
        """
        Internal method to fetch health metrics from Garmin API with retry logic.

        Args:
            target_date: Date to fetch metrics for

        Returns:
            Dict with parsed health metrics

        Raises:
            GarminUnauthorizedError: If access token is invalid
            GarminRateLimitError: If rate limit exceeded
            GarminAPIError: For other API errors
        """
        # Convert date to Unix timestamps for API
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        start_timestamp = int(start_datetime.timestamp())
        end_timestamp = int(end_datetime.timestamp())

        # Build API URL
        url = f"{self.BASE_URL}/dailies"
        params = {
            "uploadStartTimeInSeconds": start_timestamp,
            "uploadEndTimeInSeconds": end_timestamp,
        }

        # Make API request
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(url, params=params, headers=headers)

                # Handle specific error codes
                if response.status_code == 401:
                    logger.error(
                        f"Unauthorized access to Garmin API for date {target_date}"
                    )
                    raise GarminUnauthorizedError("Access token expired or invalid")

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", 60)
                    logger.warning(
                        f"Rate limit exceeded. Retry after {retry_after} seconds"
                    )
                    raise GarminRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s"
                    )

                if response.status_code == 404:
                    # No data for this date (not an error)
                    logger.info(f"No health data available for {target_date}")
                    return self._empty_metrics(target_date)

                # Raise for other HTTP errors
                response.raise_for_status()

                # Parse response
                data = response.json()

                # API returns array, get first item
                if data and len(data) > 0:
                    logger.debug(
                        f"Successfully fetched health metrics for {target_date}"
                    )
                    return self.parser.parse(data[0])
                else:
                    logger.info(f"No health metrics returned for {target_date}")
                    return self._empty_metrics(target_date)

        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching health metrics for {target_date}: {e}")
            raise  # Will trigger retry

        except httpx.NetworkError as e:
            logger.error(
                f"Network error fetching health metrics for {target_date}: {e}"
            )
            raise  # Will trigger retry

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching health metrics for {target_date}: {e}")
            raise GarminAPIError(f"HTTP {e.response.status_code}: {e}") from e

        except Exception as e:
            logger.exception(
                f"Unexpected error fetching health metrics for {target_date}: {e}"
            )
            raise GarminAPIError(f"Unexpected error: {e}") from e

    def _empty_metrics(self, target_date: date) -> Dict[str, Any]:
        """Return empty metrics structure for a date."""
        return {
            "date": target_date,
            "hrv_ms": None,
            "resting_hr": None,
            "sleep_duration_minutes": None,
            "sleep_score": None,
            "stress_level": None,
        }

    async def get_metrics_range(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Fetch health metrics for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of daily health metrics

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Convert dates to timestamps
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        start_timestamp = int(start_datetime.timestamp())
        end_timestamp = int(end_datetime.timestamp())

        # Build API URL
        url = f"{self.BASE_URL}/dailies"
        params = {
            "uploadStartTimeInSeconds": start_timestamp,
            "uploadEndTimeInSeconds": end_timestamp,
        }

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 401:
                raise Exception("Unauthorized - access token expired or invalid")

            response.raise_for_status()

            # Parse all responses
            data = response.json()
            return [self.parser.parse(item) for item in data]
