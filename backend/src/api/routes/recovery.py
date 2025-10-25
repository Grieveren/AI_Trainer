"""Recovery and recommendations routes."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{date}")
async def get_recovery_score(date: str):
    """Get recovery score for a specific date (placeholder)."""
    return {"message": f"Recovery score for {date} - to be implemented"}


@router.get("/today")
async def get_recovery_today():
    """Get today's recovery score (placeholder)."""
    return {"message": "Today's recovery score - to be implemented"}
