"""Unit tests for JWT token service."""

import pytest
import uuid
from datetime import datetime, timedelta
from jose import jwt, JWTError

from src.services.jwt_service import JWTService
from src.config.settings import get_settings


@pytest.fixture
def jwt_service():
    """Create a JWT service instance."""
    return JWTService()


@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return uuid.uuid4()


class TestJWTService:
    """Test JWT token creation and validation."""

    def test_create_access_token(self, jwt_service, test_user_id):
        """Test creating an access token."""
        token = jwt_service.create_access_token(user_id=test_user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, jwt_service, test_user_id):
        """Test creating a refresh token."""
        token = jwt_service.create_refresh_token(user_id=test_user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_correct_claims(self, jwt_service, test_user_id):
        """Test that access token contains the correct claims."""
        settings = get_settings()
        token = jwt_service.create_access_token(user_id=test_user_id)

        # Decode without verification to inspect claims
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == str(test_user_id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_contains_correct_claims(self, jwt_service, test_user_id):
        """Test that refresh token contains the correct claims."""
        settings = get_settings()
        token = jwt_service.create_refresh_token(user_id=test_user_id)

        # Decode without verification to inspect claims
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == str(test_user_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_expiration(self, jwt_service, test_user_id):
        """Test that access token has correct expiration time."""
        settings = get_settings()
        token = jwt_service.create_access_token(user_id=test_user_id)

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        expected_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

        # Allow 1 second tolerance for test execution time
        actual_delta = exp_time - iat_time
        assert abs(actual_delta - expected_delta) < timedelta(seconds=1)

    def test_refresh_token_expiration(self, jwt_service, test_user_id):
        """Test that refresh token has correct expiration time."""
        settings = get_settings()
        token = jwt_service.create_refresh_token(user_id=test_user_id)

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        # Verify expiration is set and in the future
        assert "exp" in payload
        assert "iat" in payload
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])

        # Verify expiration is after issuance
        assert exp_time > iat_time

        # Verify it's approximately the right duration (within 1 day tolerance for timezone issues)
        expected_seconds = settings.jwt_refresh_token_expire_days * 24 * 60 * 60
        actual_seconds = (exp_time - iat_time).total_seconds()
        assert abs(actual_seconds - expected_seconds) < 86400  # 1 day tolerance

    def test_verify_valid_access_token(self, jwt_service, test_user_id):
        """Test verifying a valid access token."""
        token = jwt_service.create_access_token(user_id=test_user_id)
        payload = jwt_service.verify_token(token, expected_type="access")

        assert payload is not None
        assert payload["sub"] == str(test_user_id)
        assert payload["type"] == "access"

    def test_verify_valid_refresh_token(self, jwt_service, test_user_id):
        """Test verifying a valid refresh token."""
        token = jwt_service.create_refresh_token(user_id=test_user_id)
        payload = jwt_service.verify_token(token, expected_type="refresh")

        assert payload is not None
        assert payload["sub"] == str(test_user_id)
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self, jwt_service, test_user_id):
        """Test that verifying a token with wrong type fails."""
        access_token = jwt_service.create_access_token(user_id=test_user_id)

        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_service.verify_token(access_token, expected_type="refresh")

    def test_verify_expired_token(self, jwt_service, test_user_id):
        """Test that verifying an expired token fails."""
        # Create a token that expires immediately
        token = jwt_service.create_access_token(
            user_id=test_user_id, expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(JWTError):
            jwt_service.verify_token(token, expected_type="access")

    def test_verify_invalid_token(self, jwt_service):
        """Test that verifying an invalid token fails."""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            jwt_service.verify_token(invalid_token, expected_type="access")

    def test_verify_tampered_token(self, jwt_service, test_user_id):
        """Test that verifying a tampered token fails."""
        token = jwt_service.create_access_token(user_id=test_user_id)

        # Tamper with the token by changing a character
        tampered_token = token[:-10] + "X" + token[-9:]

        with pytest.raises(JWTError):
            jwt_service.verify_token(tampered_token, expected_type="access")

    def test_get_user_id_from_token(self, jwt_service, test_user_id):
        """Test extracting user ID from a valid token."""
        token = jwt_service.create_access_token(user_id=test_user_id)
        extracted_id = jwt_service.get_user_id_from_token(token)

        assert extracted_id == test_user_id

    def test_get_user_id_from_invalid_token(self, jwt_service):
        """Test that extracting user ID from invalid token returns None."""
        invalid_token = "invalid.token.here"

        extracted_id = jwt_service.get_user_id_from_token(invalid_token)
        assert extracted_id is None

    def test_create_token_with_custom_expiration(self, jwt_service, test_user_id):
        """Test creating a token with custom expiration time."""
        custom_delta = timedelta(hours=2)
        token = jwt_service.create_access_token(
            user_id=test_user_id, expires_delta=custom_delta
        )

        settings = get_settings()
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        actual_delta = exp_time - iat_time

        assert abs(actual_delta - custom_delta) < timedelta(seconds=1)

    def test_tokens_are_different_for_same_user(self, jwt_service, test_user_id):
        """Test that multiple tokens for same user can be created and verified independently."""
        import time

        token1 = jwt_service.create_access_token(user_id=test_user_id)
        time.sleep(
            1
        )  # Ensure different iat timestamp (1 second minimum for iat precision)
        token2 = jwt_service.create_access_token(user_id=test_user_id)

        # Both tokens should be valid
        payload1 = jwt_service.verify_token(token1, expected_type="access")
        payload2 = jwt_service.verify_token(token2, expected_type="access")

        # Both should have the same user ID but different timestamps
        assert payload1["sub"] == payload2["sub"]
        assert payload1["iat"] != payload2["iat"]
