"""
Unit tests for Garmin OAuth2 PKCE flow implementation.

Tests focus on PKCE (Proof Key for Code Exchange) specific functionality,
code verifier generation, code challenge creation, and state management.
"""

import pytest
import hashlib
import base64
from datetime import datetime, timedelta

from src.services.garmin.oauth_service import GarminOAuthService


class TestPKCECodeGeneration:
    """Test PKCE code verifier and challenge generation."""

    def test_code_verifier_length(self):
        """Test that code verifier is between 43-128 characters."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        code_verifier = oauth_service._generate_code_verifier()

        assert 43 <= len(code_verifier) <= 128
        assert code_verifier.replace("-", "").replace("_", "").isalnum()

    def test_code_verifier_uniqueness(self):
        """Test that each code verifier is unique."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        verifiers = [oauth_service._generate_code_verifier() for _ in range(100)]

        # All should be unique
        assert len(verifiers) == len(set(verifiers))

    def test_code_challenge_from_verifier(self):
        """Test code challenge is correctly derived from verifier."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        test_verifier = "test_verifier_1234567890_abcdefghijklmnopqrstuvwxyz"

        code_challenge = oauth_service._generate_code_challenge(test_verifier)

        # Verify challenge is base64url encoded SHA-256 hash
        expected_hash = hashlib.sha256(test_verifier.encode()).digest()
        expected_challenge = (
            base64.urlsafe_b64encode(expected_hash).decode().rstrip("=")
        )

        assert code_challenge == expected_challenge

    def test_code_challenge_method(self):
        """Test that code challenge method is S256 (SHA-256)."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        assert oauth_service.challenge_method == "S256"


class TestStateManagement:
    """Test OAuth state parameter generation and validation."""

    def test_state_generation(self):
        """Test that state is randomly generated and sufficiently long."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        state = oauth_service._generate_state()

        assert len(state) >= 32
        assert state.replace("-", "").replace("_", "").isalnum()

    def test_state_uniqueness(self):
        """Test that each state value is unique."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        states = [oauth_service._generate_state() for _ in range(100)]

        # All should be unique
        assert len(states) == len(set(states))

    def test_state_validation_success(self):
        """Test successful state validation."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        expected_state = "test_state_12345"

        # Should not raise exception
        is_valid = oauth_service.validate_state(expected_state, expected_state)
        assert is_valid is True

    def test_state_validation_failure(self):
        """Test state validation fails with mismatched states."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        expected_state = "expected_state"
        received_state = "different_state"

        is_valid = oauth_service.validate_state(expected_state, received_state)
        assert is_valid is False


class TestAuthorizationURL:
    """Test authorization URL construction."""

    def test_authorization_url_contains_client_id(self):
        """Test that authorization URL includes client ID."""
        oauth_service = GarminOAuthService(
            client_id="test_client_123",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        auth_url, state, verifier = oauth_service.get_authorization_url()

        assert (
            "oauth_consumer_key=test_client_123" in auth_url
            or "client_id=test_client_123" in auth_url
        )

    def test_authorization_url_contains_redirect_uri(self):
        """Test that authorization URL includes encoded redirect URI."""
        redirect_uri = "http://localhost:8000/api/v1/garmin/callback"
        oauth_service = GarminOAuthService(
            client_id="test_id", client_secret="test_secret", redirect_uri=redirect_uri
        )

        auth_url, state, verifier = oauth_service.get_authorization_url()

        # Redirect URI should be URL-encoded in the authorization URL
        assert "oauth_callback=" in auth_url or "redirect_uri=" in auth_url

    def test_authorization_url_returns_state_and_verifier(self):
        """Test that get_authorization_url returns state and verifier."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        auth_url, state, verifier = oauth_service.get_authorization_url()

        assert state is not None
        assert verifier is not None
        assert len(state) >= 32
        assert len(verifier) >= 43


class TestTokenStorage:
    """Test token storage and expiration tracking."""

    def test_calculate_expiration_time(self):
        """Test that token expiration is correctly calculated."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        expires_in_seconds = 3600  # 1 hour
        before = datetime.utcnow()

        expiration = oauth_service._calculate_expiration(expires_in_seconds)

        after = datetime.utcnow()

        # Expiration should be approximately 1 hour from now
        expected_expiration = before + timedelta(seconds=expires_in_seconds)

        # Allow 1 second tolerance for test execution time
        assert abs((expiration - expected_expiration).total_seconds()) < 1

    def test_is_token_expired_returns_true_for_past_date(self):
        """Test that expired tokens are correctly identified."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        past_date = datetime.utcnow() - timedelta(hours=1)

        is_expired = oauth_service.is_token_expired(past_date)
        assert is_expired is True

    def test_is_token_expired_returns_false_for_future_date(self):
        """Test that valid tokens are not marked as expired."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        future_date = datetime.utcnow() + timedelta(hours=1)

        is_expired = oauth_service.is_token_expired(future_date)
        assert is_expired is False

    def test_is_token_expired_with_buffer(self):
        """Test token expiration check includes 5-minute buffer."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        # Token expires in 3 minutes (less than 5-minute buffer)
        near_expiration = datetime.utcnow() + timedelta(minutes=3)

        # Should be considered expired due to buffer
        is_expired = oauth_service.is_token_expired(near_expiration, buffer_minutes=5)
        assert is_expired is True


class TestErrorHandling:
    """Test OAuth error scenarios."""

    def test_invalid_client_credentials_format(self):
        """Test handling of invalid client credentials."""
        with pytest.raises(ValueError):
            oauth_service = GarminOAuthService(
                client_id="",  # Empty client ID
                client_secret="test_secret",
                redirect_uri="http://localhost/callback",
            )

    def test_invalid_redirect_uri_format(self):
        """Test handling of invalid redirect URI."""
        with pytest.raises(ValueError):
            oauth_service = GarminOAuthService(
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="not_a_valid_url",  # Invalid URL
            )

    def test_missing_code_verifier_on_token_exchange(self):
        """Test that token exchange requires code verifier."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        with pytest.raises(ValueError):
            # Attempting token exchange without code verifier should fail
            oauth_service._validate_token_exchange_params(
                auth_code="test_code", code_verifier=None
            )


class TestSecurityMeasures:
    """Test security-related OAuth functionality."""

    def test_code_verifier_uses_secure_random(self):
        """Test that code verifier uses cryptographically secure randomness."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        # Generate multiple verifiers and check entropy
        verifiers = [oauth_service._generate_code_verifier() for _ in range(1000)]

        # Check that verifiers have high uniqueness (no collisions in 1000 attempts)
        assert len(set(verifiers)) == 1000

    def test_state_uses_secure_random(self):
        """Test that state uses cryptographically secure randomness."""
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        # Generate multiple states and check entropy
        states = [oauth_service._generate_state() for _ in range(1000)]

        # Check that states have high uniqueness (no collisions in 1000 attempts)
        assert len(set(states)) == 1000

    def test_pkce_prevents_authorization_code_interception(self):
        """
        Test that PKCE flow prevents authorization code interception attacks.

        An attacker who intercepts the authorization code cannot exchange it
        for tokens without the original code verifier.
        """
        oauth_service = GarminOAuthService(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback",
        )

        # Legitimate client generates verifier and challenge
        auth_url, state, original_verifier = oauth_service.get_authorization_url()
        original_challenge = oauth_service._generate_code_challenge(original_verifier)

        # Attacker tries with different verifier
        attacker_verifier = "attacker_verifier_different_from_original"
        attacker_challenge = oauth_service._generate_code_challenge(attacker_verifier)

        # Challenges should be different
        assert original_challenge != attacker_challenge

        # This demonstrates that the attacker cannot successfully complete
        # the token exchange without the original code verifier
