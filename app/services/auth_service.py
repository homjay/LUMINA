"""Authentication service for admin access."""
from typing import Optional
import bcrypt
import hashlib

from app.core.config import settings
from app.core.security import create_access_token


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        """Initialize auth service."""
        # Store: bcrypt(SHA-256(password)) for double hashing
        # Client sends: SHA-256(password)
        # Server verifies: bcrypt(client_hash) == stored_hash

        # Use fixed salt for password (derived from SECRET_KEY)
        # This ensures the hash is consistent across restarts
        secret = settings.security.secret_key.encode('utf-8')[:32]
        salt = hashlib.sha256(secret).hexdigest()[:22]  # bcrypt salt is 22 chars

        # Double hash: SHA-256 first, then bcrypt
        password_hash = hashlib.sha256(settings.security.admin_password.encode()).hexdigest()
        password_bytes = password_hash.encode('utf-8')[:72]

        # Manually create bcrypt hash with our salt
        self._hashed_password = bcrypt.hashpw(password_bytes, salt.encode('utf-8'))

    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate admin user and return token.

        Args:
            username: Admin username
            password: Password hash from client (SHA-256)

        Returns:
            Access token if authentication successful, None otherwise
        """
        if username != settings.security.admin_username:
            return None

        # Verify password hash (client already sent SHA-256 hash)
        password_bytes = password.encode('utf-8')[:72]
        if not bcrypt.checkpw(password_bytes, self._hashed_password):
            return None

        # Create access token
        token_data = {
            "sub": username,
            "type": "admin"
        }
        return create_access_token(token_data)

    async def verify_token(self, token: str) -> bool:
        """Verify an access token.

        Args:
            token: Access token

        Returns:
            True if token is valid, False otherwise
        """
        from app.core.security import decode_access_token

        payload = decode_access_token(token)
        if not payload:
            return False

        # Check if it's an admin token
        return payload.get("type") == "admin"


# Global service instance
auth_service = AuthService()
