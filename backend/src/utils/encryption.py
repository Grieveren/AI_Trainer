"""Encryption utilities for sensitive data like tokens."""

from cryptography.fernet import Fernet
from src.config.settings import get_settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self):
        """Initialize encryption service with settings."""
        settings = get_settings()
        # In production, this should be loaded from environment variable
        # For now, generate a key if not set
        key = settings.jwt_secret_key.encode()[:32]  # Use first 32 bytes
        # Pad to 32 bytes if needed
        if len(key) < 32:
            key = key + b"0" * (32 - len(key))
        # Fernet requires base64 encoded 32-byte key
        import base64

        self.cipher = Fernet(base64.urlsafe_b64encode(key))

    def encrypt(self, data: str) -> str:
        """Encrypt a string.

        Args:
            data: Plain text string to encrypt

        Returns:
            Encrypted string
        """
        encrypted_bytes = self.cipher.encrypt(data.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string.

        Args:
            encrypted_data: Encrypted string

        Returns:
            Decrypted plain text string

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
        return decrypted_bytes.decode()
