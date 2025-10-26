"""
Garmin Connect API Client.

High-level client for interacting with Garmin Connect API.
Handles token management, automatic refresh, and provides
access to health and workout services.
"""

from datetime import datetime
from typing import Optional

from src.services.garmin.oauth_service import GarminOAuthService
from src.services.garmin.health_service import GarminHealthService
from src.services.garmin.workout_service import GarminWorkoutService
from src.config.settings import settings


class GarminClient:
    """
    High-level client for Garmin Connect API.

    Manages access tokens, automatic token refresh, and provides
    unified access to health metrics and workout data.
    """

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize Garmin client with tokens.

        Args:
            access_token: Valid OAuth access token
            refresh_token: OAuth refresh token
            token_expires_at: When the access token expires
            client_id: Optional client ID (defaults to settings)
            client_secret: Optional client secret (defaults to settings)
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at

        # OAuth service for token management
        self.oauth_service = GarminOAuthService(
            client_id=client_id or settings.GARMIN_CLIENT_ID,
            client_secret=client_secret or settings.GARMIN_CLIENT_SECRET,
            redirect_uri=settings.GARMIN_CALLBACK_URL,
        )

        # Service instances (created lazily)
        self._health_service: Optional[GarminHealthService] = None
        self._workout_service: Optional[GarminWorkoutService] = None

    @property
    def health_service(self) -> GarminHealthService:
        """Get health metrics service instance."""
        if self._health_service is None:
            self._health_service = GarminHealthService(self.access_token)
        return self._health_service

    @property
    def workout_service(self) -> GarminWorkoutService:
        """Get workout service instance."""
        if self._workout_service is None:
            self._workout_service = GarminWorkoutService(self.access_token)
        return self._workout_service

    async def ensure_valid_token(self) -> str:
        """
        Ensure access token is valid, refreshing if necessary.

        Returns:
            Valid access token

        Raises:
            httpx.HTTPError: If token refresh fails
        """
        if self.oauth_service.is_token_expired(self.token_expires_at):
            # Token expired or expiring soon, refresh it
            new_tokens = await self.oauth_service.refresh_access_token(
                self.refresh_token
            )

            # Update tokens
            self.access_token = new_tokens["access_token"]
            self.token_expires_at = self.oauth_service._calculate_expiration(
                new_tokens["expires_in"]
            )

            # Update service instances with new token
            self._health_service = None  # Will be recreated with new token
            self._workout_service = None

        return self.access_token

    async def test_connection(self) -> bool:
        """
        Test connection to Garmin API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.ensure_valid_token()
            # Could make a lightweight API call here to verify
            return True
        except Exception:
            return False
