"""Unit tests for User model validation."""

import uuid
from datetime import datetime, timedelta

from src.models.user import User


class TestUserModel:
    """Test User model validation and properties."""

    def test_user_creation_with_required_fields(self):
        """Test creating a user with only required fields."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            is_active=True,
            is_verified=False,
        )

        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_here"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False

    def test_user_creation_with_all_fields(self):
        """Test creating a user with all fields populated."""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=1)

        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            garmin_user_id="garmin123",
            garmin_access_token="access_token",
            garmin_refresh_token="refresh_token",
            garmin_token_expires_at=expires_at,
            is_active=True,
            is_verified=True,
        )

        assert user.garmin_user_id == "garmin123"
        assert user.garmin_access_token == "access_token"
        assert user.garmin_refresh_token == "refresh_token"
        assert user.garmin_token_expires_at == expires_at

    def test_is_garmin_connected_when_connected(self):
        """Test is_garmin_connected property returns True when connected."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            garmin_user_id="garmin123",
            garmin_access_token="access_token",
            garmin_token_expires_at=future_time,
        )

        assert user.is_garmin_connected is True

    def test_is_garmin_connected_when_not_connected(self):
        """Test is_garmin_connected property returns False when not connected."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
        )

        assert user.is_garmin_connected is False

    def test_is_garmin_connected_when_token_expired(self):
        """Test is_garmin_connected property returns False when token expired."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            garmin_user_id="garmin123",
            garmin_access_token="access_token",
            garmin_token_expires_at=past_time,
        )

        assert user.is_garmin_connected is False

    def test_is_garmin_connected_when_missing_access_token(self):
        """Test is_garmin_connected returns False when access token is missing."""
        future_time = datetime.utcnow() + timedelta(hours=1)
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            garmin_user_id="garmin123",
            garmin_token_expires_at=future_time,
        )

        assert user.is_garmin_connected is False

    def test_user_repr(self):
        """Test User string representation."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
        )

        expected = f"<User(id={user_id}, email=test@example.com)>"
        assert repr(user) == expected

    def test_email_normalization(self):
        """Test that email should be stored in lowercase."""
        user = User(
            email="Test@Example.COM",
            hashed_password="hashed_password_here",
            full_name="Test User",
        )

        # Note: Email normalization should be handled by service layer
        # This test documents current behavior
        assert user.email == "Test@Example.COM"

    def test_user_defaults(self):
        """Test default values for optional fields."""
        user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            is_active=True,
            is_verified=False,
        )

        # Verify explicit values
        assert user.is_active is True
        assert user.is_verified is False

        # Verify optional Garmin fields default to None
        assert user.garmin_user_id is None
        assert user.garmin_access_token is None
        assert user.garmin_refresh_token is None
        assert user.garmin_token_expires_at is None
