"""Authentication request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, description="Password (minimum 8 characters)"
    )
    full_name: str = Field(
        ..., min_length=1, max_length=255, description="User's full name"
    )


class UserLoginRequest(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """User information response."""

    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(..., description="Whether account is active")
    is_verified: bool = Field(..., description="Whether email is verified")
    is_garmin_connected: bool = Field(..., description="Whether Garmin is connected")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = {"from_attributes": True}


class UserWithTokensResponse(BaseModel):
    """User registration/login response with tokens."""

    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
