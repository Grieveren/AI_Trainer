"""JWT token service for authentication."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from src.config.settings import get_settings


class JWTService:
    """Service for creating and verifying JWT tokens."""

    def __init__(self):
        """Initialize JWT service with settings."""
        self.settings = get_settings()

    def create_access_token(
        self, user_id: uuid.UUID, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new access token.

        Args:
            user_id: User ID to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT access token
        """
        if expires_delta is None:
            expires_delta = timedelta(
                minutes=self.settings.jwt_access_token_expire_minutes
            )

        now = datetime.utcnow()
        expire = now + expires_delta

        to_encode = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": expire,
        }

        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        return encoded_jwt

    def create_refresh_token(
        self, user_id: uuid.UUID, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new refresh token.

        Args:
            user_id: User ID to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT refresh token
        """
        if expires_delta is None:
            expires_delta = timedelta(days=self.settings.jwt_refresh_token_expire_days)

        now = datetime.utcnow()
        expire = now + expires_delta

        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expire,
        }

        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        return encoded_jwt

    def verify_token(self, token: str, expected_type: str) -> dict:
        """Verify a JWT token and return its payload.

        Args:
            token: JWT token to verify
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token is invalid or expired
            ValueError: If token type doesn't match expected type
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )

            token_type = payload.get("type")
            if token_type != expected_type:
                raise ValueError(
                    f"Invalid token type. Expected {expected_type}, got {token_type}"
                )

            return payload

        except JWTError as e:
            raise e

    def get_user_id_from_token(self, token: str) -> Optional[uuid.UUID]:
        """Extract user ID from a token without type checking.

        Args:
            token: JWT token

        Returns:
            User ID if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            user_id_str = payload.get("sub")
            if user_id_str:
                return uuid.UUID(user_id_str)
            return None
        except (JWTError, ValueError):
            return None
