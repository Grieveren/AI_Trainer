"""
Garmin data caching service using Redis.

Implements 24-hour caching for Garmin API responses to minimize API calls
and improve performance. Includes cache key management and invalidation.
"""

from datetime import date
from typing import Optional, Dict, Any, List
import json
import logging
from functools import wraps

from src.database.redis import get_redis

logger = logging.getLogger(__name__)


class GarminCache:
    """Redis cache manager for Garmin API data."""

    # Cache TTLs (in seconds)
    HEALTH_METRICS_TTL = 86400  # 24 hours
    WORKOUT_LIST_TTL = 3600  # 1 hour (activities change more frequently)
    WORKOUT_DETAILS_TTL = 604800  # 7 days (historical data doesn't change)

    # Cache key prefixes
    HEALTH_PREFIX = "garmin:health"
    WORKOUT_LIST_PREFIX = "garmin:workouts:list"
    WORKOUT_DETAIL_PREFIX = "garmin:workouts:detail"

    def __init__(self):
        """Initialize cache manager."""
        self.redis = get_redis()

    # Health Metrics Caching

    def _make_health_key(self, user_id: str, target_date: date) -> str:
        """
        Generate cache key for health metrics.

        Format: garmin:health:{user_id}:{date}
        """
        return f"{self.HEALTH_PREFIX}:{user_id}:{target_date.isoformat()}"

    async def get_health_metrics(
        self, user_id: str, target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached health metrics.

        Args:
            user_id: User ID
            target_date: Date of metrics

        Returns:
            Cached metrics dict or None if not found
        """
        key = self._make_health_key(user_id, target_date)

        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                logger.debug(
                    f"Cache HIT: Health metrics for {user_id} on {target_date}"
                )
                return json.loads(cached_data)
            else:
                logger.debug(
                    f"Cache MISS: Health metrics for {user_id} on {target_date}"
                )
                return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    async def set_health_metrics(
        self, user_id: str, target_date: date, metrics: Dict[str, Any]
    ) -> bool:
        """
        Cache health metrics with 24-hour TTL.

        Args:
            user_id: User ID
            target_date: Date of metrics
            metrics: Metrics data to cache

        Returns:
            True if cached successfully
        """
        key = self._make_health_key(user_id, target_date)

        try:
            # Serialize to JSON
            serialized = json.dumps(metrics, default=str)

            # Set with TTL
            await self.redis.setex(key, self.HEALTH_METRICS_TTL, serialized)

            logger.debug(f"Cached health metrics for {user_id} on {target_date}")
            return True

        except Exception as e:
            logger.error(f"Error caching health metrics: {e}")
            return False

    async def invalidate_health_metrics(self, user_id: str, target_date: date) -> bool:
        """
        Invalidate cached health metrics.

        Args:
            user_id: User ID
            target_date: Date to invalidate

        Returns:
            True if invalidated successfully
        """
        key = self._make_health_key(user_id, target_date)

        try:
            await self.redis.delete(key)
            logger.debug(
                f"Invalidated health metrics cache for {user_id} on {target_date}"
            )
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False

    # Workout List Caching

    def _make_workout_list_key(
        self, user_id: str, start_date: date, end_date: date
    ) -> str:
        """
        Generate cache key for workout list.

        Format: garmin:workouts:list:{user_id}:{start_date}:{end_date}
        """
        return (
            f"{self.WORKOUT_LIST_PREFIX}:{user_id}:"
            f"{start_date.isoformat()}:{end_date.isoformat()}"
        )

    async def get_workout_list(
        self, user_id: str, start_date: date, end_date: date
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached workout list.

        Args:
            user_id: User ID
            start_date: Start date of range
            end_date: End date of range

        Returns:
            List of workouts or None if not found
        """
        key = self._make_workout_list_key(user_id, start_date, end_date)

        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                logger.debug(
                    f"Cache HIT: Workout list for {user_id} "
                    f"({start_date} to {end_date})"
                )
                return json.loads(cached_data)
            else:
                logger.debug(
                    f"Cache MISS: Workout list for {user_id} "
                    f"({start_date} to {end_date})"
                )
                return None
        except Exception as e:
            logger.error(f"Error retrieving workout list from cache: {e}")
            return None

    async def set_workout_list(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        workouts: List[Dict[str, Any]],
    ) -> bool:
        """
        Cache workout list with 1-hour TTL.

        Args:
            user_id: User ID
            start_date: Start date of range
            end_date: End date of range
            workouts: List of workout data

        Returns:
            True if cached successfully
        """
        key = self._make_workout_list_key(user_id, start_date, end_date)

        try:
            serialized = json.dumps(workouts, default=str)

            await self.redis.setex(key, self.WORKOUT_LIST_TTL, serialized)

            logger.debug(
                f"Cached workout list for {user_id} " f"({start_date} to {end_date})"
            )
            return True

        except Exception as e:
            logger.error(f"Error caching workout list: {e}")
            return False

    # Workout Details Caching

    def _make_workout_detail_key(self, user_id: str, activity_id: str) -> str:
        """
        Generate cache key for workout details.

        Format: garmin:workouts:detail:{user_id}:{activity_id}
        """
        return f"{self.WORKOUT_DETAIL_PREFIX}:{user_id}:{activity_id}"

    async def get_workout_details(
        self, user_id: str, activity_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached workout details.

        Args:
            user_id: User ID
            activity_id: Garmin activity ID

        Returns:
            Workout details or None if not found
        """
        key = self._make_workout_detail_key(user_id, activity_id)

        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                logger.debug(f"Cache HIT: Workout details for activity {activity_id}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache MISS: Workout details for activity {activity_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving workout details from cache: {e}")
            return None

    async def set_workout_details(
        self, user_id: str, activity_id: str, details: Dict[str, Any]
    ) -> bool:
        """
        Cache workout details with 7-day TTL.

        Historical workout data doesn't change, so longer TTL is appropriate.

        Args:
            user_id: User ID
            activity_id: Garmin activity ID
            details: Workout details to cache

        Returns:
            True if cached successfully
        """
        key = self._make_workout_detail_key(user_id, activity_id)

        try:
            serialized = json.dumps(details, default=str)

            await self.redis.setex(key, self.WORKOUT_DETAILS_TTL, serialized)

            logger.debug(f"Cached workout details for activity {activity_id}")
            return True

        except Exception as e:
            logger.error(f"Error caching workout details: {e}")
            return False

    # Bulk Operations

    async def invalidate_user_cache(self, user_id: str) -> int:
        """
        Invalidate all cached data for a user.

        Useful when user disconnects Garmin account.

        Args:
            user_id: User ID

        Returns:
            Number of keys deleted
        """
        try:
            # Find all keys for this user
            patterns = [
                f"{self.HEALTH_PREFIX}:{user_id}:*",
                f"{self.WORKOUT_LIST_PREFIX}:{user_id}:*",
                f"{self.WORKOUT_DETAIL_PREFIX}:{user_id}:*",
            ]

            total_deleted = 0
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    deleted = await self.redis.delete(*keys)
                    total_deleted += deleted

            logger.info(f"Invalidated {total_deleted} cache keys for user {user_id}")
            return total_deleted

        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")
            return 0

    async def get_cache_stats(self, user_id: str) -> Dict[str, int]:
        """
        Get cache statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dict with cache statistics
        """
        try:
            health_keys = await self.redis.keys(f"{self.HEALTH_PREFIX}:{user_id}:*")
            workout_list_keys = await self.redis.keys(
                f"{self.WORKOUT_LIST_PREFIX}:{user_id}:*"
            )
            workout_detail_keys = await self.redis.keys(
                f"{self.WORKOUT_DETAIL_PREFIX}:{user_id}:*"
            )

            return {
                "health_metrics_cached": len(health_keys),
                "workout_lists_cached": len(workout_list_keys),
                "workout_details_cached": len(workout_detail_keys),
                "total_cached": len(health_keys)
                + len(workout_list_keys)
                + len(workout_detail_keys),
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "health_metrics_cached": 0,
                "workout_lists_cached": 0,
                "workout_details_cached": 0,
                "total_cached": 0,
            }


# Decorator for automatic caching
def cache_garmin_health(func):
    """
    Decorator to automatically cache health metrics fetching.

    Usage:
        @cache_garmin_health
        async def get_daily_metrics(self, user_id, target_date):
            ...
    """

    @wraps(func)
    async def wrapper(self, user_id: str, target_date: date, *args, **kwargs):
        cache = GarminCache()

        # Try to get from cache first
        cached_data = await cache.get_health_metrics(user_id, target_date)
        if cached_data is not None:
            return cached_data

        # Cache miss - fetch from API
        result = await func(self, user_id, target_date, *args, **kwargs)

        # Cache the result
        if result:
            await cache.set_health_metrics(user_id, target_date, result)

        return result

    return wrapper


def cache_garmin_workouts(ttl_hours: int = 1):
    """
    Decorator to automatically cache workout list fetching.

    Args:
        ttl_hours: Cache TTL in hours (default: 1)

    Usage:
        @cache_garmin_workouts(ttl_hours=24)
        async def get_activities(self, user_id, start_date, end_date):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            self, user_id: str, start_date: date, end_date: date, *args, **kwargs
        ):
            cache = GarminCache()

            # Try to get from cache first
            cached_data = await cache.get_workout_list(user_id, start_date, end_date)
            if cached_data is not None:
                return cached_data

            # Cache miss - fetch from API
            result = await func(self, user_id, start_date, end_date, *args, **kwargs)

            # Cache the result
            if result:
                await cache.set_workout_list(user_id, start_date, end_date, result)

            return result

        return wrapper

    return decorator
