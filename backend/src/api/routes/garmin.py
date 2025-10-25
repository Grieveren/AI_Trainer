"""Garmin integration routes."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/authorize")
async def authorize():
    """Garmin OAuth authorization (placeholder)."""
    return {"message": "Garmin authorization - to be implemented"}


@router.get("/callback")
async def callback():
    """Garmin OAuth callback (placeholder)."""
    return {"message": "Garmin callback - to be implemented"}
