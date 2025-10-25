"""Contract tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.user import User


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints."""

    async def test_register_new_user_success(
        self, test_client: AsyncClient, test_db_session: AsyncSession
    ):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123",
            "full_name": "New User",
        }

        response = await test_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify user data
        user = data["user"]
        assert user["email"] == user_data["email"]
        assert user["full_name"] == user_data["full_name"]
        assert user["is_active"] is True
        assert user["is_verified"] is False
        assert user["is_garmin_connected"] is False
        assert "id" in user
        assert "created_at" in user

        # Verify tokens are non-empty strings
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert isinstance(data["refresh_token"], str)
        assert len(data["refresh_token"]) > 0

        # Verify user was created in database
        result = await test_db_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.email == user_data["email"]
        assert db_user.full_name == user_data["full_name"]

    async def test_register_duplicate_email_fails(
        self, test_client: AsyncClient, test_db_session: AsyncSession
    ):
        """Test that registering with duplicate email fails."""
        # Create first user
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePassword123",
            "full_name": "First User",
        }
        response1 = await test_client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201

        # Try to create second user with same email
        user_data2 = {
            "email": "duplicate@example.com",
            "password": "DifferentPassword456",
            "full_name": "Second User",
        }
        response2 = await test_client.post("/api/v1/auth/register", json=user_data2)

        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()

    async def test_register_invalid_email_fails(self, test_client: AsyncClient):
        """Test that registration with invalid email fails."""
        user_data = {
            "email": "not-an-email",
            "password": "SecurePassword123",
            "full_name": "Test User",
        }

        response = await test_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    async def test_register_short_password_fails(self, test_client: AsyncClient):
        """Test that registration with short password fails."""
        user_data = {
            "email": "test@example.com",
            "password": "short",  # Less than 8 characters
            "full_name": "Test User",
        }

        response = await test_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    async def test_login_success(
        self, test_client: AsyncClient, test_db_session: AsyncSession
    ):
        """Test successful user login."""
        # First register a user
        password = "SecurePassword123"
        user_data = {
            "email": "loginuser@example.com",
            "password": password,
            "full_name": "Login User",
        }
        register_response = await test_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201

        # Now login
        login_data = {
            "email": "loginuser@example.com",
            "password": password,
        }
        response = await test_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "user" in data
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify user data
        user = data["user"]
        assert user["email"] == user_data["email"]
        assert user["full_name"] == user_data["full_name"]

        # Verify tokens
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert isinstance(data["refresh_token"], str)
        assert len(data["refresh_token"]) > 0

    async def test_login_wrong_password_fails(
        self, test_client: AsyncClient, test_db_session: AsyncSession
    ):
        """Test that login with wrong password fails."""
        # First register a user
        user_data = {
            "email": "wrongpass@example.com",
            "password": "CorrectPassword123",
            "full_name": "Test User",
        }
        register_response = await test_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201

        # Try to login with wrong password
        login_data = {
            "email": "wrongpass@example.com",
            "password": "WrongPassword456",
        }
        response = await test_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user_fails(self, test_client: AsyncClient):
        """Test that login with non-existent email fails."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123",
        }
        response = await test_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_inactive_user_fails(
        self, test_client: AsyncClient, test_db_session: AsyncSession
    ):
        """Test that login fails for inactive users."""
        # Register a user
        user_data = {
            "email": "inactive@example.com",
            "password": "SecurePassword123",
            "full_name": "Inactive User",
        }
        register_response = await test_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201

        # Deactivate the user
        result = await test_db_session.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = result.scalar_one()
        user.is_active = False
        await test_db_session.commit()

        # Try to login
        login_data = {
            "email": "inactive@example.com",
            "password": "SecurePassword123",
        }
        response = await test_client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()

    async def test_email_normalization(
        self, test_client: AsyncClient, test_db_session: AsyncSession
    ):
        """Test that emails are normalized to lowercase."""
        # Register with mixed case email
        user_data = {
            "email": "MixedCase@Example.COM",
            "password": "SecurePassword123",
            "full_name": "Test User",
        }
        register_response = await test_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201

        # Verify stored as lowercase
        result = await test_db_session.execute(
            select(User).where(User.email == "mixedcase@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "mixedcase@example.com"

        # Login with different casing should work
        login_data = {
            "email": "MIXEDCASE@EXAMPLE.COM",
            "password": "SecurePassword123",
        }
        login_response = await test_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
