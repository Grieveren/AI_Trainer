"""
Garmin integration API routes.

Handles OAuth2 PKCE authorization flow with Garmin Connect:
1. POST /authorize - Initiate OAuth flow
2. GET /callback - Handle OAuth callback
3. POST /disconnect - Revoke Garmin access
4. POST /sync - Trigger manual data sync
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from src.database.connection import get_db
from src.models.user import User
from src.api.middleware.auth import get_current_user
from src.services.garmin.oauth_service import GarminOAuthService
from src.config.settings import settings
from src.utils.encryption import encrypt_token

router = APIRouter()


# OAuth service instance
def get_oauth_service() -> GarminOAuthService:
    """Dependency for Garmin OAuth service."""
    return GarminOAuthService(
        client_id=settings.GARMIN_CLIENT_ID,
        client_secret=settings.GARMIN_CLIENT_SECRET,
        redirect_uri=settings.GARMIN_CALLBACK_URL,
    )


@router.post("/authorize", status_code=status.HTTP_200_OK)
async def initiate_authorization(
    current_user: User = Depends(get_current_user),
    oauth_service: GarminOAuthService = Depends(get_oauth_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate Garmin OAuth2 PKCE authorization flow.

    Generates authorization URL and stores state/verifier for callback validation.

    Returns:
        Dict with authorization_url for frontend redirect
    """
    # Generate authorization URL with PKCE
    auth_url, state, code_verifier = oauth_service.get_authorization_url()

    # Store state and verifier in user session for callback validation
    # In production, store in Redis with TTL
    # For now, we'll return them to be stored client-side
    # (This is simplified; in production use server-side session storage)

    return {
        "authorization_url": auth_url,
        "state": state,
        "code_verifier": code_verifier,
    }


@router.get("/callback", status_code=status.HTTP_302_FOUND)
async def handle_oauth_callback(
    oauth_token: str = Query(..., description="OAuth token from Garmin"),
    oauth_verifier: str = Query(..., description="OAuth verifier from Garmin"),
    code_verifier: str = Query(..., description="PKCE code verifier from client"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    expected_state: str = Query(..., description="Expected state from authorization"),
    current_user: User = Depends(get_current_user),
    oauth_service: GarminOAuthService = Depends(get_oauth_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback from Garmin.

    Validates state, exchanges auth code for tokens, and stores encrypted tokens.

    Returns:
        Redirect to frontend success page
    """
    # Validate state to prevent CSRF
    if not oauth_service.validate_state(expected_state, state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter - possible CSRF attack",
        )

    try:
        # Exchange authorization code for tokens
        token_response = await oauth_service.exchange_code_for_token(
            auth_code=oauth_token, code_verifier=code_verifier
        )

        # Extract tokens
        access_token = token_response["access_token"]
        refresh_token = token_response["refresh_token"]
        expires_in = token_response["expires_in"]
        garmin_user_id = token_response.get("user_id")

        # Calculate expiration
        token_expires_at = oauth_service._calculate_expiration(expires_in)

        # Encrypt tokens before storing
        encrypted_access_token = encrypt_token(access_token)
        encrypted_refresh_token = encrypt_token(refresh_token)

        # Update user with Garmin credentials
        current_user.garmin_user_id = garmin_user_id
        current_user.garmin_access_token = encrypted_access_token
        current_user.garmin_refresh_token = encrypted_refresh_token
        current_user.garmin_token_expires_at = token_expires_at

        await db.commit()

        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/settings/garmin/success",
            status_code=status.HTTP_302_FOUND,
        )

    except Exception as e:
        # Log error and redirect to failure page
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code: {str(e)}",
        )


@router.post("/disconnect", status_code=status.HTTP_200_OK)
async def disconnect_garmin(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Disconnect Garmin account by removing stored tokens.

    Returns:
        Success message
    """
    # Clear Garmin credentials
    current_user.garmin_user_id = None
    current_user.garmin_access_token = None
    current_user.garmin_refresh_token = None
    current_user.garmin_token_expires_at = None

    await db.commit()

    return {"message": "Garmin account disconnected successfully"}


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_sync(
    target_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger manual sync of Garmin data.

    Queues background job to fetch latest health metrics and workouts.

    Args:
        target_date: Optional specific date to sync (defaults to today)

    Returns:
        Job ID for tracking sync status
    """
    # Verify user has Garmin connected
    if not current_user.garmin_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Garmin account not connected",
        )

    # Import here to avoid circular dependency
    from src.jobs.garmin_sync import sync_user_garmin_data

    # Queue background job
    sync_date = target_date or date.today()
    job = sync_user_garmin_data.delay(
        user_id=str(current_user.id), sync_date=sync_date.isoformat()
    )

    return {"message": "Sync job queued", "job_id": job.id, "sync_date": sync_date}


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_garmin_status(current_user: User = Depends(get_current_user)):
    """
    Get Garmin connection status for current user.

    Returns:
        Connection status and last sync information
    """
    is_connected = current_user.garmin_access_token is not None

    return {
        "connected": is_connected,
        "garmin_user_id": current_user.garmin_user_id,
        "token_expires_at": current_user.garmin_token_expires_at,
        "last_synced": None,  # TODO: Track last sync timestamp
    }
