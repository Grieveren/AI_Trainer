"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserWithTokensResponse,
    UserResponse,
)
from src.database.connection import get_async_session
from src.models.user import User
from src.services.jwt_service import JWTService
from src.services.password_service import PasswordService
from sqlalchemy import select

router = APIRouter()
jwt_service = JWTService()
password_service = PasswordService()


@router.post(
    "/register",
    response_model=UserWithTokensResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserRegisterRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        User information with JWT tokens

    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email.lower()))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = password_service.hash_password(user_data.password)
    new_user = User(
        email=user_data.email.lower(),
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate tokens
    access_token = jwt_service.create_access_token(user_id=new_user.id)
    refresh_token = jwt_service.create_refresh_token(user_id=new_user.id)

    return UserWithTokensResponse(
        user=UserResponse.model_validate(new_user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/login", response_model=UserWithTokensResponse)
async def login(
    credentials: UserLoginRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Authenticate user and return tokens.

    Args:
        credentials: User login credentials
        db: Database session

    Returns:
        User information with JWT tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not password_service.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Generate tokens
    access_token = jwt_service.create_access_token(user_id=user.id)
    refresh_token = jwt_service.create_refresh_token(user_id=user.id)

    return UserWithTokensResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
