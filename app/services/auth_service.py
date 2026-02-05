"""Authentication service for admin access."""
from typing import Optional
import bcrypt

from app.core.config import settings
from app.core.security import create_access_token


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        """Initialize auth service."""
        # In production, this should be replaced with database storage
        # Hash password during initialization
        password_bytes = settings.security.admin_password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        self._hashed_password = bcrypt.hashpw(password_bytes, salt)

    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate admin user and return token.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            Access token if authentication successful, None otherwise
        """
        if username != settings.security.admin_username:
            return None

        # Verify password
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
