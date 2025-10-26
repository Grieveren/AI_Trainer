"""JWT authentication middleware."""

import os
from typing import Optional

from jose import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database.connection import get_sync_db_session
from src.models.user import User


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


def get_current_user_id(request: Request) -> str:
    """Get current user ID from request state."""
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer),
) -> User:
    """
    Get current authenticated user from JWT token.

    This is a FastAPI dependency that can be used in route handlers.

    Usage:
        @app.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Decode token to get user_id
    payload = jwt_bearer.decode_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Fetch user from database
    with get_sync_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Detach from session so it can be used outside the context
        db.expunge(user)
        return user
