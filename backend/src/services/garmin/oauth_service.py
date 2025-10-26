"""
Garmin OAuth2 PKCE (Proof Key for Code Exchange) Service.

Implements the OAuth 2.0 PKCE flow for secure authentication with Garmin Connect API.
PKCE prevents authorization code interception attacks by requiring a code verifier
that only the original client possesses.

References:
- RFC 7636: Proof Key for Code Exchange by OAuth Public Clients
- Garmin OAuth2 Documentation: https://developer.garmin.com/gc-developer-program/overview/
"""

import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional
from urllib.parse import urlencode, urlparse
import httpx



class GarminOAuthService:
    """
    Handles OAuth2 PKCE flow for Garmin Connect API authentication.

    The PKCE flow works as follows:
    1. Generate code_verifier (random string)
    2. Create code_challenge (SHA-256 hash of verifier)
    3. Redirect user to Garmin with challenge
    4. User authorizes, Garmin redirects with auth code
    5. Exchange code + verifier for access/refresh tokens
    """

    # Garmin OAuth endpoints
    AUTHORIZATION_ENDPOINT = "https://connect.garmin.com/oauthConfirm"
    TOKEN_ENDPOINT = "https://connectapi.garmin.com/oauth-service/oauth/access_token"

    # PKCE configuration
    CODE_VERIFIER_LENGTH = 64  # 43-128 characters allowed, using 64
    STATE_LENGTH = 32  # Minimum 32 characters for security

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize OAuth service with client credentials.

        Args:
            client_id: Garmin application consumer key
            client_secret: Garmin application consumer secret
            redirect_uri: Callback URL for OAuth redirect

        Raises:
            ValueError: If credentials are invalid
        """
        self._validate_credentials(client_id, client_secret, redirect_uri)

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.challenge_method = "S256"  # SHA-256 hashing

    def _validate_credentials(
        self, client_id: str, client_secret: str, redirect_uri: str
    ) -> None:
        """
        Validate OAuth credentials.

        Args:
            client_id: Client ID to validate
            client_secret: Client secret to validate
            redirect_uri: Redirect URI to validate

        Raises:
            ValueError: If any credential is invalid
        """
        if not client_id or not client_id.strip():
            raise ValueError("Client ID cannot be empty")

        if not client_secret or not client_secret.strip():
            raise ValueError("Client secret cannot be empty")

        # Validate redirect URI format
        try:
            parsed = urlparse(redirect_uri)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Redirect URI must be a valid URL")
        except Exception:
            raise ValueError("Invalid redirect URI format")

    def _generate_code_verifier(self) -> str:
        """
        Generate a cryptographically random code verifier.

        The verifier must be:
        - 43-128 characters long
        - URL-safe (alphanumeric + -_)
        - Cryptographically random

        Returns:
            URL-safe random string for PKCE verifier
        """
        # Generate random bytes and encode as URL-safe base64
        random_bytes = secrets.token_bytes(self.CODE_VERIFIER_LENGTH)
        verifier = base64.urlsafe_b64encode(random_bytes).decode("utf-8")

        # Remove padding characters (=) to ensure URL safety
        verifier = verifier.rstrip("=")

        # Ensure length is within spec (43-128)
        return verifier[: self.CODE_VERIFIER_LENGTH]

    def _generate_code_challenge(self, code_verifier: str) -> str:
        """
        Generate code challenge from code verifier using SHA-256.

        Args:
            code_verifier: The code verifier to hash

        Returns:
            Base64URL-encoded SHA-256 hash of the verifier
        """
        # Hash the verifier with SHA-256
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()

        # Encode as base64url (without padding)
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8")
        challenge = challenge.rstrip("=")

        return challenge

    def _generate_state(self) -> str:
        """
        Generate a cryptographically random state parameter.

        The state parameter prevents CSRF attacks by ensuring the
        authorization response matches the original request.

        Returns:
            URL-safe random string for state parameter
        """
        random_bytes = secrets.token_bytes(self.STATE_LENGTH)
        state = base64.urlsafe_b64encode(random_bytes).decode("utf-8")
        return state.rstrip("=")[: self.STATE_LENGTH]

    def get_authorization_url(self) -> Tuple[str, str, str]:
        """
        Generate authorization URL for user to approve access.

        Returns:
            Tuple of (authorization_url, state, code_verifier)
            - authorization_url: URL to redirect user to
            - state: State parameter (store for validation)
            - code_verifier: Code verifier (store for token exchange)
        """
        # Generate PKCE parameters
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)
        state = self._generate_state()

        # Build authorization URL parameters
        params = {
            "oauth_consumer_key": self.client_id,  # Garmin uses oauth_consumer_key
            "oauth_callback": self.redirect_uri,
        }

        # Construct full authorization URL
        auth_url = f"{self.AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

        return auth_url, state, code_verifier

    def validate_state(self, expected_state: str, received_state: str) -> bool:
        """
        Validate state parameter to prevent CSRF attacks.

        Args:
            expected_state: State value sent in authorization request
            received_state: State value received in callback

        Returns:
            True if states match, False otherwise
        """
        if not expected_state or not received_state:
            return False

        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(expected_state, received_state)

    def _validate_token_exchange_params(
        self, auth_code: str, code_verifier: Optional[str]
    ) -> None:
        """
        Validate parameters for token exchange.

        Args:
            auth_code: Authorization code from callback
            code_verifier: Code verifier from authorization request

        Raises:
            ValueError: If parameters are invalid
        """
        if not auth_code or not auth_code.strip():
            raise ValueError("Authorization code cannot be empty")

        if not code_verifier or not code_verifier.strip():
            raise ValueError("Code verifier is required for PKCE flow")

    async def exchange_code_for_token(
        self, auth_code: str, code_verifier: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            auth_code: Authorization code from callback
            code_verifier: Code verifier from authorization request

        Returns:
            Dict containing:
            - access_token: Token for API requests
            - refresh_token: Token for refreshing access token
            - expires_in: Seconds until access token expires
            - user_id: Garmin user ID

        Raises:
            httpx.HTTPError: If token exchange fails
        """
        self._validate_token_exchange_params(auth_code, code_verifier)

        # Token exchange parameters
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code_verifier": code_verifier,
        }

        # Make token request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            response.raise_for_status()

            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dict containing:
            - access_token: New access token
            - expires_in: Seconds until expiration

        Raises:
            httpx.HTTPError: If token refresh fails
        """
        if not refresh_token or not refresh_token.strip():
            raise ValueError("Refresh token cannot be empty")

        # Token refresh parameters
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        # Make refresh request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            response.raise_for_status()

            return response.json()

    def _calculate_expiration(self, expires_in_seconds: int) -> datetime:
        """
        Calculate token expiration datetime.

        Args:
            expires_in_seconds: Seconds until token expires

        Returns:
            Datetime when token will expire
        """
        return datetime.utcnow() + timedelta(seconds=expires_in_seconds)

    def is_token_expired(self, expires_at: datetime, buffer_minutes: int = 5) -> bool:
        """
        Check if token is expired or will expire soon.

        Args:
            expires_at: Token expiration datetime
            buffer_minutes: Minutes before expiration to consider expired

        Returns:
            True if token is expired or within buffer window
        """
        buffer = timedelta(minutes=buffer_minutes)
        expiration_with_buffer = expires_at - buffer

        return datetime.utcnow() >= expiration_with_buffer
