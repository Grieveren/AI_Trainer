"""JWT authentication middleware."""

import os
from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class JWTBearer(HTTPBearer):
    """JWT Bearer token authentication."""

    def __init__(self, auto_error: bool = True):
        """Initialize JWT Bearer."""
        super().__init__(auto_error=auto_error)
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-me")
        self.algorithm = "HS256"

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        """Validate JWT token from request."""
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(
            request
        )

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                )

            token = credentials.credentials
            if not self.verify_jwt(token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token.",
                )

            # Decode and attach user info to request state
            try:
                payload = jwt.decode(
                    token, self.secret_key, algorithms=[self.algorithm]
                )
                request.state.user_id = payload.get("user_id")
                request.state.email = payload.get("email")
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token has expired.",
                )
            except jwt.InvalidTokenError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token.",
                )

            return credentials

        return None

    def verify_jwt(self, token: str) -> bool:
        """Verify JWT token."""
        try:
            jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

    def decode_jwt(self, token: str) -> Optional[dict]:
        """Decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


# Global JWT bearer instance
jwt_bearer = JWTBearer()


def get_current_user_id(request: Request) -> int:
    """Get current user ID from request state."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id
