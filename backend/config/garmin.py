"""Garmin OAuth configuration."""

import os


class GarminConfig:
    """Configuration for Garmin Connect API integration."""

    def __init__(self):
        """Initialize Garmin configuration from environment."""
        self.client_id: str = os.getenv("GARMIN_CLIENT_ID", "")
        self.client_secret: str = os.getenv("GARMIN_CLIENT_SECRET", "")
        self.redirect_uri: str = os.getenv(
            "GARMIN_REDIRECT_URI", "http://localhost:8000/api/v1/garmin/callback"
        )

        # OAuth 2.0 PKCE endpoints
        self.authorization_endpoint: str = "https://connect.garmin.com/oauthConfirm"
        self.token_endpoint: str = (
            "https://connectapi.garmin.com/oauth-service/oauth/access_token"
        )

        # API base URL
        self.api_base_url: str = "https://apis.garmin.com"

        # Scopes required for health and workout data
        self.scopes: list[str] = [
            "garmin:activities_read",
            "garmin:health_read",
            "garmin:sleep_read",
            "garmin:hrv_read",
        ]

        # Request timeout (seconds)
        self.timeout: int = int(os.getenv("GARMIN_TIMEOUT", "30"))

        # Cache TTL for Garmin data (24 hours in seconds)
        self.cache_ttl: int = 86400

        # Retry configuration
        self.max_retries: int = 3
        self.retry_delay: int = 60  # seconds

    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.client_id:
            raise ValueError("GARMIN_CLIENT_ID environment variable is required")
        if not self.client_secret:
            raise ValueError("GARMIN_CLIENT_SECRET environment variable is required")
        return True

    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL.

        Args:
            state: CSRF protection state parameter

        Returns:
            Full authorization URL with query parameters
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorization_endpoint}?{query_string}"


# Global configuration instance
garmin_config = GarminConfig()
