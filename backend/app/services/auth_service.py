"""
services/auth_service.py — Dashboard authentication.

Strategy: JWT with short-lived access tokens + long-lived refresh tokens.
  - Access token: 15 minutes (in Authorization header)
  - Refresh token: 7 days (in HttpOnly cookie — JS cannot read it)

WhatsApp users do NOT need email/password.
Auth is only required for the React dashboard.

TODO: Implement in Sprint 6.
"""
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Handles JWT-based authentication for the dashboard."""

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate a user by email + password.

        Returns:
            {
                'access_token': str,   # Short-lived JWT (15 min)
                'refresh_token': str,  # Long-lived JWT (7 days)
                'user': dict,          # User public profile
            }

        Raises:
            ValueError: If credentials are invalid or user is inactive.

        TODO: Implement in Sprint 6.
        """
        raise NotImplementedError("Sprint 6")

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Generate a new access token from a valid refresh token.

        Returns:
            {'access_token': str}

        Raises:
            ValueError: If refresh token is invalid, expired, or revoked.

        TODO: Implement in Sprint 6.
        """
        raise NotImplementedError("Sprint 6")

    def logout(self, refresh_token: str) -> None:
        """
        Revoke a refresh token so it can no longer generate access tokens.

        TODO: Implement in Sprint 6.
        """
        raise NotImplementedError("Sprint 6")

    def validate_access_token(self, token: str) -> dict:
        """
        Validate an access token and return its claims.

        Returns:
            {'user_id': str, 'email': str, 'exp': int}

        Raises:
            ValueError: If token is invalid or expired.

        TODO: Implement in Sprint 6.
        """
        raise NotImplementedError("Sprint 6")

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password using bcrypt. TODO: Sprint 6."""
        raise NotImplementedError("Sprint 6")

    def verify_password(self, plaintext: str, hashed: str) -> bool:
        """Verify a plaintext password against a bcrypt hash. TODO: Sprint 6."""
        raise NotImplementedError("Sprint 6")
