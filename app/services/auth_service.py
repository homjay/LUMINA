"""Authentication service for admin access."""
from typing import Optional
import bcrypt
import hashlib
import os

from app.core.config import settings
from app.core.security import create_access_token


def hmac_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


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

        # Load API keys from database
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from storage."""
        try:
            if settings.storage.type == "sqlite":
                import sqlite3
                db_path = settings.storage.sqlite_path
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    # Create table if not exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS api_keys (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            key TEXT UNIQUE NOT NULL,
                            name TEXT,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            expires_at TEXT,
                            is_active BOOLEAN DEFAULT 1
                        )
                    """)
                    conn.commit()
                    # Load active non-expired keys
                    cursor.execute("""
                        SELECT key FROM api_keys
                        WHERE is_active = 1
                        AND (expires_at IS NULL OR datetime(expires_at) > datetime('now')
                        """)
                    return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            print(f"Warning: Failed to load API keys from database: {e}")

        # Fallback to environment variable
        env_key = os.environ.get("API_KEY")
        return {env_key} if env_key else set()

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

    async def verify_api_key(self, api_key: str) -> bool:
        """Verify a long-term API key.

        Args:
            api_key: API key to verify

        Returns:
            True if API key is valid, False otherwise
        """
        if not self.api_keys:
            return False

        # Constant-time comparison with all stored keys
        for stored_key in self.api_keys:
            if hmac_compare(api_key, stored_key):
                return True
        return False

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

    async def verify_token_or_api_key(self, token: str, api_key: Optional[str] = None) -> bool:
        """Verify either a JWT token or an API key.

        Args:
            token: JWT access token
            api_key: Optional API key

        Returns:
            True if either credential is valid, False otherwise
        """
        # Check API key first (if provided)
        if api_key and await self.verify_api_key(api_key):
            return True

        # Fall back to JWT token verification
        return await self.verify_token(token)


# Global service instance
auth_service = AuthService()
